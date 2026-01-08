-- Staging model: Clean and standardize raw price data

with source as (
    select * from {{ source('raw', 'raw_prices') }}
),

cleaned as (
    select
        date,
        ticker,
        close as price,
        volume,
        open as open_price,
        high as high_price,
        low as low_price
    from source
    where close is not null
      and close > 0  -- Filter out invalid prices
)

select * from cleaned
