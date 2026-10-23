#!/usr/bin/env python3
"""
ServiceNow Change Request gate for the Production stage.

  check   - Fails unless the CR is approved, in Scheduled/Implement state, inside its
            planned window, and lists EXACTLY the PRs in the release manifest.
  start   - Moves the CR to Implement and adds a work note (called right before deploy).
  close   - Adds deployment evidence and moves the CR to Review (success) or records failure.

CR convention: the CR description (or custom field u_release_prs) contains a line
    Release-PRs: 1234, 1240, 1251
    Release-Id:  R2026.10.23
This is what ties "the PRs" to "the CR" -- the rule from the Marathon process.

Env: SNOW_INSTANCE (https://shell.service-now.com), SNOW_USER, SNOW_PASSWORD
     (or SNOW_TOKEN for OAuth bearer).
Note: Azure DevOps also offers the "ServiceNow Change Management" extension, which
provides a native environment check; this script is the portable equivalent and adds
the PR-list match the extension does not do.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.request

# ServiceNow change_request.state values (out-of-box)
STATES = {"-5": "New", "-4": "Assess", "-3": "Authorize", "-2": "Scheduled",
          "-1": "Implement", "0": "Review", "3": "Closed", "4": "Canceled"}
DEPLOYABLE = {"-2", "-1"}
PR_LINE = re.compile(r"Release-PRs:\s*([\d,\s]+)", re.IGNORECASE)


class Snow:
    def __init__(self):
        self.base = os.environ["SNOW_INSTANCE"].rstrip("/")
        if os.environ.get("SNOW_TOKEN"):
            self.auth = "Bearer " + os.environ["SNOW_TOKEN"]
        else:
            cred = f"{os.environ['SNOW_USER']}:{os.environ['SNOW_PASSWORD']}"
            self.auth = "Basic " + base64.b64encode(cred.encode()).decode()

    def _req(self, method: str, path: str, body: dict | None = None) -> dict:
        req = urllib.request.Request(
            self.base + path, method=method,
            data=json.dumps(body).encode() if body else None,
            headers={"Authorization": self.auth, "Accept": "application/json",
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)

    def get_cr(self, number: str, release_id: str | None = None) -> dict:
        # "--cr auto": find the open CR whose description carries "Release-Id: <id>"
        query = (f"number={number}" if number != "auto" else
                 f"descriptionLIKERelease-Id: {release_id}^stateNOT IN3,4^ORDERBYDESCsys_created_on")
        q = urllib.parse.urlencode({
            "sysparm_query": query,
            "sysparm_fields": "sys_id,number,state,approval,start_date,end_date,description,u_release_prs,short_description",
            "sysparm_display_value": "false", "sysparm_limit": "1"})
        res = self._req("GET", f"/api/now/table/change_request?{q}")["result"]
        if not res:
            raise SystemExit(f"CR {number} not found")
        return res[0]

    def patch(self, sys_id: str, fields: dict) -> None:
        self._req("PATCH", f"/api/now/table/change_request/{sys_id}", fields)


def evaluate(cr: dict, manifest: dict, now: dt.datetime | None = None) -> list[str]:
    """Pure function (unit-testable): returns list of failures; empty = gate passes."""
    now = now or dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    fails = []
    if cr.get("approval") != "approved":
        fails.append(f"approval is '{cr.get('approval')}', must be 'approved'")
    if str(cr.get("state")) not in DEPLOYABLE:
        fails.append(f"state is '{STATES.get(str(cr.get('state')), cr.get('state'))}', must be Scheduled or Implement")
    fmt = "%Y-%m-%d %H:%M:%S"
    try:
        start, end = dt.datetime.strptime(cr["start_date"], fmt), dt.datetime.strptime(cr["end_date"], fmt)
        if not (start <= now <= end):
            fails.append(f"outside change window {cr['start_date']} -> {cr['end_date']} (UTC)")
    except (KeyError, ValueError):
        fails.append("planned start/end dates missing")
    text = (cr.get("u_release_prs") or "") + "\n" + (cr.get("description") or "")
    m = PR_LINE.search(text) if not cr.get("u_release_prs") else re.match(r"([\d,\s]+)", cr["u_release_prs"])
    cr_prs = sorted(int(x) for x in re.findall(r"\d+", m.group(1))) if m else []
    rel_prs = sorted(manifest["pr_ids"])
    if cr_prs != rel_prs:
        fails.append(f"CR PR list {cr_prs} != release manifest {rel_prs}")
    return fails


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["check", "start", "close"])
    ap.add_argument("--cr", required=True, help="CHG number, or 'auto' to look up by Release-Id")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--result", choices=["success", "failed"], default="success")
    ap.add_argument("--evidence-url", default=os.environ.get("BUILD_URL", ""))
    a = ap.parse_args()
    manifest = json.load(open(a.manifest))
    snow = Snow()
    cr = snow.get_cr(a.cr, manifest["release_id"])
    a.cr = cr["number"]
    print(f"##vso[task.setvariable variable=changeRequest;isOutput=true]{a.cr}")

    if a.command == "check":
        fails = evaluate(cr, manifest)
        for f in fails:
            print(f"##vso[task.logissue type=error]CR {a.cr}: {f}")
        print("CR gate PASSED" if not fails else "CR gate FAILED")
        return 1 if fails else 0
    if a.command == "start":
        snow.patch(cr["sys_id"], {"state": "-1", "work_notes":
                   f"Deployment started for release {manifest['release_id']} (PRs {manifest['pr_ids']}). {a.evidence_url}"})
        return 0
    note = (f"Release {manifest['release_id']} deployed to PROD: {a.result.upper()}.\n"
            f"PRs: {manifest['pr_ids']}\nWork items: {manifest['work_items']}\n"
            f"Branch: {manifest['branch']}\nPipeline: {a.evidence_url}")
    fields = {"work_notes": note}
    if a.result == "success":
        fields.update({"state": "0", "close_code": "successful", "close_notes": note})
    snow.patch(cr["sys_id"], fields)
    return 0


if __name__ == "__main__":
    sys.exit(main())
