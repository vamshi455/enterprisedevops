-- RUNTIME STATE: written by ADF at run time. Schema is deployed, rows are NEVER deployed or overwritten.
CREATE TABLE [etl].[watermark] (
    [source_code]   VARCHAR(50)  NOT NULL CONSTRAINT [PK_watermark] PRIMARY KEY,
    [last_value]    NVARCHAR(100) NULL,
    [last_run_id]   UNIQUEIDENTIFIER NULL,
    [updated_at]    DATETIME2(0) NOT NULL CONSTRAINT [DF_watermark_upd] DEFAULT SYSUTCDATETIME()
);
