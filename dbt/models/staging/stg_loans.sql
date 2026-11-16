select
    loan_id,
    borrower_id,
    lower(product_type)              as product_type,
    cast(principal as double)        as principal,
    cast(apr as double)              as apr,
    cast(term_months as integer)     as term_months,
    cast(monthly_payment as double)  as monthly_payment,
    cast(origination_date as date)   as origination_date,
    date_trunc('quarter', cast(origination_date as date)) as vintage_quarter
from {{ source('raw', 'loans') }}
