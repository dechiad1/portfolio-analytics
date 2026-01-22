-- Marts model: Calculate performance metrics for each holding
-- Includes both 1-year and 5-year performance metrics

with daily_returns as (
    select * from {{ ref('int_daily_returns') }}
),

benchmarks as (
    select * from {{ ref('stg_benchmarks') }}
),

-- Get the most recent date in the data
latest_date as (
    select max(date) as max_date from daily_returns
),

-- Calculate date boundaries
date_bounds as (
    select
        max_date,
        max_date - interval '1 year' as date_1y_ago,
        max_date - interval '5 years' as date_5y_ago
    from latest_date
),

-- Get benchmark (S&P 500 / VFIAX) returns for comparison
benchmark_1y as (
    select
        ((last(d.price order by d.date) / first(d.price order by d.date)) - 1) * 100 as sp500_return_1y
    from daily_returns d
    cross join date_bounds db
    where d.ticker = 'VFIAX'
      and d.date >= db.date_1y_ago
),

benchmark_5y as (
    select
        ((last(d.price order by d.date) / first(d.price order by d.date)) - 1) * 100 as sp500_return_5y
    from daily_returns d
    cross join date_bounds db
    where d.ticker = 'VFIAX'
      and d.date >= db.date_5y_ago
),

-- Full period benchmark return
benchmark_full as (
    select
        ((last(d.price order by d.date) / first(d.price order by d.date)) - 1) * 100 as sp500_return_full
    from daily_returns d
    where d.ticker = 'VFIAX'
),

-- Average risk-free rate for each period
risk_free_1y as (
    select avg(risk_free_rate) as avg_rf_1y
    from benchmarks b
    cross join date_bounds db
    where b.date >= db.date_1y_ago
),

risk_free_5y as (
    select avg(risk_free_rate) as avg_rf_5y
    from benchmarks b
    cross join date_bounds db
    where b.date >= db.date_5y_ago
),

risk_free_full as (
    select avg(risk_free_rate) as avg_rf_full
    from benchmarks
),

-- Calculate full period metrics (for backwards compatibility with dim_funds)
metrics_full as (
    select
        d.ticker,
        min(d.date) as first_date,
        max(d.date) as last_date,
        min(d.price) as min_price,
        max(d.price) as max_price,
        first(d.price order by d.date) as starting_price,
        last(d.price order by d.date) as ending_price,
        ((last(d.price order by d.date) / first(d.price order by d.date)) - 1) * 100 as total_return_full_pct,
        stddev(d.daily_return) * sqrt(252) * 100 as volatility_full_pct,
        count(distinct d.date) as trading_days,
        count(distinct date_trunc('month', d.date)) as months_tracked
    from daily_returns d
    group by d.ticker
),

-- Calculate 1-Year metrics per ticker
metrics_1y as (
    select
        d.ticker,
        ((last(d.price order by d.date) / first(d.price order by d.date)) - 1) * 100 as total_return_1y_pct,
        stddev(d.daily_return) * sqrt(252) * 100 as volatility_1y_pct,
        count(distinct d.date) as trading_days_1y
    from daily_returns d
    cross join date_bounds db
    where d.date >= db.date_1y_ago
    group by d.ticker
),

-- Calculate 5-Year metrics per ticker
metrics_5y as (
    select
        d.ticker,
        ((last(d.price order by d.date) / first(d.price order by d.date)) - 1) * 100 as total_return_5y_pct,
        stddev(d.daily_return) * sqrt(252) * 100 as volatility_5y_pct,
        count(distinct d.date) as trading_days_5y
    from daily_returns d
    cross join date_bounds db
    where d.date >= db.date_5y_ago
    group by d.ticker
),

-- Combine all metrics
combined as (
    select
        mf.ticker,

        -- Full period metrics (for backwards compatibility)
        mf.first_date,
        mf.last_date,
        mf.min_price,
        mf.max_price,
        mf.starting_price,
        mf.ending_price,
        mf.trading_days,
        mf.months_tracked,
        rff.avg_rf_full as avg_risk_free_rate,
        bf.sp500_return_full as benchmark_total_return,

        -- Legacy fields (map to full period for backwards compat)
        mf.total_return_full_pct as total_return_pct,
        -- Annualized return based on years tracked
        case
            when mf.months_tracked > 0
            then (power(1 + mf.total_return_full_pct / 100, 12.0 / mf.months_tracked) - 1) * 100
            else null
        end as annualized_return_pct,
        mf.volatility_full_pct as volatility_pct,
        case
            when mf.volatility_full_pct > 0
            then (mf.total_return_full_pct - (rff.avg_rf_full * 100)) / mf.volatility_full_pct
            else null
        end as sharpe_ratio,
        mf.total_return_full_pct - bf.sp500_return_full as vs_benchmark_pct,

        -- 1-Year metrics
        m1.total_return_1y_pct,
        m1.total_return_1y_pct - (rf1.avg_rf_1y * 100) as return_vs_risk_free_1y_pct,
        m1.total_return_1y_pct - b1.sp500_return_1y as return_vs_sp500_1y_pct,
        m1.volatility_1y_pct,
        case
            when m1.volatility_1y_pct > 0
            then (m1.total_return_1y_pct - (rf1.avg_rf_1y * 100)) / m1.volatility_1y_pct
            else null
        end as sharpe_ratio_1y,
        m1.trading_days_1y,

        -- 5-Year metrics
        m5.total_return_5y_pct,
        m5.total_return_5y_pct - (rf5.avg_rf_5y * 5 * 100) as return_vs_risk_free_5y_pct,
        m5.total_return_5y_pct - b5.sp500_return_5y as return_vs_sp500_5y_pct,
        m5.volatility_5y_pct,
        case
            when m5.volatility_5y_pct > 0
            then ((m5.total_return_5y_pct / 5) - (rf5.avg_rf_5y * 100)) / m5.volatility_5y_pct
            else null
        end as sharpe_ratio_5y,
        m5.trading_days_5y

    from metrics_full mf
    left join metrics_1y m1 on mf.ticker = m1.ticker
    left join metrics_5y m5 on mf.ticker = m5.ticker
    cross join benchmark_1y b1
    cross join benchmark_5y b5
    cross join benchmark_full bf
    cross join risk_free_1y rf1
    cross join risk_free_5y rf5
    cross join risk_free_full rff
)

select * from combined
