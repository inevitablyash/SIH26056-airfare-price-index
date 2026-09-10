import sqlite3
import random
from datetime import date, timedelta, datetime


DB_NAME = "airfare.db"

random.seed(42)


# ==================================================
# DATABASE
# ==================================================

conn = sqlite3.connect(DB_NAME)

cursor = conn.cursor()


# ==================================================
# SOURCES
# ==================================================

sources = [

    (
        "Airline Portal",
        "Airline",
        "prototype-airline-source"
    ),

    (
        "OTA Portal A",
        "OTA",
        "prototype-ota-a"
    ),

    (
        "OTA Portal B",
        "OTA",
        "prototype-ota-b"
    )

]


for source_name, source_type, website in sources:

    cursor.execute(
        """
        INSERT INTO sources
        (
            source_name,
            source_type,
            website
        )

        VALUES (?, ?, ?)
        """,

        (
            source_name,
            source_type,
            website
        )
    )


# ==================================================
# ROUTES
# ==================================================

routes = [

    ("DEL-BOM", "DEL", "BOM", 0.18),

    ("BOM-DEL", "BOM", "DEL", 0.16),

    ("DEL-BLR", "DEL", "BLR", 0.15),

    ("BLR-DEL", "BLR", "DEL", 0.13),

    ("HYD-DEL", "HYD", "DEL", 0.10),

    ("DEL-HYD", "DEL", "HYD", 0.09),

    ("BOM-BLR", "BOM", "BLR", 0.06),

    ("BLR-BOM", "BLR", "BOM", 0.05),

    ("HYD-BOM", "HYD", "BOM", 0.04),

    ("BOM-HYD", "BOM", "HYD", 0.04)

]


for route_name, origin, destination, weight in routes:

    cursor.execute(
        """
        INSERT INTO routes
        (
            route_name,
            origin,
            destination,
            weight
        )

        VALUES (?, ?, ?, ?)
        """,

        (
            route_name,
            origin,
            destination,
            weight
        )
    )


# ==================================================
# AIRLINES
# ==================================================

airlines = [

    "IndiGo",

    "Air India",

    "Akasa Air"

]


# ==================================================
# BOOKING WINDOWS
# ==================================================

booking_windows = [

    1,
    7,
    15,
    30,
    45

]


# ==================================================
# BASE PRICES
# ==================================================

base_prices = {

    "DEL-BOM": 5200,

    "BOM-DEL": 5100,

    "DEL-BLR": 6000,

    "BLR-DEL": 5900,

    "HYD-DEL": 4700,

    "DEL-HYD": 4600,

    "BOM-BLR": 4800,

    "BLR-BOM": 4700,

    "HYD-BOM": 4300,

    "BOM-HYD": 4200

}


# ==================================================
# BOOKING WINDOW PRICE EFFECT
# ==================================================

window_factor = {

    1: 1.18,

    7: 1.08,

    15: 1.02,

    30: 0.97,

    45: 0.93

}


# ==================================================
# DATE RANGE
# ==================================================

start_date = date(
    2026,
    8,
    11
)

number_of_days = 30


# ==================================================
# GENERATE OBSERVATIONS
# ==================================================

observation_count = 0


for day_offset in range(number_of_days):

    booking_date = (
        start_date +
        timedelta(days=day_offset)
    )


    for route_name, origin, destination, route_weight in routes:

        for airline in airlines:

            for days_to_departure in booking_windows:


                # ----------------------------------
                # Travel date
                # ----------------------------------

                travel_date = (
                    booking_date +
                    timedelta(
                        days=days_to_departure
                    )
                )


                # ----------------------------------
                # Base route price
                # ----------------------------------

                route_base = base_prices[
                    route_name
                ]


                # ----------------------------------
                # Booking window effect
                # ----------------------------------

                price = (
                    route_base *
                    window_factor[
                        days_to_departure
                    ]
                )


                # ----------------------------------
                # Airline effect
                # ----------------------------------

                if airline == "Air India":

                    price *= 1.04

                elif airline == "Akasa Air":

                    price *= 0.96


                # ----------------------------------
                # Daily market movement
                # ----------------------------------

                daily_factor = (
                    1 +
                    random.uniform(
                        -0.05,
                        0.05
                    )
                )


                # ----------------------------------
                # Individual flight variation
                # ----------------------------------

                flight_factor = (
                    1 +
                    random.uniform(
                        -0.04,
                        0.04
                    )
                )


                base_fare = round(

                    price *
                    daily_factor *
                    flight_factor,

                    2

                )


                # ----------------------------------
                # Taxes
                # ----------------------------------

                taxes = round(

                    base_fare *
                    random.uniform(
                        0.15,
                        0.22
                    ),

                    2

                )


                # ----------------------------------
                # Total fare
                # ----------------------------------

                total_fare = round(

                    base_fare +
                    taxes,

                    2

                )


                # ----------------------------------
                # Fare class
                # ----------------------------------

                fare_class = random.choice(

                    [
                        "Economy",
                        "Economy Flex"
                    ]

                )


                # ----------------------------------
                # Source
                # ----------------------------------

                source_id = random.randint(

                    1,
                    len(sources)

                )


                source_name = cursor.execute(
                    """
                    SELECT source_name
                    FROM sources
                    WHERE source_id = ?
                    """,

                    (source_id,)

                ).fetchone()[0]


                # ----------------------------------
                # Collected timestamp
                # ----------------------------------

                collected_at = datetime.now().isoformat(
                    timespec="seconds"
                )


                # ----------------------------------
                # Route ID
                # ----------------------------------

                route_id = cursor.execute(
                    """
                    SELECT route_id
                    FROM routes
                    WHERE route_name = ?
                    """,

                    (route_name,)

                ).fetchone()[0]


                # ----------------------------------
                # INSERT OBSERVATION
                # ----------------------------------

                cursor.execute(
                    """
                    INSERT INTO observations (

                        route_origin,

                        route_destination,

                        airline,

                        travel_date,

                        booking_date,

                        days_to_departure,

                        fare_class,

                        base_fare,

                        taxes,

                        total_fare,

                        source,

                        collected_at,

                        route_id,

                        source_id

                    )

                    VALUES (

                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?,
                        ?, ?

                    )
                    """,

                    (

                        origin,

                        destination,

                        airline,

                        travel_date.isoformat(),

                        booking_date.isoformat(),

                        days_to_departure,

                        fare_class,

                        base_fare,

                        taxes,

                        total_fare,

                        source_name,

                        collected_at,

                        route_id,

                        source_id

                    )

                )


                observation_count += 1


# ==================================================
# SAVE
# ==================================================

conn.commit()


# ==================================================
# VERIFICATION
# ==================================================

total = cursor.execute(
    """
    SELECT COUNT(*)
    FROM observations
    """
).fetchone()[0]


print(
    "=========================================="
)

print(
    "AIRFARE OBSERVATION DATA GENERATED"
)

print(
    "=========================================="
)


print(
    f"Observations inserted: {observation_count}"
)


print(
    f"Database total: {total}"
)


print(
    "\nBooking window distribution:"
)


rows = cursor.execute(
    """
    SELECT
        days_to_departure,
        COUNT(*)

    FROM observations

    GROUP BY days_to_departure

    ORDER BY days_to_departure
    """
).fetchall()


for days, count in rows:

    print(
        f"{days} days -> {count} observations"
    )


# ==================================================
# SAMPLE RECORD
# ==================================================

print(
    "\nSample observation:"
)


sample = cursor.execute(
    """
    SELECT

        observation_id,

        route_origin,

        route_destination,

        airline,

        travel_date,

        booking_date,

        days_to_departure,

        fare_class,

        base_fare,

        taxes,

        total_fare,

        source

    FROM observations

    LIMIT 1
    """
).fetchone()


print(sample)


conn.close()


print(
    "\nDatabase ready."
)