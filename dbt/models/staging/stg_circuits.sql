{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('raw', 'raw_circuits') }}
),

renamed as (
    select
        -- Primary key
        "circuitId" as circuit_id,

        -- Circuit details
        "circuitRef" as circuit_ref,
        name as circuit_name,
        location,
        country,
        lat as latitude,
        lng as longitude,
        alt as altitude

    from source
)

select * from renamed
