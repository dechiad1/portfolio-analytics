-- Intermediate model: Calculate daily returns for each holding

{{ config(**intermediate_config('int_daily_returns')) }}

with prices as (
    select * from {{ ref('stg_prices') }}
),

with_lag as (
    select
        ticker,
        date,
        price,
        lag(price) over (partition by ticker order by date) as prev_price,
        lag(date) over (partition by ticker order by date) as prev_date
    from prices
),

returns as (
    select
        ticker,
        date,
        price,
        prev_price,
        -- Calculate daily return
        case 
            when prev_price is not null and prev_price > 0
            then (price / prev_price) - 1
            else null
        end as daily_return,
        -- Calculate log return (for volatility calculations)
        case
            when prev_price is not null and prev_price > 0
            then ln(price / prev_price)
            else null
        end as log_return
    from with_lag
)

select * from returns
where daily_return is not null
