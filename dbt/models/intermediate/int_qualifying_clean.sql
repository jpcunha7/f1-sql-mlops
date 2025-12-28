{{
    config(
        materialized='view'
    )
}}

with qualifying as (
    select * from {{ ref('stg_qualifying') }}
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

cleaned as (
    select
        -- Qualifying identifiers
        q.qualify_id,
        q.race_id,
        q.driver_id,
        q.constructor_id,

        -- Race details
        ra.year,
        ra.round,
        ra.race_name,
        ra.circuit_id,

        -- Driver details
        d.driver_code,
        d.full_name as driver_name,

        -- Constructor details
        co.constructor_name,

        -- Qualifying results
        q.qualifying_position,
        q.q1,
        q.q2,
        q.q3,

        -- Derived flags
        case when q.q1 is not null then true else false end as completed_q1,
        case when q.q2 is not null then true else false end as completed_q2,
        case when q.q3 is not null then true else false end as completed_q3,

        -- Best qualifying time (last non-null session)
        coalesce(q.q3, q.q2, q.q1) as best_qualifying_time

    from qualifying q
    inner join races ra on q.race_id = ra.race_id
    inner join drivers d on q.driver_id = d.driver_id
    inner join constructors co on q.constructor_id = co.constructor_id
)

select * from cleaned
