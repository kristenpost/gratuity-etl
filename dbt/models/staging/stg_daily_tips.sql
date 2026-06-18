with source as (
    select * from {{ source('gratuity_raw', 'daily_tips') }}
)

select
    shift_date,
    gross_sales,
    coalesce(cash_tips, 0) as cash_tips,
    coalesce(credit_tips, 0) as credit_tips,
    round(gross_sales * {{ var('auto_gratuity_rate') }}, 2) as auto_gratuity_amount,
    round(
        (gross_sales * {{ var('auto_gratuity_rate') }})
        + coalesce(cash_tips, 0)
        + coalesce(credit_tips, 0),
        2
    ) as total_tip_pool,
    loaded_at
from source
