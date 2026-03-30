with source as (
    select * from {{ source('raw', 'procedures') }}
)

select
    procedure_code,
    trim(description)                       as procedure_description,
    trim(specialty)                         as specialty,
    cast(high_denial as boolean)            as high_denial_flag,
    current_timestamp                       as loaded_at

from source