{{
    config(
        materialized='table'
    )
}}

with drivers as (
    select * from {{ ref('stg_drivers') }}
),

driver_stats as (
    select
        driver_id,
        count(distinct race_id) as total_races,
        count(distinct year) as seasons_active,
        min(year) as first_season,
        max(year) as last_season,
        sum(points) as career_points,
        sum(case when is_top_10 then 1 else 0 end) as top_10_finishes,
        sum(case when is_dnf then 1 else 0 end) as dnf_count,
        count(distinct case when finish_position_order = 1 then race_id end) as wins,
        count(distinct case when finish_position_order <= 3 then race_id end) as podiums
    from {{ ref('int_results_enriched') }}
    group by driver_id
),

final as (
    select
        -- Driver identification
        d.driver_id,
        d.driver_ref,
        d.driver_code,
        d.driver_number,

        -- Driver details
        d.forename,
        d.surname,
        d.full_name,
        d.date_of_birth,
        d.nationality,

        -- Career statistics
        coalesce(s.total_races, 0) as total_races,
        coalesce(s.seasons_active, 0) as seasons_active,
        s.first_season,
        s.last_season,
        coalesce(s.career_points, 0) as career_points,
        coalesce(s.top_10_finishes, 0) as top_10_finishes,
        coalesce(s.dnf_count, 0) as dnf_count,
        coalesce(s.wins, 0) as wins,
        coalesce(s.podiums, 0) as podiums,

        -- Derived metrics
        case
            when s.total_races > 0
            then round(s.top_10_finishes::decimal / s.total_races, 3)
            else 0
        end as top_10_rate,

        case
            when s.total_races > 0
            then round(s.dnf_count::decimal / s.total_races, 3)
            else 0
        end as dnf_rate

    from drivers d
    left join driver_stats s on d.driver_id = s.driver_id
)

select * from final
