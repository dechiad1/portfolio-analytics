
  
    
    

    create  table
      "portfolio"."main_marts"."dim_asset_classes__dbt_tmp"
  
    as (
      -- Marts model: Asset class distribution and analysis

with holdings as (
    select * from "portfolio"."main_staging"."stg_holdings"
),

performance as (
    select * from "portfolio"."main_marts"."fct_performance"
),

combined as (
    select
        h.ticker,
        h.name,
        h.asset_class,
        h.sector,
        h.broker,
        h.purchase_date,
        p.total_return_pct,
        p.annualized_return_pct,
        p.volatility_pct,
        p.sharpe_ratio,
        p.vs_benchmark_pct,
        p.starting_price,
        p.ending_price,
        p.first_date,
        p.last_date
    from holdings h
    left join performance p on h.ticker = p.ticker
)

select * from combined
    );
  
  