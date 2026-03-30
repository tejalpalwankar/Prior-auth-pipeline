with source as (
    select * from {{ source('raw', 'payers') }}
)

select
    payer_id,
    trim(payer_name)                        as payer_name,
    cast(avg_response_hrs as double)        as avg_response_hrs,
    cast(base_denial_rate as double)        as base_denial_rate,
    current_timestamp                       as loaded_at

from source