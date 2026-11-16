-- Fails if outstanding principal is negative or exceeds the original principal
-- (small tolerance for cent-level rounding in the amortization schedule).
select loan_id, principal, outstanding_principal
from {{ ref('fct_loan_performance') }}
where outstanding_principal < -1
   or outstanding_principal > principal + 1
