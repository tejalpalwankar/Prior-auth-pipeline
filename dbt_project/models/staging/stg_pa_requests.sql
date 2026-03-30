with source as (
    select * from {{ source('raw', 'pa_requests') }}
)

select
    request_id,
    patient_id,
    provider_npi,
    payer_id,
    procedure_code,
    cast(submitted_at as timestamp)         as submitted_at,
    cast(decided_at  as timestamp)          as decided_at,
    lower(trim(status))                     as status,
    cast(is_urgent as boolean)              as is_urgent,
    denial_reason_code,
    denial_reason_text,
    cast(elapsed_hours as double)           as elapsed_hours,
    cast(sla_limit_hours as integer)        as sla_limit_hours,
    cast(sla_breach_flag as boolean)        as sla_breach_flag,
    cast(approaching_breach as boolean)     as approaching_breach,
    cast(days_pending as double)            as days_pending,
    cast(auto_approve_score as double)      as auto_approve_score,
    cast(created_at as timestamp)           as created_at,
    current_timestamp                       as loaded_at

from source