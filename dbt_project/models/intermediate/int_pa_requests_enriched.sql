with requests as (
    select * from {{ ref('stg_pa_requests') }}
),

payers as (
    select * from {{ ref('stg_payers') }}
),

procedures as (
    select * from {{ ref('stg_procedures') }}
),

providers as (
    select * from {{ ref('stg_providers') }}
),

enriched as (
    select
        r.request_id,
        r.patient_id,
        r.provider_npi,
        r.payer_id,
        r.procedure_code,
        r.submitted_at,
        r.decided_at,
        r.status,
        r.is_urgent,
        r.denial_reason_code,
        r.denial_reason_text,
        r.elapsed_hours,
        r.sla_limit_hours,
        r.sla_breach_flag,
        r.approaching_breach,
        r.days_pending,
        r.auto_approve_score,
        r.created_at,

        -- payer info
        p.payer_name,
        p.avg_response_hrs        as payer_avg_response_hrs,
        p.base_denial_rate        as payer_base_denial_rate,

        -- procedure info
        pr.procedure_description,
        pr.specialty               as procedure_specialty,
        pr.high_denial_flag,

        -- provider info
        pv.provider_name,
        pv.provider_specialty,
        pv.provider_state,
        pv.organization,

        -- derived time fields
        date_trunc('week', r.submitted_at)   as submission_week,
        date_trunc('month', r.submitted_at)  as submission_month,
        dayofweek(r.submitted_at)            as submission_dow,

        -- urgency label
        case
            when r.is_urgent then 'Expedited'
            else 'Standard'
        end                                  as urgency_type,

        -- SLA risk label for Streamlit
        case
            when r.status = 'pending' and r.days_pending >= r.sla_limit_hours
                then 'Breached'
            when r.status = 'pending' and r.approaching_breach
                then 'At Risk'
            when r.status = 'pending'
                then 'On Track'
            when r.sla_breach_flag
                then 'Breached'
            else 'Within SLA'
        end                                  as sla_status,

        -- hours remaining before breach (pending only)
        case
            when r.status = 'pending'
                then r.sla_limit_hours - r.days_pending
            else null
        end                                  as hours_until_breach

    from requests r
    left join payers     p  on r.payer_id       = p.payer_id
    left join procedures pr on r.procedure_code = pr.procedure_code
    left join providers  pv on r.provider_npi   = pv.provider_npi
)

select * from enriched
