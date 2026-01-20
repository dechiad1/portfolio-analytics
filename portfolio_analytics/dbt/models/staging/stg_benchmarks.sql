-- Staging model: Benchmark and risk-free rate data
-- Risk-free rates now derived from Treasury yields (10Y) via stg_risk_free_rates

with benchmark as (
    select * from {{ source('raw', 'raw_benchmark_prices') }}
),

risk_free as (
    select * from {{ ref('stg_risk_free_rates') }}
),

joined as (
    select
        b.date,
        b.benchmark_ticker,
        b.benchmark_price,
        r.risk_free_rate,
        r.risk_free_rate_daily
    from benchmark b
    left join risk_free r on b.date = r.date
)

select * from joined
