-- Staging model: Bond details from Postgres

with source as (
    select * from {{ source('postgres', 'pg_bond_details') }}
),

staged as (
    select
        security_id,
        issuer_name,
        coupon_type,
        coupon_rate,
        payment_frequency,
        day_count_convention,
        issue_date,
        maturity_date,
        par_value,
        price_quote_convention,
        created_at,
        updated_at,
        -- Derived fields for calculations
        case payment_frequency
            when 'ANNUAL' then 1
            when 'SEMIANNUAL' then 2
            when 'QUARTERLY' then 4
            when 'MONTHLY' then 12
            else 2  -- default to semiannual
        end as payments_per_year,
        case
            when coupon_type = 'FIXED' and coupon_rate is not null
            then coupon_rate / case payment_frequency
                when 'ANNUAL' then 1
                when 'SEMIANNUAL' then 2
                when 'QUARTERLY' then 4
                when 'MONTHLY' then 12
                else 2
            end
            else 0
        end as coupon_per_period
    from source
)

select * from staged
