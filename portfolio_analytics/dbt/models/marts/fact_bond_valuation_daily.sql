-- Fact: Daily bond valuation with accrued interest
-- Computes accrued interest and dirty price for each bond on each day
-- This enables proper market value calculation for bond positions

{{
    config(
        materialized='table'
    )
}}

with dim_security as (
    select * from {{ ref('dim_security') }}
    where asset_type = 'BOND'
),

fact_price as (
    select * from {{ ref('fact_price_daily') }}
),

-- Generate date spine for bonds (from issue to maturity or today)
date_spine as (
    select
        ds.security_id,
        generate_series(
            greatest(ds.issue_date, date '2020-01-01'),
            least(ds.maturity_date, current_date),
            interval '1 day'
        )::date as as_of_date
    from dim_security ds
),

-- Calculate accrued interest for each bond-day combination
bond_valuations as (
    select
        spine.as_of_date,
        spine.security_id,
        ds.coupon_type,
        ds.coupon_rate,
        ds.payment_frequency,
        ds.payments_per_year,
        ds.day_count_convention,
        ds.issue_date,
        ds.maturity_date,
        ds.par_value,

        -- Get clean price (default to par if no price available)
        coalesce(fp.price, 100.0) as clean_price,

        -- Calculate days in current coupon period and days since last coupon
        -- Simplified calculation assuming regular periods
        case ds.payment_frequency
            when 'ANNUAL' then 365
            when 'SEMIANNUAL' then 182
            when 'QUARTERLY' then 91
            when 'MONTHLY' then 30
            else 182
        end as days_in_period,

        -- Days since last coupon payment (simplified)
        -- In production, would calculate based on actual coupon schedule
        case ds.payment_frequency
            when 'ANNUAL' then
                (spine.as_of_date - ds.issue_date) % 365
            when 'SEMIANNUAL' then
                (spine.as_of_date - ds.issue_date) % 182
            when 'QUARTERLY' then
                (spine.as_of_date - ds.issue_date) % 91
            when 'MONTHLY' then
                (spine.as_of_date - ds.issue_date) % 30
            else (spine.as_of_date - ds.issue_date) % 182
        end as days_since_last_coupon

    from date_spine spine
    inner join dim_security ds on spine.security_id = ds.security_id
    left join fact_price fp
        on spine.security_id = fp.security_id
        and spine.as_of_date = fp.as_of_date
),

-- Final calculations
final as (
    select
        as_of_date,
        security_id,
        clean_price,

        -- Accrued interest per 100 par
        -- Formula: (coupon_rate / payments_per_year) * (days_since_last_coupon / days_in_period) * par_value
        case
            when coupon_type = 'ZERO' then 0
            else
                (coalesce(coupon_rate, 0) / payments_per_year) *
                (cast(days_since_last_coupon as decimal) / days_in_period) *
                par_value
        end as accrued_interest_per_100,

        -- Dirty price = clean price + accrued interest (per 100 par)
        clean_price +
        case
            when coupon_type = 'ZERO' then 0
            else
                (coalesce(coupon_rate, 0) / payments_per_year) *
                (cast(days_since_last_coupon as decimal) / days_in_period) *
                par_value
        end as dirty_price_per_100,

        -- Coupon payment per period (per 100 par)
        case
            when coupon_type = 'ZERO' then 0
            else (coalesce(coupon_rate, 0) / payments_per_year) * par_value
        end as coupon_payment_per_100,

        -- Days until next coupon
        days_in_period - days_since_last_coupon as days_to_next_coupon,

        -- Metadata
        day_count_convention,
        payment_frequency

    from bond_valuations
)

select * from final
