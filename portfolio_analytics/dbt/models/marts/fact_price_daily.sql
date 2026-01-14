-- Fact: Daily prices for all securities
-- Equities/ETFs: closing price from market data
-- Bonds: clean price (% of par) - sourced from vendor or derived from yields

{{
    config(
        materialized='table'
    )
}}

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

-- Bond prices from raw bond prices (when available)
-- Falls back to last known price or par if no price data
bond_prices as (
    select
        cast(rbp.date as date) as as_of_date,
        ds.security_id,
        rbp.clean_price as price,
        'market_data' as price_source
    from {{ source('raw', 'raw_bond_prices') }} rbp
    inner join dim_security ds
        on rbp.cusip = ds.primary_id_value
        and ds.asset_type = 'BOND'
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
