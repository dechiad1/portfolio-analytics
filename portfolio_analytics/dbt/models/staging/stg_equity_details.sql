-- Staging model: Equity/ETF details from Postgres

with source as (
    select * from {{ source('postgres', 'pg_equity_details') }}
),

staged as (
    select
        security_id,
        ticker,
        exchange,
        country,
        sector,
        industry,
        created_at,
        updated_at
    from source
)

select * from staged
