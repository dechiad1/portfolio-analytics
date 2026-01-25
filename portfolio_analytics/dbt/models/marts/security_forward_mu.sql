-- Mart: Forward-looking expected return per security
-- Derived from analyst price targets (12-month implied return)

with analyst_targets as (
    select * from {{ ref('stg_analyst_targets') }}
),

forward_returns as (
    select
        ticker,
        (target_mean_price / current_price) - 1 as forward_mu,
        analyst_count,
        current_price,
        target_mean_price,
        target_high_price,
        target_low_price,
        fetched_at
    from analyst_targets
    where target_mean_price is not null
      and current_price is not null
      and current_price > 0
)

select * from forward_returns
