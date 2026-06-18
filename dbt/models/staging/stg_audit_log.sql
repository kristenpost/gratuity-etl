with source as (
    select * from {{ source('gratuity_raw', 'audit_log') }}
)

select
    audit_id,
    trim(employee_name) as employee_name,
    shift_date,
    snapshot_timestamp,
    clock_in,
    clock_out,
    hours_at_snapshot,
    event_type,
    loaded_at
from source
