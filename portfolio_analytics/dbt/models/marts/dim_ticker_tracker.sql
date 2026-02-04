-- Marts model: Unified ticker tracker for ingestion scripts
-- Combines tickers from seed file and user portfolios (PostgreSQL)
-- Used by Python ingestion scripts to know which tickers to fetch data for

{{ config(**mart_config('dim_ticker_tracker')) }}

with seed_tickers as (
    -- Tickers from manually curated seed file
    select
        ticker,
        name as display_name,
        asset_class,
        sector,
        'seed' as source
    from {{ ref('stg_holdings') }}
    where ticker is not null
      and trim(ticker) != ''
),

postgres_tickers as (
    -- Tickers from user portfolios (via PostgreSQL replication)
    select
        ed.ticker,
        sr.display_name,
        coalesce(ed.sector, 'Unknown') as asset_class,
        ed.sector,
        'postgres' as source
    from {{ ref('stg_equity_details') }} ed
    left join {{ ref('stg_security_registry') }} sr on ed.security_id = sr.security_id
    where ed.ticker is not null
      and trim(ed.ticker) != ''
),

-- Get seed data grouped by ticker
seed_grouped as (
    select
        ticker,
        first(display_name) as display_name,
        first(asset_class) as asset_class,
        first(sector) as sector
    from seed_tickers
    group by ticker
),

-- Get postgres data grouped by ticker
postgres_grouped as (
    select
        ticker,
        first(display_name) as display_name,
        first(asset_class) as asset_class,
        first(sector) as sector
    from postgres_tickers
    group by ticker
),

-- Get all unique tickers
all_tickers as (
    select ticker from seed_grouped
    union
    select ticker from postgres_grouped
),

-- Join back to get metadata, preferring seed over postgres
final as (
    select
        t.ticker,
        coalesce(s.display_name, p.display_name) as display_name,
        coalesce(s.asset_class, p.asset_class, 'Unknown') as asset_class,
        coalesce(s.sector, p.sector, 'Unknown') as sector,
        s.ticker is not null as is_in_seed,
        p.ticker is not null as is_in_portfolio,
        case
            when s.ticker is not null and p.ticker is not null then 'both'
            when s.ticker is not null then 'seed_only'
            else 'portfolio_only'
        end as source_type,
        current_timestamp as updated_at
    from all_tickers t
    left join seed_grouped s on t.ticker = s.ticker
    left join postgres_grouped p on t.ticker = p.ticker
)

select * from final
order by ticker
