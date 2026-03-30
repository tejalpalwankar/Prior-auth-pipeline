with base as (
    select * from {{ ref('int_pa_requests_enriched') }}
),

procedure_stats as (
    select
        procedure_code,
        procedure_description,
        procedure_specialty,
        high_denial_flag,

        count(*)                                                    as total_requests,

        count(case when status = 'denied' then 1 end)              as total_denied,

        round(
            count(case when status = 'denied' then 1 end) * 100.0
            / nullif(count(*), 0), 2
        )                                                           as denial_rate_pct,

        round(avg(case when status != 'pending' then elapsed_hours end), 2)
                                                                    as avg_approval_hrs,

        count(case when sla_breach_flag = true then 1 end)         as total_sla_breaches

    from base
    group by
        procedure_code, procedure_description,
        procedure_specialty, high_denial_flag
),

-- add top denial reason per procedure
top_denial as (
    select
        procedure_code,
        denial_reason_code,
        count(*) as reason_count,
        row_number() over (
            partition by procedure_code
            order by count(*) desc
        ) as rn
    from base
    where denial_reason_code is not null
    group by procedure_code, denial_reason_code
)

select
    ps.*,
    td.denial_reason_code    as top_denial_reason

from procedure_stats ps
left join top_denial td
    on ps.procedure_code = td.procedure_code
    and td.rn = 1

order by denial_rate_pct desc
