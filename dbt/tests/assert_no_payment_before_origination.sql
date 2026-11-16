-- Fails if any installment was due or paid before its loan was originated.
select p.payment_id, p.due_date, p.paid_date, l.origination_date
from {{ ref('stg_payments') }} p
join {{ ref('stg_loans') }} l using (loan_id)
where p.due_date <= l.origination_date
   or p.paid_date < l.origination_date
