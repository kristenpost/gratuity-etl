with source as (
    select * from {{ source('gratuity_raw', 'shifts') }}
),

cleaned as (
    select
        shift_date,
        trim(employee_name) as employee_name,
        clock_in,
        clock_out,
        coalesce(
            hours_worked,
            case
                when clock_out is not null
                    then round(timestamp_diff(clock_out, clock_in, minute) / 60.0, 2)
                else 0.0
            end
        ) as hours_worked,
        coalesce(is_mid_shift_clockout, false) as is_mid_shift_clockout,
        loaded_at
    from source
)

select *
from cleaned
where hours_worked > 0
