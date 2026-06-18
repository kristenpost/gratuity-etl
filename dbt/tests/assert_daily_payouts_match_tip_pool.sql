-- Assert daily employee payouts sum to the tip pool within a penny tolerance.
select
    p.shift_date,
    p.total_tip_pool,
    sum(f.total_payout) as summed_payouts,
    abs(p.total_tip_pool - sum(f.total_payout)) as payout_diff
from {{ ref('int_daily_tip_pool') }} as p
inner join {{ ref('fct_daily_employee_payouts') }} as f
    on p.shift_date = f.shift_date
group by p.shift_date, p.total_tip_pool
having abs(p.total_tip_pool - sum(f.total_payout)) > 0.02
