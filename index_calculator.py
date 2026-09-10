import sqlite3
import math
from collections import defaultdict


DB_NAME = "airfare.db"


# ==================================================
# BOOKING WINDOW WEIGHTS
# ==================================================

WINDOW_WEIGHTS = {
    1: 0.30,
    7: 0.25,
    15: 0.20,
    30: 0.15,
    45: 0.10
}


# ==================================================
# DATABASE
# ==================================================

conn = sqlite3.connect(DB_NAME)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()


# ==================================================
# DATES
# ==================================================

dates = [
    row[0]
    for row in cursor.execute(
        """
        SELECT DISTINCT booking_date
        FROM observations
        ORDER BY booking_date
        """
    ).fetchall()
]


if not dates:
    print("No observations found.")
    conn.close()
    exit()


BASE_DATE = dates[0]


print("==========================================")
print("INDIA AIRFARE PRICE INDEX CALCULATOR")
print("==========================================")
print(f"Base period: {BASE_DATE}")
print(f"Dates found: {len(dates)}")

print("\nBooking window weights:")

for window, weight in WINDOW_WEIGHTS.items():
    print(f"{window} days = {weight * 100:.0f}%")

print(f"Total = {sum(WINDOW_WEIGHTS.values()) * 100:.0f}%")


# ==================================================
# CLEAR PREVIOUS INDEX
# ==================================================

cursor.execute("DELETE FROM index_data")


# ==================================================
# GEOMETRIC MEAN
# ==================================================

def geometric_mean(values):

    values = [
        value
        for value in values
        if value is not None and value > 0
    ]

    if not values:
        return None

    log_sum = sum(math.log(value) for value in values)

    return math.exp(
        log_sum / len(values)
    )


# ==================================================
# ROUTES
# ==================================================

routes = cursor.execute(
    """
    SELECT
        route_id,
        route_name,
        origin,
        destination,
        weight
    FROM routes
    WHERE is_active = 1
    ORDER BY route_id
    """
).fetchall()


if not routes:

    print("No active routes found.")

    conn.close()
    exit()


print(f"\nActive routes: {len(routes)}")


# ==================================================
# PRICE LOOKUP
# ==================================================

def get_prices(
    route_id,
    window,
    booking_date
):
    """
    Get all observed fares for a route,
    booking window and booking date.

    route_id is mandatory in the new schema.
    """

    rows = cursor.execute(
        """
        SELECT total_fare
        FROM observations
        WHERE route_id = ?
          AND days_to_departure = ?
          AND booking_date = ?
          AND total_fare > 0
        """,
        (
            route_id,
            window,
            booking_date
        )
    ).fetchall()

    return [
        row[0]
        for row in rows
    ]


# ==================================================
# BASE PRICES
# ==================================================

base_prices = {}

for (
    route_id,
    route_name,
    origin,
    destination,
    route_weight
) in routes:

    for window in WINDOW_WEIGHTS:

        prices = get_prices(
            route_id,
            window,
            BASE_DATE
        )

        gm = geometric_mean(prices)

        if gm is not None:

            base_prices[
                (route_id, window)
            ] = gm


print(
    f"Base price cells available: "
    f"{len(base_prices)}"
)


# ==================================================
# CALCULATE PRICE RELATIVES
# ==================================================

all_route_window_data = defaultdict(dict)


for current_date in dates:

    for (
        route_id,
        route_name,
        origin,
        destination,
        route_weight
    ) in routes:

        for window in WINDOW_WEIGHTS:

            base_price = base_prices.get(
                (route_id, window)
            )

            if base_price is None:
                continue


            current_prices = get_prices(
                route_id,
                window,
                current_date
            )


            current_price = geometric_mean(
                current_prices
            )


            if current_price is None:
                continue


            relative = (
                current_price / base_price
            ) * 100


            all_route_window_data[
                current_date
            ][
                (route_id, window)
            ] = relative


# ==================================================
# LASPEYRES
# ==================================================

def calculate_laspeyres(route_data):

    weighted_sum = 0.0
    total_weight = 0.0

    for route_id, data in route_data.items():

        weight = data["weight"]
        relative = data["relative"]

        if weight <= 0 or relative <= 0:
            continue

        weighted_sum += (
            weight * relative
        )

        total_weight += weight


    if total_weight == 0:
        return 100.0


    # Normalize when only a subset of routes
    # has valid observations.

    return (
        weighted_sum /
        total_weight
    )


# ==================================================
# PAASCHE
# ==================================================

def calculate_paasche(
    route_data,
    epsilon=-0.85
):

    numerator = 0.0
    denominator = 0.0

    for route_id, data in route_data.items():

        weight = data["weight"]
        relative = data["relative"]

        if weight <= 0 or relative <= 0:
            continue


        numerator += (
            weight *
            (relative ** (1 + epsilon))
        )


        denominator += (
            weight *
            (relative ** epsilon)
        )


    if denominator == 0:
        return 100.0


    return (
        numerator /
        denominator
    )


# ==================================================
# MAIN CALCULATION
# ==================================================

for current_date in dates:

    route_window_values = defaultdict(dict)

    for (
        route_id,
        window
    ), relative in all_route_window_data[current_date].items():

        route_window_values[route_id][window] = relative


    # --------------------------------------------------
    # Calculate national index separately for each
    # booking window
    # --------------------------------------------------

    for window in WINDOW_WEIGHTS:

        route_data = {}

        for (
            route_id,
            route_name,
            origin,
            destination,
            route_weight
        ) in routes:

            relative = route_window_values.get(
                route_id,
                {}
            ).get(window)

            if relative is None:
                continue

            route_data[route_id] = {
                "weight": route_weight,
                "relative": relative
            }


        # --------------------------------------------------
        # National indices for this booking window
        # --------------------------------------------------

        laspeyres = calculate_laspeyres(
            route_data
        )

        paasche = calculate_paasche(
            route_data
        )

        fisher = math.sqrt(
            max(
                0.0,
                laspeyres * paasche
            )
        )


        # --------------------------------------------------
        # National record
        # --------------------------------------------------

        cursor.execute(
            """
            INSERT INTO index_data (
                period_date,
                route_id,
                days_to_departure,
                price_index,
                overall_index,
                laspeyres_index,
                paasche_index,
                fisher_index
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                current_date,
                None,
                window,
                fisher,
                fisher,
                laspeyres,
                paasche,
                fisher
            )
        )


        # --------------------------------------------------
        # Route × booking window records
        # --------------------------------------------------

        for (
            route_id,
            route_name,
            origin,
            destination,
            route_weight
        ) in routes:

            relative = route_window_values.get(
                route_id,
                {}
            ).get(window)

            if relative is None:
                continue

            cursor.execute(
                """
                INSERT INTO index_data (
                    period_date,
                    route_id,
                    days_to_departure,
                    price_index,
                    overall_index,
                    laspeyres_index,
                    paasche_index,
                    fisher_index
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    current_date,
                    route_id,
                    window,
                    relative,
                    relative,
                    None,
                    None,
                    None
                )
            )


conn.commit()
# ==================================================
# LATEST ROUTE INDICES
# ==================================================

print("\n==========================================")
print("LATEST ROUTE INDICES")
print("==========================================")


latest_date = dates[-1]


route_rows = cursor.execute(
    """
    SELECT
        r.route_name,
        i.days_to_departure,
        i.price_index
    FROM index_data i

    JOIN routes r
        ON i.route_id = r.route_id

    WHERE i.period_date = ?

    ORDER BY
        r.route_id,
        i.days_to_departure
    """,
    (latest_date,)
).fetchall()


current_route = None


for (
    route_name,
    window,
    price_index
) in route_rows:

    if current_route != route_name:

        print(
            f"\n{route_name}"
        )

        current_route = route_name


    print(
        f"  {window} days -> "
        f"{price_index:.2f}"
    )


# ==================================================
# FINAL
# ==================================================

conn.close()


print("\n==========================================")
print("Calculation complete.")
print("==========================================")