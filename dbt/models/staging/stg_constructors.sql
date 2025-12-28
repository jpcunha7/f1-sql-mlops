{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('raw', 'raw_constructors') }}
),

renamed as (
    select
        -- Primary key
        "constructorId" as constructor_id,

        -- Constructor details
        "constructorRef" as constructor_ref,
        name as constructor_name,
        nationality

    from source
)

select * from renamed
