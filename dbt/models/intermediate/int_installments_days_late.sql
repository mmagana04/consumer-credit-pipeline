-- One row per installment, with how late it was (or still is) as of the reporting date.
select
    *,
    case
        when is_paid then greatest(date_diff('day', due_date, paid_date), 0)
        else date_diff('day', due_date, {{ as_of_date() }})
    end as days_late
from {{ ref('stg_payments') }}
where due_date <= {{ as_of_date() }}
