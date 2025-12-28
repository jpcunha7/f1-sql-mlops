{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('raw', 'raw_seasons') }}
),

renamed as (
    select
        -- Primary key
        year

    from source
)

select * from renamed
