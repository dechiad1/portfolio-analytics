-- Staging: Clean security characteristics for scenario-based LLM selection
-- Source: raw_security_characteristics (from ingest_security_characteristics.py)

with raw as (
    select * from {{ source('raw', 'raw_security_characteristics') }}
),

cleaned as (
    select
        -- Identification
        ticker,
        security_name,
        quote_type,
        sector,
        industry,
        country,
        exchange,
        currency,

        -- Market dynamics
        market_cap,
        enterprise_value,
        beta,
        fifty_two_week_high,
        fifty_two_week_low,
        fifty_day_average,
        two_hundred_day_average,
        avg_volume_10d,
        avg_volume_3m,

        -- Valuation
        trailing_pe,
        forward_pe,
        peg_ratio,
        price_to_book,
        price_to_sales,
        enterprise_to_revenue,
        enterprise_to_ebitda,

        -- Profitability
        profit_margin,
        operating_margin,
        gross_margin,
        ebitda_margin,
        return_on_equity,
        return_on_assets,

        -- Income
        dividend_yield,
        dividend_rate,
        trailing_annual_dividend_yield,
        payout_ratio,
        five_year_avg_dividend_yield,

        -- Growth
        revenue_growth,
        earnings_growth,
        earnings_quarterly_growth,
        revenue_per_share,

        -- Financial health
        total_debt,
        total_cash,
        debt_to_equity,
        current_ratio,
        quick_ratio,
        free_cash_flow,
        operating_cash_flow,

        -- Classifications
        market_cap_category,
        is_dividend_payer,
        is_high_growth,
        is_value,
        is_defensive,
        is_cyclical,
        is_rate_sensitive,
        is_inflation_hedge,

        -- ETF-specific
        expense_ratio,
        total_assets,
        category,
        fund_family,

        -- Metadata
        fetched_at

    from raw
    where ticker is not null
)

select * from cleaned
