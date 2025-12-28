{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('raw', 'raw_qualifying') }}
),

renamed as (
    select
        -- Primary key
        "qualifyId" as qualify_id,

        -- Foreign keys
        "raceId" as race_id,
        "driverId" as driver_id,
        "constructorId" as constructor_id,

        -- Qualifying results
        number as driver_number,
        position as qualifying_position,
        q1,
        q2,
        q3

    from source
)

select * from renamed
