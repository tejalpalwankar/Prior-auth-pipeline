with base as (
    select * from {{ ref('int_pa_requests_enriched') }}
    where status != 'pending'   -- only decided requests
),

weekly as (
    select
        submission_week,

        count(*)                                                    as total_decided,

        count(case when sla_breach_flag = false then 1 end)        as within_sla,

        count(case when sla_breach_flag = true  then 1 end)        as breached_sla,

        round(
            count(case when sla_breach_flag = false then 1 end) * 100.0
            / nullif(count(*), 0), 2
        )                                                           as sla_compliance_pct,

        round(avg(elapsed_hours), 2)                               as avg_elapsed_hrs,

        count(case when status = 'denied' then 1 end)              as total_denied,

        round(
            count(case when status = 'denied' then 1 end) * 100.0
            / nullif(count(*), 0), 2
        )                                                           as denial_rate_pct

    from base
    group by submission_week
)

select * from weekly
order by submission_week asc
