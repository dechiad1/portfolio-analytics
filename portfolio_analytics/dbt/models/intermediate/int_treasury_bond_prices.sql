-- Intermediate: Derive Treasury bond clean prices from yield curve
-- Uses present value formula: Price = PV(coupons) + PV(principal)
-- Only applies to Treasury bonds (issuer_name like '%Treasury%')

{{
    config(
        materialized='table'
    )
}}

with treasury_yields as (
    select
        cast(date as date) as as_of_date,
        tenor,
        yield_rate
    from {{ source('raw', 'raw_treasury_yields') }}
),

-- Pivot yields to get all tenors in one row per date
yield_curve as (
    select
        as_of_date,
        max(case when tenor = '2Y' then yield_rate end) as yield_2y,
        max(case when tenor = '5Y' then yield_rate end) as yield_5y,
        max(case when tenor = '10Y' then yield_rate end) as yield_10y,
        max(case when tenor = '30Y' then yield_rate end) as yield_30y
    from treasury_yields
    group by as_of_date
),

-- Get Treasury bonds from dim_security
treasury_bonds as (
    select
        security_id,
        coupon_type,
        coupon_rate,
        payments_per_year,
        issue_date,
        maturity_date,
        par_value
    from {{ ref('dim_security') }}
    where asset_type = 'BOND'
      and issuer_name like '%Treasury%'
),

-- Cross join bonds with yield dates to get all bond-date combinations
bond_dates as (
    select
        tb.security_id,
        tb.coupon_type,
        tb.coupon_rate,
        tb.payments_per_year,
        tb.issue_date,
        tb.maturity_date,
        tb.par_value,
        yc.as_of_date,
        yc.yield_2y,
        yc.yield_5y,
        yc.yield_10y,
        yc.yield_30y,
        -- Years to maturity as of this date
        (tb.maturity_date - yc.as_of_date) / 365.25 as years_to_maturity
    from treasury_bonds tb
    cross join yield_curve yc
    where yc.as_of_date >= tb.issue_date
      and yc.as_of_date < tb.maturity_date
),

-- Interpolate yield based on years to maturity
bond_yields as (
    select
        *,
        -- Linear interpolation between yield curve points
        case
            when years_to_maturity <= 2 then yield_2y
            when years_to_maturity <= 5 then
                yield_2y + (yield_5y - yield_2y) * (years_to_maturity - 2) / 3
            when years_to_maturity <= 10 then
                yield_5y + (yield_10y - yield_5y) * (years_to_maturity - 5) / 5
            when years_to_maturity <= 30 then
                yield_10y + (yield_30y - yield_10y) * (years_to_maturity - 10) / 20
            else yield_30y
        end as interpolated_yield
    from bond_dates
),

-- Calculate clean price using simplified present value formula
-- For simplicity, using single discount rate (not per-period)
-- Price = (C/y) * (1 - 1/(1+y)^n) + F/(1+y)^n
-- Where C = annual coupon, y = yield, n = years, F = face value
bond_prices as (
    select
        as_of_date,
        security_id,
        coupon_type,
        coupon_rate,
        interpolated_yield as yield_rate,
        years_to_maturity,
        par_value,

        case
            -- Zero coupon bonds: Price = F / (1+y)^n
            when coupon_type = 'ZERO' then
                par_value / power(1 + interpolated_yield, years_to_maturity)

            -- Coupon bonds: PV of coupons + PV of principal
            -- Using continuous approximation for simplicity
            when interpolated_yield > 0 then
                -- PV of coupon stream
                (coupon_rate * par_value / interpolated_yield) *
                (1 - 1 / power(1 + interpolated_yield, years_to_maturity))
                -- Plus PV of principal
                + par_value / power(1 + interpolated_yield, years_to_maturity)

            -- Edge case: zero yield (price = sum of coupons + par)
            else
                (coupon_rate * par_value * years_to_maturity) + par_value
        end as clean_price

    from bond_yields
    where interpolated_yield is not null
)

select
    as_of_date,
    security_id,
    round(clean_price, 4) as clean_price,
    round(yield_rate * 100, 4) as yield_pct,
    round(years_to_maturity, 2) as years_to_maturity,
    'derived_from_yields' as price_source
from bond_prices
