-- Staging model: Portfolio holdings from S3
-- Note: holdings.parquet must be uploaded to S3 (converted from seeds/holdings.csv)

with source as (
    select * from {{ source('seeds', 'holdings') }}
),

cleaned as (
    select
        ticker,
        name,
        asset_class,
        sector,
        broker,
        cast(purchase_date as date) as purchase_date
    from source
)

select * from cleaned
