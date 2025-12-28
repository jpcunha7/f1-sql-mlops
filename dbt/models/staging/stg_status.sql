{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('raw', 'raw_status') }}
),

renamed as (
    select
        -- Primary key
        "statusId" as status_id,

        -- Status details
        status as status_description

    from source
)

select * from renamed
