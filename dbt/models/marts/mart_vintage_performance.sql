-- How each origination quarter (vintage) has performed over its life.
-- "Ever 30+" = the loan was 30+ days late at any point, a standard early-warning metric.
select
    vintage_quarter,
    product_type,
    count(*)                                                       as loans_originated,
    round(sum(principal), 2)                                       as principal_originated,
    round(avg(apr), 4)                                             as avg_apr,
    round(avg(case when max_days_late_ever >= 30 then 1 else 0 end), 4) as ever_30plus_rate,
    round(avg(case when loan_status = 'charged_off' then 1 else 0 end), 4) as charge_off_rate,
    round(avg(case when loan_status = 'paid_off' then 1 else 0 end), 4)    as paid_off_rate,
    round(sum(total_paid) / nullif(sum(principal), 0), 4)          as cash_collected_to_principal
from {{ ref('fct_loan_performance') }}
group by vintage_quarter, product_type
order by vintage_quarter, product_type
