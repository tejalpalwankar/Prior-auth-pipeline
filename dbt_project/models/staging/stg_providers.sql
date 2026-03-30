with source as (
    select * from {{ source('raw', 'providers') }}
)

select
    provider_npi,
    trim(provider_name)                     as provider_name,
    trim(specialty)                         as provider_specialty,
    trim(state)                             as provider_state,
    trim(organization)                      as organization,
    current_timestamp                       as loaded_at

from source