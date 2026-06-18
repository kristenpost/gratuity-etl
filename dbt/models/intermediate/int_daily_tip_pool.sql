select
    shift_date,
    gross_sales,
    cash_tips,
    credit_tips,
    auto_gratuity_amount,
    total_tip_pool
from {{ ref('stg_daily_tips') }}
