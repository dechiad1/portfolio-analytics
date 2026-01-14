-- Staging model: Security identifiers from Postgres

with source as (
    select * from {{ source('postgres', 'pg_security_identifier') }}
),

staged as (
    select
        id as identifier_id,
        security_id,
        id_type,
        id_value,
        source as identifier_source,
        is_primary,
        created_at
    from source
)

select * from staged
