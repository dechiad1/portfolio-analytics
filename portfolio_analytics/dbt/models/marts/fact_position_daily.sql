-- Fact: Daily position snapshots per portfolio per security
-- Built from current positions (v1: no historical backfill)
-- Future enhancement: replay transaction_ledger for historical positions

{{
    config(
        materialized='table'
    )
}}

with position_current as (
    select * from {{ ref('stg_position_current') }}
),

dim_security as (
    select * from {{ ref('dim_security') }}
),

-- For v1, we use current positions as the snapshot
-- In production, this would be built incrementally from transaction ledger
current_positions as (
    select
        current_date as as_of_date,
        pc.portfolio_id,
        pc.security_id,
        pc.quantity,
        pc.avg_cost as cost_basis_per_unit,
        pc.quantity * pc.avg_cost as total_cost_basis,
        pc.updated_at
    from position_current pc
    inner join dim_security ds on pc.security_id = ds.security_id
    where pc.quantity != 0
)

select
    as_of_date,
    portfolio_id,
    security_id,
    quantity,
    cost_basis_per_unit,
    total_cost_basis
from current_positions
