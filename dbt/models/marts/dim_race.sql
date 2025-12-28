{{
    config(
        materialized='table'
    )
}}

with races as (
    select * from {{ ref('stg_races') }}
),

circuits as (
    select * from {{ ref('stg_circuits') }}
),

race_stats as (
    select
        race_id,
        count(*) as total_drivers,
        sum(case when is_dnf then 1 else 0 end) as dnf_count,
        sum(case when is_dnf then 1 else 0 end)::decimal / count(*) as dnf_rate,
        max(laps) as total_laps
    from {{ ref('int_results_enriched') }}
    group by race_id
),

final as (
    select
        -- Race identification
        r.race_id,
        r.year,
        r.round,
        r.race_name,
        r.race_date,
        r.race_time,

        -- Circuit details
        r.circuit_id,
        c.circuit_name,
        c.country as circuit_country,
        c.location as circuit_location,

        -- Race statistics
        coalesce(s.total_drivers, 0) as total_drivers,
        coalesce(s.dnf_count, 0) as dnf_count,
        round(coalesce(s.dnf_rate, 0), 3) as dnf_rate,
        s.total_laps

    from races r
    inner join circuits c on r.circuit_id = c.circuit_id
    left join race_stats s on r.race_id = s.race_id
)

select * from final
