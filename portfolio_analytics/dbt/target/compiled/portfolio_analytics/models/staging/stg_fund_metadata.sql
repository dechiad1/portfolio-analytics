-- Staging model: Clean and standardize fund metadata

with source as (
    select * from "portfolio"."main"."raw_fund_metadata"
),

cleaned as (
    select
        ticker,
        fund_name,

        -- Convert expense ratio to percentage for easier reading
        -- yfinance returns as decimal (e.g., 0.0003 = 0.03%)
        case
            when expense_ratio is not null
            then round(expense_ratio * 100, 4)  -- Convert to percentage (0.03%)
            else null
        end as expense_ratio_pct,

        fund_family,
        category,
        fund_inception_date,
        total_assets,
        currency,
        exchange,
        quote_type,
        long_business_summary as mandate,
        asset_distribution,
        top_sectors

    from source
)

select * from cleaned