-- Fact: Daily prices for all securities
-- Equities/ETFs: closing price from market data
-- Bonds: clean price derived from Treasury yield curve

{{ config(**mart_config('fact_price_daily')) }}

with dim_security as (
    select * from {{ ref('dim_security') }}
),

-- Equity/ETF prices from raw market data
equity_prices as (
    select
        cast(rp.date as date) as as_of_date,
        ds.security_id,
        rp.close as price,
        'market_data' as price_source
    from {{ source('raw', 'raw_prices') }} rp
    inner join dim_security ds
        on rp.ticker = ds.ticker
        and ds.asset_type in ('EQUITY', 'ETF')
),

-- Treasury bond prices derived from yield curve
bond_prices as (
    select
        as_of_date,
        security_id,
        clean_price as price,
        price_source
    from {{ ref('int_treasury_bond_prices') }}
),

-- Union all price sources
all_prices as (
    select * from equity_prices
    union all
    select * from bond_prices
)

select
    as_of_date,
    security_id,
    price,
    price_source
from all_prices
