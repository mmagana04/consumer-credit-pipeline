-- 30/60/90-day delinquency rates on the OPEN book (excludes paid-off and charged-off loans),
-- by product and credit band, with 'ALL' subtotal rows from ROLLUP.
-- Count-based rates = share of loans; balance-based = share of outstanding principal.
select
    coalesce(product_type, 'ALL')  as product_type,
    coalesce(credit_band, 'ALL')   as credit_band,
    count(*)                                        as open_loans,
    round(sum(outstanding_principal), 2)            as outstanding_balance,
    round(avg(case when is_dq30 then 1 else 0 end), 4) as dq30_rate,
    round(avg(case when is_dq60 then 1 else 0 end), 4) as dq60_rate,
    round(avg(case when is_dq90 then 1 else 0 end), 4) as dq90_rate,
    round(
        sum(case when is_dq30 then outstanding_principal else 0 end)
        / nullif(sum(outstanding_principal), 0), 4
    ) as dq30_balance_rate,
    {{ as_of_date() }} as as_of_date
from {{ ref('fct_loan_performance') }}
where loan_status = 'open'
group by rollup (product_type, credit_band)
order by product_type, credit_band
