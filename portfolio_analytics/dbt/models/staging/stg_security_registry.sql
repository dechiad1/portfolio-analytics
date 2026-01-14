-- Staging model: Security registry from Postgres

with source as (
    select * from {{ source('postgres', 'pg_security_registry') }}
),

staged as (
    select
        security_id,
        asset_type,
        currency,
        display_name,
        is_active,
        created_at,
        updated_at
    from source
    where is_active = true
)

select * from staged
