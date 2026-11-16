-- Loan-level payment summary and current delinquency as of the reporting date.
-- Days past due (DPD) = days since the OLDEST unpaid installment was due.
with payment_summary as (
    select
        loan_id,
        count(*)                                                    as installments_due,
        count(paid_date)                                            as installments_paid,
        sum(amount_paid)                                            as total_paid,
        sum(case when is_paid then principal_component else 0 end) as principal_repaid,
        min(case when not is_paid then due_date end)               as oldest_unpaid_due_date,
        max(days_late)                                              as max_days_late_ever
    from {{ ref('int_installments_days_late') }}
    group by loan_id
),

joined as (
    select
        l.*,
        coalesce(p.installments_due, 0)    as installments_due,
        coalesce(p.installments_paid, 0)   as installments_paid,
        coalesce(p.total_paid, 0)          as total_paid,
        l.principal - coalesce(p.principal_repaid, 0) as outstanding_principal,
        p.oldest_unpaid_due_date,
        coalesce(p.max_days_late_ever, 0)  as max_days_late_ever,
        case
            when p.oldest_unpaid_due_date is null then 0
            else date_diff('day', p.oldest_unpaid_due_date, {{ as_of_date() }})
        end as days_past_due
    from {{ ref('stg_loans') }} l
    left join payment_summary p using (loan_id)
)

select
    *,
    {{ delinquency_bucket('days_past_due') }} as delinquency_bucket,
    case
        when installments_paid >= term_months then 'paid_off'
        when days_past_due >= 180            then 'charged_off'
        else 'open'
    end as loan_status
from joined
