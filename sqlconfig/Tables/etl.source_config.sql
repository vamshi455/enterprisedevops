CREATE TABLE [etl].[source_config] (
    [source_code]     VARCHAR(50)   NOT NULL CONSTRAINT [PK_source_config] PRIMARY KEY,
    [source_system]   VARCHAR(50)   NOT NULL,
    [landing_path]    VARCHAR(400)  NOT NULL,
    [file_pattern]    VARCHAR(200)  NULL,
    [target_table]    VARCHAR(200)  NOT NULL,   -- e.g. {catalog}.bronze.sales_raw
    [load_type]       VARCHAR(20)   NOT NULL CONSTRAINT [CK_source_config_load_type] CHECK ([load_type] IN ('full','incremental')),
    [watermark_column] VARCHAR(100) NULL,
    [copy_parallelism] INT          NOT NULL CONSTRAINT [DF_source_config_par] DEFAULT 4,
    [is_active]       BIT           NOT NULL CONSTRAINT [DF_source_config_active] DEFAULT 1,
    [modified_by_pr]  INT           NULL       -- PR that last changed this row (traceability)
);
