{{
    config(
        materialized='table'
    )
}}

with enriched as (
    select * from {{ ref('int_results_enriched') }}
),

final as (
    select
        -- Primary key
        result_id,

        -- Foreign keys (dimensions)
        race_id,
        driver_id,
        constructor_id,
        circuit_id,
        status_id,

        -- Race context
        year,
        round,

        -- Performance metrics
        grid_position,
        finish_position,
        finish_position_order,
        points,
        laps,
        finish_time_ms,

        -- Fastest lap metrics
        fastest_lap,
        fastest_lap_rank,
        fastest_lap_time,
        fastest_lap_speed,

        -- Derived metrics
        case
            when grid_position is not null and finish_position_order is not null
            then finish_position_order - grid_position
            else null
        end as positions_gained,

        -- Flags
        is_top_10,
        is_dnf,

        case when finish_position_order = 1 then true else false end as is_win,
        case when finish_position_order <= 3 then true else false end as is_podium,
        case when grid_position = 1 then true else false end as started_pole,
        case when fastest_lap_rank is not null and fastest_lap_rank = 1 then true else false end as had_fastest_lap

    from enriched
)

select * from final
