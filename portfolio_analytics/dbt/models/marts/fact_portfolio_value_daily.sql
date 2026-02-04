-- Fact: Daily portfolio value rollup
-- Computes market value by asset type with proper bond valuation (dirty price)

{{ config(**mart_config('fact_portfolio_value_daily')) }}

with fact_position as (
    select * from {{ ref('fact_position_daily') }}
),

dim_security as (
    select * from {{ ref('dim_security') }}
),

fact_price as (
    select * from {{ ref('fact_price_daily') }}
),

fact_bond_valuation as (
    select * from {{ ref('fact_bond_valuation_daily') }}
),

cash_balance as (
    select * from {{ ref('stg_cash_balance') }}
),

stg_portfolio as (
    select * from {{ ref('stg_portfolio') }}
),

-- Calculate position values by asset type
position_values as (
    select
        fp.as_of_date,
        fp.portfolio_id,
        fp.security_id,
        ds.asset_type,
        fp.quantity,
        fp.total_cost_basis,

        -- Market value calculation differs by asset type
        case
            -- Equities/ETFs: quantity * price
            when ds.asset_type in ('EQUITY', 'ETF') then
                fp.quantity * coalesce(price.price, 0)

            -- Bonds: face_amount * (dirty_price / 100)
            -- quantity for bonds = face amount
            when ds.asset_type = 'BOND' then
                fp.quantity * (coalesce(bv.dirty_price_per_100, 100) / 100)

            else 0
        end as market_value,

        -- Clean value for bonds (excludes accrued interest)
        case
            when ds.asset_type = 'BOND' then
                fp.quantity * (coalesce(bv.clean_price, 100) / 100)
            else null
        end as clean_market_value,

        -- Accrued interest for bonds
        case
            when ds.asset_type = 'BOND' then
                fp.quantity * (coalesce(bv.accrued_interest_per_100, 0) / 100)
            else null
        end as accrued_interest

    from fact_position fp
    inner join dim_security ds on fp.security_id = ds.security_id
    left join fact_price price
        on fp.security_id = price.security_id
        and fp.as_of_date = price.as_of_date
    left join fact_bond_valuation bv
        on fp.security_id = bv.security_id
        and fp.as_of_date = bv.as_of_date
),

-- Aggregate by portfolio and date
portfolio_totals as (
    select
        as_of_date,
        portfolio_id,

        -- Total market value
        sum(market_value) as total_market_value,

        -- Value by asset type
        sum(case when asset_type = 'EQUITY' then market_value else 0 end) as equity_market_value,
        sum(case when asset_type = 'ETF' then market_value else 0 end) as etf_market_value,
        sum(case when asset_type = 'BOND' then market_value else 0 end) as bond_market_value,

        -- Bond-specific breakdowns
        sum(case when asset_type = 'BOND' then clean_market_value else 0 end) as bond_clean_value,
        sum(case when asset_type = 'BOND' then accrued_interest else 0 end) as bond_accrued_interest,

        -- Cost basis
        sum(total_cost_basis) as total_cost_basis,

        -- Position count
        count(distinct security_id) as position_count

    from position_values
    group by as_of_date, portfolio_id
),

-- Add cash balances
final as (
    select
        pt.as_of_date,
        pt.portfolio_id,
        p.portfolio_name,
        p.base_currency,

        -- Cash (from cash_balance table, using portfolio's base currency)
        coalesce(cb.balance, 0) as cash_value,

        -- Securities
        pt.total_market_value as securities_market_value,
        pt.equity_market_value,
        pt.etf_market_value,
        pt.bond_market_value,
        pt.bond_clean_value,
        pt.bond_accrued_interest,

        -- Total portfolio value
        coalesce(cb.balance, 0) + pt.total_market_value as total_portfolio_value,

        -- Cost and P&L
        pt.total_cost_basis,
        pt.total_market_value - pt.total_cost_basis as unrealized_pl,
        case
            when pt.total_cost_basis > 0
            then (pt.total_market_value - pt.total_cost_basis) / pt.total_cost_basis
            else 0
        end as unrealized_pl_pct,

        -- Allocation percentages
        case
            when coalesce(cb.balance, 0) + pt.total_market_value > 0
            then coalesce(cb.balance, 0) / (coalesce(cb.balance, 0) + pt.total_market_value)
            else 0
        end as cash_allocation_pct,
        case
            when coalesce(cb.balance, 0) + pt.total_market_value > 0
            then pt.equity_market_value / (coalesce(cb.balance, 0) + pt.total_market_value)
            else 0
        end as equity_allocation_pct,
        case
            when coalesce(cb.balance, 0) + pt.total_market_value > 0
            then pt.etf_market_value / (coalesce(cb.balance, 0) + pt.total_market_value)
            else 0
        end as etf_allocation_pct,
        case
            when coalesce(cb.balance, 0) + pt.total_market_value > 0
            then pt.bond_market_value / (coalesce(cb.balance, 0) + pt.total_market_value)
            else 0
        end as bond_allocation_pct,

        pt.position_count

    from portfolio_totals pt
    inner join stg_portfolio p on pt.portfolio_id = p.portfolio_id
    left join cash_balance cb
        on pt.portfolio_id = cb.portfolio_id
        and cb.currency = p.base_currency
)

select * from final
