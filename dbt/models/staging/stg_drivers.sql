{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('raw', 'raw_drivers') }}
),

renamed as (
    select
        -- Primary key
        "driverId" as driver_id,

        -- Driver identification
        "driverRef" as driver_ref,
        number as driver_number,
        code as driver_code,

        -- Driver details
        forename,
        surname,
        concat(forename, ' ', surname) as full_name,
        dob as date_of_birth,
        nationality

    from source
)

select * from renamed
