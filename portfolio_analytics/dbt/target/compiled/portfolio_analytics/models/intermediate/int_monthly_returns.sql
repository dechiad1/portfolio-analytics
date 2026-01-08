-- Intermediate model: Calculate monthly returns

with daily_prices as (
    select * from "portfolio"."main_staging"."stg_prices"
),

monthly_prices as (
    select
        ticker,
        date_trunc('month', date) as month,
        -- Get last price of each month
        max(date) as last_trading_day,
        last(price order by date) as month_end_price
    from daily_prices
    group by ticker, date_trunc('month', date)
),

with_lag as (
    select
        ticker,
        month,
        month_end_price,
        lag(month_end_price) over (partition by ticker order by month) as prev_month_price
    from monthly_prices
),

returns as (
    select
        ticker,
        month,
        month_end_price as price,
        prev_month_price,
        case
            when prev_month_price is not null and prev_month_price > 0
            then (month_end_price / prev_month_price) - 1
            else null
        end as monthly_return
    from with_lag
)

select * from returns
where monthly_return is not null