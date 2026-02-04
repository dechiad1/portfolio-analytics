-- Marts model: Comprehensive fund dimension with metadata and performance
-- Uses dim_ticker_tracker as the canonical source of tickers

{{ config(**mart_config('dim_funds')) }}

with ticker_tracker as (
    -- Canonical source of all tickers to track
    select * from {{ ref('dim_ticker_tracker') }}
),

fund_metadata as (
    select * from {{ ref('stg_fund_metadata') }}
),

performance as (
    select * from {{ ref('fct_performance') }}
),

holdings as (
    -- Legacy seed data for backward compatibility
    select * from {{ ref('stg_holdings') }}
),

combined as (
    select
        -- Ticker from canonical tracker
        tt.ticker,

        -- Fund name: prefer Yahoo metadata, fall back to tracker display_name
        coalesce(fm.fund_name, tt.display_name) as fund_name,

        -- Fund metadata (from Yahoo Finance)
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

        -- Asset class: prefer tracker (more accurate), fall back to holdings seed
        coalesce(tt.asset_class, h.asset_class) as asset_class,
        coalesce(tt.sector, h.sector) as sector,
        h.broker,
        h.purchase_date,

        -- Ticker source info
        tt.is_in_seed,
        tt.is_in_portfolio,
        tt.source_type,

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

        -- 1-Year metrics
        p.total_return_1y_pct,
        p.return_vs_risk_free_1y_pct,
        p.return_vs_sp500_1y_pct,
        p.volatility_1y_pct,
        p.sharpe_ratio_1y,

        -- 5-Year metrics
        p.total_return_5y_pct,
        p.return_vs_risk_free_5y_pct,
        p.return_vs_sp500_5y_pct,
        p.volatility_5y_pct,
        p.sharpe_ratio_5y,

        -- Data quality flags
        case when fm.ticker is not null then 1 else 0 end as has_fund_metadata,
        case when fm.expense_ratio_pct is not null then 1 else 0 end as has_expense_ratio,
        case when fm.mandate is not null then 1 else 0 end as has_mandate,
        case when fm.asset_distribution is not null then 1 else 0 end as has_asset_distribution,
        case when p.ticker is not null then 1 else 0 end as has_performance_data

    from ticker_tracker tt
    left join fund_metadata fm on tt.ticker = fm.ticker
    left join holdings h on tt.ticker = h.ticker
    left join performance p on tt.ticker = p.ticker
)

select * from combined
