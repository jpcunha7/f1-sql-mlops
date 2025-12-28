{{
    config(
        materialized='table'
    )
}}

with results as (
    select * from {{ ref('fct_results') }}
),

qualifying as (
    select * from {{ ref('fct_qualifying') }}
),

dim_driver as (
    select * from {{ ref('dim_driver') }}
),

dim_constructor as (
    select * from {{ ref('dim_constructor') }}
),

dim_circuit as (
    select * from {{ ref('dim_circuit') }}
),

dim_race as (
    select * from {{ ref('dim_race') }}
),

-- Join qualifying with results (qualifying happens before race)
pre_race_base as (
    select
        r.result_id,
        r.race_id,
        r.driver_id,
        r.constructor_id,
        r.circuit_id,
        r.year,
        r.round,

        -- Qualifying performance (known before race)
        q.qualifying_position,
        q.q1,
        q.q2,
        q.q3,

        -- Grid position (known before race)
        r.grid_position,

        -- Target variables (NOT features - these are what we predict)
        r.is_top_10 as target_top_10,
        r.is_dnf as target_dnf,

        -- Race metadata
        dr.race_date

    from results r
    left join qualifying q
        on r.race_id = q.race_id
        and r.driver_id = q.driver_id
    inner join dim_race dr on r.race_id = dr.race_id
),

-- Driver recent performance features (using only PREVIOUS races)
driver_recent_performance as (
    select
        result_id,
        race_id,
        driver_id,

        -- Recent form (last N races before this one)
        avg(case when is_top_10 then 1.0 else 0.0 end) over (
            partition by driver_id
            order by year, round
            rows between {{ var('recent_races_window') }} preceding and 1 preceding
        ) as driver_top10_rate_recent,

        avg(case when is_dnf then 1.0 else 0.0 end) over (
            partition by driver_id
            order by year, round
            rows between {{ var('dnf_lookback_window') }} preceding and 1 preceding
        ) as driver_dnf_rate_recent,

        avg(points) over (
            partition by driver_id
            order by year, round
            rows between {{ var('recent_races_window') }} preceding and 1 preceding
        ) as driver_avg_points_recent,

        avg(positions_gained) over (
            partition by driver_id
            order by year, round
            rows between {{ var('recent_races_window') }} preceding and 1 preceding
        ) as driver_avg_positions_gained_recent,

        -- Count of recent races (for new drivers, this will be low)
        count(*) over (
            partition by driver_id
            order by year, round
            rows between {{ var('recent_races_window') }} preceding and 1 preceding
        ) as driver_races_in_window

    from results
),

-- Constructor recent performance features
constructor_recent_performance as (
    select
        result_id,
        race_id,
        driver_id,
        constructor_id,

        -- Recent constructor performance
        avg(case when is_top_10 then 1.0 else 0.0 end) over (
            partition by constructor_id
            order by year, round
            rows between {{ var('recent_races_window') }} preceding and 1 preceding
        ) as constructor_top10_rate_recent,

        avg(case when is_dnf then 1.0 else 0.0 end) over (
            partition by constructor_id
            order by year, round
            rows between {{ var('dnf_lookback_window') }} preceding and 1 preceding
        ) as constructor_dnf_rate_recent,

        avg(points) over (
            partition by constructor_id
            order by year, round
            rows between {{ var('recent_races_window') }} preceding and 1 preceding
        ) as constructor_avg_points_recent

    from results
),

-- Circuit-specific driver performance
driver_circuit_performance as (
    select
        result_id,
        race_id,
        driver_id,
        circuit_id,

        -- How has this driver performed at this circuit before?
        avg(case when is_top_10 then 1.0 else 0.0 end) over (
            partition by driver_id, circuit_id
            order by year, round
            rows between unbounded preceding and 1 preceding
        ) as driver_top10_rate_at_circuit,

        avg(case when is_dnf then 1.0 else 0.0 end) over (
            partition by driver_id, circuit_id
            order by year, round
            rows between unbounded preceding and 1 preceding
        ) as driver_dnf_rate_at_circuit,

        count(*) over (
            partition by driver_id, circuit_id
            order by year, round
            rows between unbounded preceding and 1 preceding
        ) as driver_races_at_circuit

    from results
),

-- Assemble all features
features as (
    select
        -- Identifiers
        b.result_id,
        b.race_id,
        b.driver_id,
        b.constructor_id,
        b.circuit_id,
        b.year,
        b.round,
        b.race_date,

        -- Target variables
        b.target_top_10,
        b.target_dnf,

        -- Pre-race known: Grid position
        b.grid_position,
        b.qualifying_position,

        -- Driver career stats (up to this point)
        dd.total_races as driver_career_races,
        dd.top_10_rate as driver_career_top10_rate,
        dd.dnf_rate as driver_career_dnf_rate,
        dd.wins as driver_career_wins,

        -- Driver recent form
        coalesce(drp.driver_top10_rate_recent, dd.top_10_rate, 0) as driver_top10_rate_recent,
        coalesce(drp.driver_dnf_rate_recent, dd.dnf_rate, 0) as driver_dnf_rate_recent,
        coalesce(drp.driver_avg_points_recent, 0) as driver_avg_points_recent,
        coalesce(drp.driver_avg_positions_gained_recent, 0) as driver_avg_positions_gained_recent,
        coalesce(drp.driver_races_in_window, 0) as driver_races_in_window,

        -- Constructor career stats
        dc.total_race_entries as constructor_career_entries,
        dc.top_10_rate as constructor_career_top10_rate,
        dc.dnf_rate as constructor_career_dnf_rate,

        -- Constructor recent form
        coalesce(crp.constructor_top10_rate_recent, dc.top_10_rate, 0) as constructor_top10_rate_recent,
        coalesce(crp.constructor_dnf_rate_recent, dc.dnf_rate, 0) as constructor_dnf_rate_recent,
        coalesce(crp.constructor_avg_points_recent, 0) as constructor_avg_points_recent,

        -- Circuit characteristics
        dci.avg_dnf_rate as circuit_avg_dnf_rate,
        dci.times_hosted as circuit_times_hosted,

        -- Driver at this specific circuit
        coalesce(dcp.driver_top10_rate_at_circuit, 0) as driver_top10_rate_at_circuit,
        coalesce(dcp.driver_dnf_rate_at_circuit, 0) as driver_dnf_rate_at_circuit,
        coalesce(dcp.driver_races_at_circuit, 0) as driver_races_at_circuit,

        -- Interaction features
        case
            when b.grid_position <= 5 then true
            else false
        end as started_top_5,

        case
            when b.grid_position <= 10 then true
            else false
        end as started_top_10

    from pre_race_base b
    left join driver_recent_performance drp
        on b.result_id = drp.result_id
    left join constructor_recent_performance crp
        on b.result_id = crp.result_id
    left join driver_circuit_performance dcp
        on b.result_id = dcp.result_id
    left join dim_driver dd on b.driver_id = dd.driver_id
    left join dim_constructor dc on b.constructor_id = dc.constructor_id
    left join dim_circuit dci on b.circuit_id = dci.circuit_id
)

select * from features
