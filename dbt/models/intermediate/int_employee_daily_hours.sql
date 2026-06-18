select
    shift_date,
    employee_name,
    sum(hours_worked) as hours_worked,
    count(*) as shift_count
from {{ ref('stg_shifts') }}
group by shift_date, employee_name
