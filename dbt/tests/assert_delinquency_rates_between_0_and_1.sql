-- Fails if any delinquency rate is outside [0, 1], or if dq90 > dq60 > dq30 ordering is broken.
select *
from {{ ref('mart_delinquency_rates') }}
where dq30_rate not between 0 and 1
   or dq60_rate not between 0 and 1
   or dq90_rate not between 0 and 1
   or dq60_rate > dq30_rate
   or dq90_rate > dq60_rate
