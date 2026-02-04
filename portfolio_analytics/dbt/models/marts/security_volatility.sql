-- Mart: Annualized volatility (standard deviation) per security
-- Calculated from daily returns using sqrt(252) annualization factor

{{ config(**mart_config('security_volatility')) }}

with daily_returns as (
    select * from {{ ref('int_daily_returns') }}
),

aggregated as (
    select
        ticker,
        stddev(daily_return) * sqrt(252) as annualized_volatility,
        count(*) as observation_count,
        min(date) as data_start,
        max(date) as data_end
    from daily_returns
    where daily_return is not null
    group by ticker
)

select * from aggregated
