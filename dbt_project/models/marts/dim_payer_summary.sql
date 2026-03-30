with base as (
    select * from {{ ref('int_pa_requests_enriched') }}
),

payer_stats as (
    select
        payer_id,
        payer_name,
        payer_avg_response_hrs,
        payer_base_denial_rate,

        count(*)                                                    as total_requests,

        count(case when status = 'approved' then 1 end)            as total_approved,
        count(case when status = 'denied'   then 1 end)            as total_denied,
        count(case when status = 'pending'  then 1 end)            as total_pending,

        round(
            count(case when status = 'denied' then 1 end) * 100.0
            / nullif(count(*), 0), 2
        )                                                           as denial_rate_pct,

        round(avg(case when status != 'pending' then elapsed_hours end), 2)
                                                                    as avg_approval_hrs,

        round(min(case when status != 'pending' then elapsed_hours end), 2)
                                                                    as min_approval_hrs,

        round(max(case when status != 'pending' then elapsed_hours end), 2)
                                                                    as max_approval_hrs,

        count(case when sla_breach_flag = true then 1 end)         as total_sla_breaches,

        round(
            count(case when sla_breach_flag = true then 1 end) * 100.0
            / nullif(count(case when status != 'pending' then 1 end), 0), 2
        )                                                           as sla_breach_rate_pct,

        count(case when approaching_breach = true then 1 end)      as requests_approaching_breach

    from base
    group by
        payer_id, payer_name,
        payer_avg_response_hrs, payer_base_denial_rate
)

select * from payer_stats
order by avg_approval_hrs desc
