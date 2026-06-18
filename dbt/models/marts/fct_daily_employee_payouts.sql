with hours as (
    select * from {{ ref('int_employee_daily_hours') }}
),

pools as (
    select * from {{ ref('int_daily_tip_pool') }}
),

daily_totals as (
    select
        shift_date,
        sum(hours_worked) as total_hours_all_staff
    from hours
    group by shift_date
),

prorated as (
    select
        h.shift_date,
        h.employee_name,
        h.hours_worked,
        h.shift_count,
        d.total_hours_all_staff,
        safe_divide(h.hours_worked, d.total_hours_all_staff) as hours_share_pct,
        p.gross_sales,
        p.auto_gratuity_amount,
        p.cash_tips,
        p.credit_tips,
        p.total_tip_pool,
        round(safe_divide(h.hours_worked, d.total_hours_all_staff) * p.auto_gratuity_amount, 2)
            as auto_gratuity_share,
        round(safe_divide(h.hours_worked, d.total_hours_all_staff) * p.cash_tips, 2)
            as cash_share,
        round(safe_divide(h.hours_worked, d.total_hours_all_staff) * p.credit_tips, 2)
            as credit_share,
        round(safe_divide(h.hours_worked, d.total_hours_all_staff) * p.total_tip_pool, 2)
            as total_payout
    from hours as h
    inner join daily_totals as d
        on h.shift_date = d.shift_date
    inner join pools as p
        on h.shift_date = p.shift_date
)

select *
from prorated
