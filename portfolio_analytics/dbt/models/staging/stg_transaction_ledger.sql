-- Staging model: Transaction ledger from Postgres

with source as (
    select * from {{ source('postgres', 'pg_transaction_ledger') }}
),

staged as (
    select
        txn_id,
        portfolio_id,
        event_ts,
        cast(event_ts as date) as event_date,
        txn_type,
        security_id,
        quantity,
        price,
        fees,
        currency,
        notes,
        created_at,
        -- Derived: signed quantity (positive for buys/deposits, negative for sells/withdrawals)
        case
            when txn_type in ('BUY', 'DEPOSIT', 'DIVIDEND', 'COUPON') then quantity
            when txn_type in ('SELL', 'WITHDRAW', 'FEE') then -quantity
            else quantity
        end as signed_quantity,
        -- Derived: transaction value (for cost basis)
        case
            when txn_type in ('BUY', 'SELL') and price is not null
            then quantity * price
            else null
        end as transaction_value
    from source
)

select * from staged
