{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('raw', 'raw_results') }}
),

renamed as (
    select
        -- Primary key
        "resultId" as result_id,

        -- Foreign keys
        "raceId" as race_id,
        "driverId" as driver_id,
        "constructorId" as constructor_id,
        "statusId" as status_id,

        -- Race performance
        number as driver_number,
        grid as grid_position,
        position as finish_position,
        "positionText" as finish_position_text,
        "positionOrder" as finish_position_order,
        points,
        laps,
        time as finish_time,
        milliseconds as finish_time_ms,
        "fastestLap" as fastest_lap,
        rank as fastest_lap_rank,
        "fastestLapTime" as fastest_lap_time,
        "fastestLapSpeed" as fastest_lap_speed

    from source
)

select * from renamed
