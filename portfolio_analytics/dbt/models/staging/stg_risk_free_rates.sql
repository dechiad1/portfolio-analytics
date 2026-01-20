-- Staging model: Risk-free rates derived from Treasury yields
-- Uses 10Y Treasury as the risk-free rate proxy (standard practice)

with treasury_yields as (
    select * from {{ source('raw', 'raw_treasury_yields') }}
    where tenor = '10Y'
),

final as (
    select
        cast(date as date) as date,
        yield_rate as risk_free_rate,  -- Annual rate as decimal
        yield_rate / 252 as risk_free_rate_daily  -- Daily rate (252 trading days)
    from treasury_yields
)

select * from final
