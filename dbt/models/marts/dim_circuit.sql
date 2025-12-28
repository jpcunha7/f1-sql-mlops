{{
    config(
        materialized='table'
    )
}}

with circuits as (
    select * from {{ ref('stg_circuits') }}
),

circuit_stats as (
    select
        circuit_id,
        count(distinct race_id) as times_hosted,
        count(distinct year) as years_active,
        min(year) as first_race_year,
        max(year) as last_race_year,
        avg(laps) as avg_laps_per_race,
        sum(case when is_dnf then 1 else 0 end)::decimal / count(*) as avg_dnf_rate
    from {{ ref('int_results_enriched') }}
    group by circuit_id
),

final as (
    select
        -- Circuit identification
        c.circuit_id,
        c.circuit_ref,
        c.circuit_name,

        -- Location details
        c.location,
        c.country,
        c.latitude,
        c.longitude,
        c.altitude,

        -- Circuit statistics
        coalesce(s.times_hosted, 0) as times_hosted,
        coalesce(s.years_active, 0) as years_active,
        s.first_race_year,
        s.last_race_year,
        round(s.avg_laps_per_race, 1) as avg_laps_per_race,
        round(s.avg_dnf_rate, 3) as avg_dnf_rate

    from circuits c
    left join circuit_stats s on c.circuit_id = s.circuit_id
)

select * from final
