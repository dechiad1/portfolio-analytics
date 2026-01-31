-- Dimension: Enriched security data for LLM scenario-based selection
-- Combines static registry data with dynamic characteristics and analyst data
-- This view provides all context an LLM needs to select securities for scenarios

with dim_security as (
    select * from {{ ref('dim_security') }}
),

characteristics as (
    select * from {{ ref('stg_security_characteristics') }}
),

analyst_targets as (
    select * from {{ ref('stg_analyst_targets') }}
),

volatility as (
    select * from {{ ref('security_volatility') }}
),

historical_returns as (
    select * from {{ ref('security_historical_mu') }}
),

-- Join all data sources
enriched as (
    select
        -- =================================================================
        -- CORE IDENTITY
        -- =================================================================
        ds.security_id,
        ds.asset_type,
        coalesce(ds.ticker, ds.primary_id_value) as ticker,
        coalesce(c.security_name, ds.display_name) as display_name,
        ds.currency,
        ds.primary_id_type,
        ds.primary_id_value,

        -- =================================================================
        -- CLASSIFICATION
        -- =================================================================
        coalesce(c.sector, ds.sector) as sector,
        coalesce(c.industry, ds.industry) as industry,
        coalesce(c.country, ds.country) as country,
        coalesce(c.exchange, ds.exchange) as exchange,
        c.quote_type,
        c.market_cap_category,

        -- =================================================================
        -- MARKET DYNAMICS
        -- =================================================================
        c.market_cap,
        c.enterprise_value,
        c.beta,
        v.annualized_volatility,
        v.volatility_percentile,
        c.fifty_two_week_high,
        c.fifty_two_week_low,
        c.fifty_day_average,
        c.two_hundred_day_average,
        c.avg_volume_10d,
        c.avg_volume_3m,

        -- =================================================================
        -- VALUATION METRICS
        -- =================================================================
        c.trailing_pe,
        c.forward_pe,
        c.peg_ratio,
        c.price_to_book,
        c.price_to_sales,
        c.enterprise_to_revenue,
        c.enterprise_to_ebitda,

        -- =================================================================
        -- PROFITABILITY
        -- =================================================================
        c.profit_margin,
        c.operating_margin,
        c.gross_margin,
        c.return_on_equity,
        c.return_on_assets,

        -- =================================================================
        -- INCOME / DIVIDENDS
        -- =================================================================
        c.dividend_yield,
        c.dividend_rate,
        c.payout_ratio,
        c.five_year_avg_dividend_yield,

        -- =================================================================
        -- GROWTH
        -- =================================================================
        c.revenue_growth,
        c.earnings_growth,
        c.earnings_quarterly_growth,

        -- =================================================================
        -- FINANCIAL HEALTH
        -- =================================================================
        c.total_debt,
        c.total_cash,
        c.debt_to_equity,
        c.current_ratio,
        c.quick_ratio,
        c.free_cash_flow,

        -- =================================================================
        -- ANALYST SENTIMENT
        -- =================================================================
        at.current_price,
        at.target_mean_price,
        at.target_high_price,
        at.target_low_price,
        at.analyst_count,
        at.implied_return as analyst_implied_return,

        -- =================================================================
        -- HISTORICAL PERFORMANCE
        -- =================================================================
        hr.historical_mu as historical_annual_return,
        hr.lookback_years,

        -- =================================================================
        -- SCENARIO-RELEVANT FLAGS
        -- =================================================================
        coalesce(c.is_dividend_payer, false) as is_dividend_payer,
        coalesce(c.is_high_growth, false) as is_high_growth,
        coalesce(c.is_value, false) as is_value,
        coalesce(c.is_defensive, false) as is_defensive,
        coalesce(c.is_cyclical, false) as is_cyclical,
        coalesce(c.is_rate_sensitive, false) as is_rate_sensitive,
        coalesce(c.is_inflation_hedge, false) as is_inflation_hedge,

        -- =================================================================
        -- ETF-SPECIFIC
        -- =================================================================
        c.expense_ratio,
        c.total_assets as etf_aum,
        c.category as etf_category,
        c.fund_family,

        -- =================================================================
        -- BOND-SPECIFIC (from dim_security)
        -- =================================================================
        ds.issuer_name,
        ds.coupon_type,
        ds.coupon_rate,
        ds.maturity_date,
        ds.years_to_maturity,
        ds.duration_bucket,
        ds.bond_sector,

        -- =================================================================
        -- METADATA
        -- =================================================================
        c.fetched_at as characteristics_fetched_at,
        at.fetched_at as analyst_data_fetched_at,
        ds.created_at,
        ds.updated_at

    from dim_security ds
    left join characteristics c
        on ds.ticker = c.ticker
    left join analyst_targets at
        on ds.ticker = at.ticker
    left join volatility v
        on ds.ticker = v.ticker
    left join historical_returns hr
        on ds.ticker = hr.ticker
)

select * from enriched
