-- One row per loan: the core fact table for loan performance reporting.
select
    s.loan_id,
    s.borrower_id,
    b.state,
    b.credit_score,
    b.credit_band,
    s.product_type,
    s.vintage_quarter,
    s.origination_date,
    s.principal,
    s.apr,
    s.term_months,
    s.monthly_payment,
    s.installments_due,
    s.installments_paid,
    s.total_paid,
    round(s.outstanding_principal, 2)  as outstanding_principal,
    s.days_past_due,
    s.max_days_late_ever,
    s.delinquency_bucket,
    s.loan_status,
    s.days_past_due >= 30 as is_dq30,
    s.days_past_due >= 60 as is_dq60,
    s.days_past_due >= 90 as is_dq90
from {{ ref('int_loan_status') }} s
join {{ ref('stg_borrowers') }} b using (borrower_id)
