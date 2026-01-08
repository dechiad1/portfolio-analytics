-- Staging model: Benchmark and risk-free rate data

with benchmark as (
    select * from {{ source('raw', 'raw_benchmark_prices') }}
),

risk_free as (
    select * from {{ source('raw', 'raw_risk_free_rates') }}
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
