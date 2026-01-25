-- Mart: Historical annualized mean return per security
-- Calculated from daily returns using 252 trading days per year

with daily_returns as (
    select * from {{ ref('int_daily_returns') }}
),

aggregated as (
    select
        ticker,
        avg(daily_return) * 252 as annualized_mu,
        count(*) as observation_count,
        min(date) as data_start,
        max(date) as data_end
    from daily_returns
    where daily_return is not null
    group by ticker
)

select * from aggregated
