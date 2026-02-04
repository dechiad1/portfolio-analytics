-- Dimension: Unified security dimension with denormalized attributes
-- Includes equity, ETF, and bond details for all active securities

{{ config(**mart_config('dim_security')) }}

with security_registry as (
    select * from {{ ref('stg_security_registry') }}
),

equity_details as (
    select * from {{ ref('stg_equity_details') }}
),

bond_details as (
    select * from {{ ref('stg_bond_details') }}
),

-- Get primary identifier (ticker for equities, CUSIP for bonds)
primary_identifiers as (
    select
        security_id,
        id_type,
        id_value
    from {{ ref('stg_security_identifier') }}
    where is_primary = true
),

-- Combine all security types
unified_securities as (
    select
        sr.security_id,
        sr.asset_type,
        sr.currency,
        sr.display_name,

        -- Primary identifier
        pi.id_type as primary_id_type,
        pi.id_value as primary_id_value,

        -- Equity/ETF attributes (null for bonds)
        ed.ticker,
        ed.exchange,
        ed.country,
        ed.sector,
        ed.industry,

        -- Bond attributes (null for equities/ETFs)
        bd.issuer_name,
        bd.coupon_type,
        bd.coupon_rate,
        bd.payment_frequency,
        bd.day_count_convention,
        bd.issue_date,
        bd.maturity_date,
        bd.par_value,
        bd.price_quote_convention,
        bd.payments_per_year,
        bd.coupon_per_period,

        -- Derived bond attributes for learning visuals
        case
            when sr.asset_type = 'BOND' then
                case
                    when bd.issuer_name like '%Treasury%' then 'Government'
                    when bd.issuer_name like '%Municipal%' then 'Municipal'
                    else 'Corporate'
                end
            else null
        end as bond_sector,

        case
            when sr.asset_type = 'BOND' then
                -- Years to maturity as of today
                (bd.maturity_date - current_date) / 365.25
            else null
        end as years_to_maturity,

        case
            when sr.asset_type = 'BOND' then
                case
                    when (bd.maturity_date - current_date) / 365.25 <= 2 then 'Short (0-2Y)'
                    when (bd.maturity_date - current_date) / 365.25 <= 7 then 'Intermediate (2-7Y)'
                    when (bd.maturity_date - current_date) / 365.25 <= 15 then 'Long (7-15Y)'
                    else 'Ultra-Long (15Y+)'
                end
            else null
        end as duration_bucket,

        sr.created_at,
        sr.updated_at

    from security_registry sr
    left join equity_details ed on sr.security_id = ed.security_id
    left join bond_details bd on sr.security_id = bd.security_id
    left join primary_identifiers pi on sr.security_id = pi.security_id
)

select * from unified_securities
