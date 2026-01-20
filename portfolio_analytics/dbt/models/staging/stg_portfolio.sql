-- Staging model: Portfolio data from Postgres

with source as (
    select * from {{ source('postgres', 'pg_portfolio') }}
),

staged as (
    select
        portfolio_id,
        user_id,
        name as portfolio_name,
        base_currency,
        created_at,
        updated_at
    from source
)

select * from staged
