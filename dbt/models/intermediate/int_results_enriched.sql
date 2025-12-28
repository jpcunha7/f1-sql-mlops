{{
    config(
        materialized='view'
    )
}}

with results as (
    select * from {{ ref('stg_results') }}
),

races as (
    select * from {{ ref('stg_races') }}
),

drivers as (
    select * from {{ ref('stg_drivers') }}
),

constructors as (
    select * from {{ ref('stg_constructors') }}
),

circuits as (
    select * from {{ ref('stg_circuits') }}
),

status as (
    select * from {{ ref('stg_status') }}
),

enriched as (
    select
        -- Result identifiers
        r.result_id,
        r.race_id,
        r.driver_id,
        r.constructor_id,

        -- Race details
        ra.year,
        ra.round,
        ra.race_name,
        ra.race_date,
        ra.circuit_id,
        c.circuit_name,
        c.country as circuit_country,

        -- Driver details
        d.driver_code,
        d.full_name as driver_name,
        d.nationality as driver_nationality,

        -- Constructor details
        co.constructor_name,
        co.nationality as constructor_nationality,

        -- Race performance
        r.grid_position,
        r.finish_position,
        r.finish_position_order,
        r.points,
        r.laps,
        r.finish_time,
        r.finish_time_ms,

        -- Fastest lap
        r.fastest_lap,
        r.fastest_lap_rank,
        r.fastest_lap_time,
        r.fastest_lap_speed,

        -- Status
        r.status_id,
        s.status_description,

        -- Derived flags
        case
            when r.finish_position_order <= 10 then true
            else false
        end as is_top_10,

        case
            when s.status_description = 'Finished' then false
            when s.status_description like '+%' then false  -- Lapped but finished
            else true
        end as is_dnf

    from results r
    inner join races ra on r.race_id = ra.race_id
    inner join drivers d on r.driver_id = d.driver_id
    inner join constructors co on r.constructor_id = co.constructor_id
    inner join circuits c on ra.circuit_id = c.circuit_id
    inner join status s on r.status_id = s.status_id
)

select * from enriched
