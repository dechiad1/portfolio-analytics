-- Staging: Clean analyst price targets from raw data

with raw as (
    select * from {{ source('raw', 'raw_analyst_targets') }}
),

cleaned as (
    select
        ticker,
        current_price,
        target_mean_price,
        target_high_price,
        target_low_price,
        coalesce(analyst_count, 0) as analyst_count,
        implied_return,
        fetched_at
    from raw
    where ticker is not null
      and current_price is not null
      and current_price > 0
)

select * from cleaned
