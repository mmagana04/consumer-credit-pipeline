-- One row per borrower with a simple, explainable rule-based credit risk tier.
-- DTI here = monthly payments on this lender's open loans x 12 / annual income.
with borrower_loans as (
    select
        borrower_id,
        count(*)                                                        as total_loans,
        count(*) filter (where loan_status = 'open')                    as open_loans,
        sum(case when loan_status = 'open' then monthly_payment else 0 end) as monthly_obligations,
        sum(case when loan_status = 'open' then outstanding_principal else 0 end) as open_balance,
        max(days_past_due)                                              as worst_current_dpd,
        max(case when loan_status = 'charged_off' then 1 else 0 end) = 1 as has_charge_off
    from {{ ref('fct_loan_performance') }}
    group by borrower_id
)

select
    b.borrower_id,
    b.state,
    b.credit_score,
    b.credit_band,
    b.annual_income,
    coalesce(l.total_loans, 0)          as total_loans,
    coalesce(l.open_loans, 0)           as open_loans,
    round(coalesce(l.open_balance, 0), 2) as open_balance,
    round(coalesce(l.monthly_obligations, 0) * 12 / nullif(b.annual_income, 0), 4) as dti,
    coalesce(l.worst_current_dpd, 0)    as worst_current_dpd,
    coalesce(l.has_charge_off, false)   as has_charge_off,
    case
        when coalesce(l.has_charge_off, false)
          or coalesce(l.worst_current_dpd, 0) >= 60
          or b.credit_score < 580
          or coalesce(l.monthly_obligations, 0) * 12 / nullif(b.annual_income, 0) > 0.45
            then 'high'
        when coalesce(l.worst_current_dpd, 0) >= 30
          or b.credit_score < 670
          or coalesce(l.monthly_obligations, 0) * 12 / nullif(b.annual_income, 0) > 0.36
            then 'medium'
        else 'low'
    end as risk_tier
from {{ ref('stg_borrowers') }} b
left join borrower_loans l using (borrower_id)
