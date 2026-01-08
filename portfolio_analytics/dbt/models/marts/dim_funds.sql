-- Marts model: Comprehensive fund dimension with metadata and performance

{{
  config(
    materialized='table'
  )
}}

with fund_metadata as (
    select * from {{ ref('stg_fund_metadata') }}
),

performance as (
    select * from {{ ref('fct_performance') }}
),

holdings as (
    select * from {{ ref('stg_holdings') }}
),

combined as (
    select
        -- Fund identifiers
        fm.ticker,
        fm.fund_name,

        -- Fund metadata
        fm.expense_ratio_pct,
        fm.fund_family,
        fm.category,
        fm.fund_inception_date,
        fm.total_assets,
        fm.currency,
        fm.exchange,
        fm.quote_type,
        fm.mandate,
        fm.asset_distribution,
        fm.top_sectors,

        -- Legacy holdings data (from old seed)
        h.name as holdings_name,
        h.asset_class,
        h.sector,
        h.broker,
        h.purchase_date,

        -- Performance metrics
        p.first_date as performance_start_date,
        p.last_date as performance_end_date,
        p.starting_price,
        p.ending_price,
        p.min_price,
        p.max_price,
        p.total_return_pct,
        p.annualized_return_pct,
        p.volatility_pct,
        p.sharpe_ratio,
        p.benchmark_total_return,
        p.vs_benchmark_pct,
        p.trading_days,
        p.months_tracked,
        p.avg_risk_free_rate,

        -- Data quality flags
        case when fm.expense_ratio_pct is not null then 1 else 0 end as has_expense_ratio,
        case when fm.mandate is not null then 1 else 0 end as has_mandate,
        case when fm.asset_distribution is not null then 1 else 0 end as has_asset_distribution,
        case when p.ticker is not null then 1 else 0 end as has_performance_data

    from fund_metadata fm
    left join holdings h on fm.ticker = h.ticker
    left join performance p on fm.ticker = p.ticker
)

select * from combined
