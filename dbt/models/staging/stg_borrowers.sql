select
    borrower_id,
    state,
    cast(annual_income as double)    as annual_income,
    cast(credit_score as integer)    as credit_score,
    cast(employment_years as integer) as employment_years,
    cast(created_at as date)         as created_at,
    case
        when credit_score >= 740 then '740+ super-prime'
        when credit_score >= 670 then '670-739 prime'
        when credit_score >= 580 then '580-669 near-prime'
        else '<580 subprime'
    end as credit_band
from {{ source('raw', 'borrowers') }}
