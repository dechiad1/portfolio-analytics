
  
  create view "portfolio"."main_staging"."stg_holdings__dbt_tmp" as (
    -- Staging model: Portfolio holdings from seed data

with source as (
    select * from "portfolio"."main_seeds"."holdings"
),

cleaned as (
    select
        ticker,
        name,
        asset_class,
        sector,
        broker,
        cast(purchase_date as date) as purchase_date
    from source
)

select * from cleaned
  );
