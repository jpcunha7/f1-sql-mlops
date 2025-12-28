{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('raw', 'raw_races') }}
),

renamed as (
    select
        -- Primary key
        "raceId" as race_id,

        -- Dimensions
        year,
        round,
        "circuitId" as circuit_id,
        name as race_name,
        date as race_date,
        time as race_time

    from source
)

select * from renamed
