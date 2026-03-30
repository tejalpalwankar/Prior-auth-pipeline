-- Only open (pending) requests that are at risk or already breached
-- This is the table powering the Streamlit alert view

select
    request_id,
    patient_id,
    provider_npi,
    provider_name,
    provider_specialty,
    payer_id,
    payer_name,
    procedure_code,
    procedure_description,
    submitted_at,
    urgency_type,
    sla_limit_hours,
    days_pending,
    hours_until_breach,
    sla_status,
    approaching_breach,
    auto_approve_score

from {{ ref('int_pa_requests_enriched') }}

where
    status = 'pending'
    and (approaching_breach = true or days_pending >= sla_limit_hours)

order by
    hours_until_breach asc nulls last,
    days_pending desc
