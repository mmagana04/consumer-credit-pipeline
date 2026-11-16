select
    payment_id,
    loan_id,
    cast(installment_number as integer)  as installment_number,
    cast(due_date as date)               as due_date,
    cast(amount_due as double)           as amount_due,
    cast(principal_component as double)  as principal_component,
    cast(interest_component as double)   as interest_component,
    cast(paid_date as date)              as paid_date,
    cast(amount_paid as double)          as amount_paid,
    paid_date is not null                as is_paid
from {{ source('raw', 'payments') }}
