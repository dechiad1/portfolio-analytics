-- Staging model: Current positions from Postgres

with source as (
    select * from {{ source('postgres', 'pg_position_current') }}
),

staged as (
    select
        portfolio_id,
        security_id,
        quantity,
        avg_cost,
        updated_at,
        -- Derived: cost basis
        quantity * avg_cost as cost_basis
    from source
    where quantity != 0  -- Only include non-zero positions
)

select * from staged
