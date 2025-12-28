{{
    config(
        materialized='table'
    )
}}

with cleaned as (
    select * from {{ ref('int_qualifying_clean') }}
),

final as (
    select
        -- Primary key
        qualify_id,

        -- Foreign keys (dimensions)
        race_id,
        driver_id,
        constructor_id,
        circuit_id,

        -- Race context
        year,
        round,

        -- Qualifying performance
        qualifying_position,
        q1,
        q2,
        q3,
        best_qualifying_time,

        -- Session completion flags
        completed_q1,
        completed_q2,
        completed_q3,

        -- Derived flags
        case when qualifying_position = 1 then true else false end as is_pole_position,
        case when qualifying_position <= 3 then true else false end as is_top_3,
        case when qualifying_position <= 10 then true else false end as is_top_10

    from cleaned
)

select * from final
