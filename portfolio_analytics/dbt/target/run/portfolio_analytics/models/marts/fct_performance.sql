
  
    
    

    create  table
      "portfolio"."main_marts"."fct_performance__dbt_tmp"
  
    as (
      -- Marts model: Calculate performance metrics for each holding

with daily_returns as (
    select * from "portfolio"."main_intermediate"."int_daily_returns"
),

monthly_returns as (
    select * from "portfolio"."main_intermediate"."int_monthly_returns"
),

benchmarks as (
    select * from "portfolio"."main_staging"."stg_benchmarks"
),

-- Calculate metrics per ticker
performance_metrics as (
    select
        d.ticker,
        
        -- Price data
        min(d.date) as first_date,
        max(d.date) as last_date,
        min(d.price) as min_price,
        max(d.price) as max_price,
        first(d.price order by d.date) as starting_price,
        last(d.price order by d.date) as ending_price,
        
        -- Total return
        ((last(d.price order by d.date) / first(d.price order by d.date)) - 1) * 100 as total_return_pct,
        
        -- Annualized return (assuming 3.75 years)
        (power(last(d.price order by d.date) / first(d.price order by d.date), 1.0 / 3.75) - 1) * 100 as annualized_return_pct,
        
        -- Volatility (annualized standard deviation of daily returns)
        stddev(d.daily_return) * sqrt(252) * 100 as volatility_pct,
        
        -- Count metrics
        count(distinct d.date) as trading_days,
        count(distinct date_trunc('month', d.date)) as months_tracked
        
    from daily_returns d
    group by d.ticker
),

-- Add Sharpe ratio calculation
with_sharpe as (
    select
        pm.*,
        -- Average risk-free rate over the period
        (select avg(risk_free_rate) from benchmarks) as avg_risk_free_rate,
        -- Sharpe ratio
        case 
            when pm.volatility_pct > 0 
            then (pm.annualized_return_pct - ((select avg(risk_free_rate) from benchmarks) * 100)) / pm.volatility_pct
            else null
        end as sharpe_ratio
    from performance_metrics pm
),

-- Add benchmark comparison
with_benchmark as (
    select
        ws.*,
        -- Get S&P 500 return for comparison
        (select total_return_pct from performance_metrics where ticker = 'VFIAX') as benchmark_total_return,
        ws.total_return_pct - (select total_return_pct from performance_metrics where ticker = 'VFIAX') as vs_benchmark_pct
    from with_sharpe ws
)

select * from with_benchmark
    );
  
  