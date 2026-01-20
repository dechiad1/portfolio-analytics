-- Staging model: Cash balances from Postgres

with source as (
    select * from {{ source('postgres', 'pg_cash_balance') }}
),

staged as (
    select
        portfolio_id,
        currency,
        balance,
        updated_at
    from source
)

select * from staged
