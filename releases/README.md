`releases/<release-id>/manifest.json` is written by `scripts/release/build_release.py` and committed
**on the release branch only** (never on main). It is the contract between QA, UAT, the ServiceNow CR
and Prod: PR ids, squash commits, cherry-picked commits, work items, baseline, dependency warnings.
