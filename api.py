from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from typing import Optional

# ============================================================
# CONFIG
# ============================================================

DB_NAME = "airfare.db"

app = FastAPI(
    title="India Airfare Price Index API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
def health():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) AS count FROM observations"
        )

        observations = cursor.fetchone()["count"]

        cursor.execute(
            "SELECT COUNT(*) AS count FROM routes"
        )

        routes = cursor.fetchone()["count"]

        return {
            "status": "ok",
            "database": DB_NAME,
            "observations": observations,
            "routes": routes
        }

    finally:
        conn.close()


# ============================================================
# CURRENT INDEX
# ============================================================

# ============================================================
# CURRENT INDEX
# ============================================================

@app.get("/api/index/current")
def current_index(window: Optional[int] = None):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        allowed_windows = [1, 7, 15, 30, 45]

        if window not in allowed_windows:
            window = 7

        # Current national index for selected booking window
        cursor.execute("""
            SELECT
                period_date,
                days_to_departure,
                price_index,
                laspeyres_index,
                paasche_index,
                fisher_index
            FROM index_data
            WHERE days_to_departure = ?
              AND route_id IS NULL
            ORDER BY period_date DESC
            LIMIT 1
        """, (window,))

        current = cursor.fetchone()

        # Base period date
        cursor.execute("""
            SELECT MIN(period_date) AS base_period_date
            FROM index_data
            WHERE days_to_departure = ?
              AND route_id IS NULL
        """, (window,))

        base = cursor.fetchone()

        if not current:
            return {
                "available": False,
                "booking_window_days": window,
                "overall_index": 100.0,
                "change_percent": 0.0,
                "period_date": None,
                "base_period_date": None
            }

        fisher = current["fisher_index"]

        return {
            "available": True,
            "period_date": current["period_date"],
            "days_to_departure": current["days_to_departure"],
            "price_index": current["price_index"],
            "laspeyres_index": current["laspeyres_index"],
            "paasche_index": current["paasche_index"],
            "fisher_index": fisher,
            "overall_index": fisher,

            "change_percent": (
                round(float(fisher) - 100.0, 2)
                if fisher is not None
                else None
            ),

            "base_period_date": (
                base["base_period_date"]
                if base
                else None
            )
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        conn.close()
# ============================================================
# INDEX HISTORY
# ============================================================

@app.get("/api/index/history")
def index_history(
    window: Optional[int] = None,
    limit: int = Query(30, ge=1, le=365)
):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        if window in [1, 7, 15, 30, 45]:

            cursor.execute("""
                SELECT
                    period_date,
                    days_to_departure,
                    price_index,
                    laspeyres_index,
                    paasche_index,
                    fisher_index
                FROM index_data
                WHERE days_to_departure = ?
                AND route_id IS NULL
                ORDER BY period_date ASC
                LIMIT ?
            """, (window, limit))

        else:

            cursor.execute("""
                SELECT
                    period_date,
                    days_to_departure,
                    price_index,
                    laspeyres_index,
                    paasche_index,
                    fisher_index
                FROM index_data
                WHERE route_id IS NULL
                ORDER BY period_date ASC
                LIMIT ?
                LIMIT ?
            """, (limit,))

        rows = cursor.fetchall()

        return [
            {
                "period_date": row["period_date"],
                "days_to_departure": row["days_to_departure"],
                "price_index": row["price_index"],
                "laspeyres_index": row["laspeyres_index"],
                "paasche_index": row["paasche_index"],
                "fisher_index": row["fisher_index"],
                "overall_index": row["fisher_index"]
            }
            for row in rows
        ]

    finally:
        conn.close()# ============================================================
# BOOKING WINDOW EFFECT
# ============================================================

@app.get("/api/index/booking-window-effect")
def booking_window_effect():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                days_to_departure,
                AVG(total_fare) AS average_fare,
                COUNT(*) AS observations
            FROM observations
            WHERE total_fare > 0
            GROUP BY days_to_departure
            ORDER BY days_to_departure DESC
        """)

        rows = cursor.fetchall()

        if not rows:
            return {
                "windows": []
            }

        base_price = rows[0]["average_fare"]

        result = []

        for row in rows:

            average_fare = float(
                row["average_fare"]
            )

            change_percent = (
                (average_fare - base_price)
                / base_price
            ) * 100

            result.append({
                "days_to_departure":
                    row["days_to_departure"],

                "average_fare":
                    round(average_fare, 2),

                "observations":
                    row["observations"],

                "change_percent":
                    round(change_percent, 2)
            })

        return {
            "windows": result
        }

    finally:
        conn.close()


# ============================================================
# BOOKING WINDOW EFFECT BY ROUTE
# ============================================================

@app.get("/api/index/booking-window-effect/route")
def booking_window_effect_route(
    route_id: Optional[int] = None
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        if route_id is not None:

            cursor.execute("""
                SELECT
                    o.route_id,
                    r.route_name,
                    o.days_to_departure,
                    AVG(o.total_fare) AS average_fare,
                    COUNT(*) AS observations
                FROM observations o
                JOIN routes r
                    ON o.route_id = r.route_id
                WHERE
                    o.route_id = ?
                    AND o.total_fare > 0
                GROUP BY
                    o.route_id,
                    r.route_name,
                    o.days_to_departure
                ORDER BY
                    o.days_to_departure DESC
            """, (route_id,))

        else:

            cursor.execute("""
                SELECT
                    o.route_id,
                    r.route_name,
                    o.days_to_departure,
                    AVG(o.total_fare) AS average_fare,
                    COUNT(*) AS observations
                FROM observations o
                JOIN routes r
                    ON o.route_id = r.route_id
                WHERE o.total_fare > 0
                GROUP BY
                    o.route_id,
                    r.route_name,
                    o.days_to_departure
                ORDER BY
                    r.route_name,
                    o.days_to_departure DESC
            """)

        rows = cursor.fetchall()

        return [
            {
                "route_id": row["route_id"],
                "route": row["route_name"],
                "days_to_departure":
                    row["days_to_departure"],
                "average_fare":
                    round(float(row["average_fare"]), 2),
                "observations":
                    row["observations"]
            }
            for row in rows
        ]

    finally:
        conn.close()


# ============================================================
# BOOKING WINDOW WEIGHTS
# ============================================================

@app.get("/api/index/booking-window-weights")
def booking_window_weights():

    return {
        "weights": {
            "1": 0.30,
            "7": 0.25,
            "15": 0.20,
            "30": 0.15,
            "45": 0.10
        }
    }


# ============================================================
# ROUTES
# ============================================================

@app.get("/api/routes")
def routes():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                route_id,
                route_name,
                origin,
                destination,
                weight
            FROM routes
            ORDER BY weight DESC
        """)

        rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        conn.close()


# ============================================================
# ROUTE INDEX
# ============================================================

@app.get("/api/routes/index")
def route_indices(
    window: Optional[int] = None
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        # ----------------------------------------------------
        # Get route index data
        # ----------------------------------------------------

        if window in [1, 7, 15, 30, 45]:

            cursor.execute("""
                SELECT
                    i.period_date,
                    i.route_id,
                    r.route_name,
                    r.origin,
                    r.destination,
                    r.weight,
                    i.days_to_departure,
                    i.price_index
                FROM index_data i
                JOIN routes r
                    ON i.route_id = r.route_id
                WHERE i.days_to_departure = ?
                ORDER BY r.weight DESC
            """, (window,))

        else:

            cursor.execute("""
                SELECT
                    i.period_date,
                    i.route_id,
                    r.route_name,
                    r.origin,
                    r.destination,
                    r.weight,
                    i.days_to_departure,
                    i.price_index
                FROM index_data i
                JOIN routes r
                    ON i.route_id = r.route_id
                ORDER BY
                    r.weight DESC
            """)

        rows = cursor.fetchall()

        result = []

        # ----------------------------------------------------
        # For each route calculate base/current price
        # ----------------------------------------------------

        for row in rows:

            route_id = row["route_id"]
            days = row["days_to_departure"]

            cursor.execute("""
                SELECT
                    MIN(booking_date) AS base_date,
                    MAX(booking_date) AS current_date
                FROM observations
                WHERE
                    route_id = ?
                    AND days_to_departure = ?
                    AND total_fare > 0
            """, (route_id, days))

            dates = cursor.fetchone()

            base_price = None
            current_price = None

            if dates:

                base_date = dates["base_date"]
                current_date = dates["current_date"]

                if base_date:

                    cursor.execute("""
                        SELECT AVG(total_fare)
                        FROM observations
                        WHERE
                            route_id = ?
                            AND days_to_departure = ?
                            AND booking_date = ?
                            AND total_fare > 0
                    """, (
                        route_id,
                        days,
                        base_date
                    ))

                    value = cursor.fetchone()[0]

                    if value is not None:
                        base_price = float(value)

                if current_date:

                    cursor.execute("""
                        SELECT AVG(total_fare)
                        FROM observations
                        WHERE
                            route_id = ?
                            AND days_to_departure = ?
                            AND booking_date = ?
                            AND total_fare > 0
                    """, (
                        route_id,
                        days,
                        current_date
                    ))

                    value = cursor.fetchone()[0]

                    if value is not None:
                        current_price = float(value)

            result.append({

                "period_date":
                    row["period_date"],

                "route_id":
                    route_id,

                "route":
                    row["route_name"],

                "origin":
                    row["origin"],

                "destination":
                    row["destination"],

                "weight":
                    row["weight"],

                "days_to_departure":
                    days,

                "route_index":
                    row["price_index"],

                "price_index":
                    row["price_index"],

                "current_price":
                    round(current_price, 2)
                    if current_price is not None
                    else None,

                "base_price":
                    round(base_price, 2)
                    if base_price is not None
                    else None
            })

        return result

    finally:
        conn.close()


# ============================================================
# OBSERVATIONS
# ============================================================

@app.get("/api/observations")
def observations(
    limit: int = Query(100, ge=1, le=1000),
    window: Optional[int] = None
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        if window in [1, 7, 15, 30, 45]:

            cursor.execute("""
                SELECT
                    o.*,
                    s.source_name
                FROM observations o
                LEFT JOIN sources s
                    ON o.source_id = s.source_id
                WHERE o.days_to_departure = ?
                ORDER BY o.collected_at DESC
                LIMIT ?
            """, (window, limit))

        else:

            cursor.execute("""
                SELECT
                    o.*,
                    s.source_name
                FROM observations o
                LEFT JOIN sources s
                    ON o.source_id = s.source_id
                ORDER BY o.collected_at DESC
                LIMIT ?
            """, (limit,))

        rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        conn.close()


# ============================================================
# LATEST OBSERVATIONS
# ============================================================

@app.get("/api/observations/latest")
def latest_observations(
    limit: int = Query(20, ge=1, le=200)
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                o.*,
                s.source_name
            FROM observations o
            LEFT JOIN sources s
                ON o.source_id = s.source_id
            ORDER BY
                o.collected_at DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        conn.close()


# ============================================================
# FLIGHTS
# ============================================================

@app.get("/api/flights")
def flights(
    limit: int = Query(100, ge=1, le=1000)
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                o.observation_id,
                o.route_id,
                o.route_origin,
                o.route_destination,
                o.airline,
                o.airline_code,
                o.flight_number,
                o.travel_date,
                o.booking_date,
                o.days_to_departure,
                o.fare_class,
                o.base_fare,
                o.taxes,
                o.total_fare,
                o.currency,
                o.departure_time,
                o.arrival_time,
                o.duration_minutes,
                o.stops,
                o.aircraft_type,
                o.baggage_allowance,
                o.fare_family,
                o.booking_url,
                o.collected_at,
                s.source_name
            FROM observations o
            LEFT JOIN sources s
                ON o.source_id = s.source_id
            ORDER BY
                o.collected_at DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()

        return {
            "flights": [
                dict(row)
                for row in rows
            ]
        }

    finally:
        conn.close()


# ============================================================
# ANOMALIES
# ============================================================

@app.get("/api/anomalies")
def get_anomalies(
    window: int = 7,
    limit: int = 3
):

    allowed_windows = [
        1,
        7,
        15,
        30,
        45
    ]

    if window not in allowed_windows:
        window = 7

    if limit < 1:
        limit = 3

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            WITH dates AS (

                SELECT
                    MIN(booking_date) AS base_date,
                    MAX(booking_date) AS current_date

                FROM observations

                WHERE
                    days_to_departure = ?
                    AND total_fare > 0
            ),

            route_prices AS (

                SELECT

                    r.route_id,
                    r.route_name,

                    AVG(
                        CASE
                            WHEN o.booking_date =
                                 d.base_date
                            THEN o.total_fare
                        END
                    ) AS base_price,

                    AVG(
                        CASE
                            WHEN o.booking_date =
                                 d.current_date
                            THEN o.total_fare
                        END
                    ) AS current_price

                FROM observations o

                JOIN routes r
                    ON o.route_id = r.route_id

                CROSS JOIN dates d

                WHERE
                    o.days_to_departure = ?
                    AND o.total_fare > 0

                GROUP BY
                    r.route_id,
                    r.route_name
            )

            SELECT

                route_id,
                route_name,
                base_price,
                current_price,

                (
                    (
                        current_price -
                        base_price
                    )
                    /
                    base_price
                ) * 100 AS change_percent

            FROM route_prices

            WHERE
                base_price > 0
                AND current_price > 0

            ORDER BY
                ABS(change_percent) DESC

            LIMIT ?
        """, (
            window,
            window,
            limit
        ))

        rows = cursor.fetchall()

        anomalies = []

        for row in rows:

            base_price = float(row["base_price"])

            current_price = float(row["current_price"])

            change_percent = (
                (
                    current_price -
                    base_price
                )
                /
                base_price
            ) * 100

            anomalies.append({

                "route":
                    row["route_name"],

                "base_price":
                    round(
                        base_price,
                        2
                    ),

                "current_price":
                    round(
                        current_price,
                        2
                    ),

                "change_percent":
                    round(
                        change_percent,
                        2
                    ),

                "difference":
                    round(
                        current_price -
                        base_price,
                        2
                    ),

                "booking_window_days":
                    window
            })

        return {

            "window":
                window,

            "anomalies":
                anomalies
        }

    finally:

        conn.close()




# ============================================================
# INDIA AIRFARE WEATHER
# ============================================================

@app.get("/api/airfare-weather")
def airfare_weather(window: int = 7):

    allowed_windows = [1, 7, 15, 30, 45]

    if window not in allowed_windows:
        window = 7

    conn = get_connection()

    try:
        cursor = conn.cursor()

        # ----------------------------------------------------
        # Get all booking dates for selected booking window
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                booking_date,
                route_id,
                route_origin,
                route_destination,
                total_fare
            FROM observations
            WHERE days_to_departure = ?
              AND total_fare > 0
            ORDER BY booking_date ASC
        """, (window,))

        rows = cursor.fetchall()

        if not rows:
            return {
                "available": False,
                "window": window,
                "condition": "Data Unavailable",
                "icon": "⚪",
                "average_change": 0,
                "volatility": 0,
                "volatility_level": "Low",
                "routes_affected": 0,
                "anomalies_detected": 0,
                "routes_analyzed": 0,
                "anomalies": []
            }

        # ----------------------------------------------------
        # Build:
        #
        # booking_date
        #       ↓
        # route
        #       ↓
        # average fare
        # ----------------------------------------------------

        daily_routes = {}

        for row in rows:

            booking_date = row["booking_date"]

            route_id = row["route_id"]

            route_name = (
                f'{row["route_origin"]}-'
                f'{row["route_destination"]}'
            )

            fare = float(row["total_fare"])

            if booking_date not in daily_routes:
                daily_routes[booking_date] = {}

            if route_id not in daily_routes[booking_date]:
                daily_routes[booking_date][route_id] = {
                    "route": route_name,
                    "fares": []
                }

            daily_routes[booking_date][route_id]["fares"].append(fare)

        # ----------------------------------------------------
        # Convert fares to daily route averages
        # ----------------------------------------------------

        for booking_date in daily_routes:

            for route_id in daily_routes[booking_date]:

                fares = daily_routes[
                    booking_date
                ][route_id]["fares"]

                daily_routes[
                    booking_date
                ][route_id]["average_fare"] = (
                    sum(fares) / len(fares)
                )

        dates = sorted(daily_routes.keys())

        if len(dates) < 2:

            return {
                "available": False,
                "window": window,
                "condition": "Insufficient Data",
                "icon": "⚪",
                "average_change": 0,
                "volatility": 0,
                "volatility_level": "Low",
                "routes_affected": 0,
                "anomalies_detected": 0,
                "routes_analyzed": 0,
                "anomalies": []
            }

        # ----------------------------------------------------
        # CURRENT VS PREVIOUS PERIOD
        # ----------------------------------------------------

        current_date = dates[-1]
        previous_date = dates[-2]

        current_routes = daily_routes[current_date]
        previous_routes = daily_routes[previous_date]

        current_changes = []

        route_changes = []

        for route_id, current_data in current_routes.items():

            if route_id not in previous_routes:
                continue

            current_fare = current_data["average_fare"]

            previous_fare = (
                previous_routes[
                    route_id
                ]["average_fare"]
            )

            if previous_fare <= 0:
                continue

            change = (
                (current_fare - previous_fare)
                / previous_fare
            ) * 100

            current_changes.append(change)

            route_changes.append({
                "route_id": route_id,
                "route": current_data["route"],
                "current_price": round(
                    current_fare, 2
                ),
                "previous_price": round(
                    previous_fare, 2
                ),
                "change_percent": round(
                    change, 4
                )
            })

        # ----------------------------------------------------
        # 1. AVERAGE FARE CHANGE
        # ----------------------------------------------------

        if current_changes:

            average_change = (
                sum(current_changes)
                / len(current_changes)
            )

        else:

            average_change = 0.0

        # ----------------------------------------------------
        # 2. ROLLING VOLATILITY
        #
        # Use up to the selected number of previous
        # periods. If database has fewer dates,
        # use all available dates.
        # ----------------------------------------------------

        lookback = min(window, len(dates) - 1)

        rolling_dates = dates[
            -(lookback + 1):
        ]

        rolling_changes = []

        for i in range(1, len(rolling_dates)):

            previous_day = rolling_dates[i - 1]
            current_day = rolling_dates[i]

            previous_routes_day = (
                daily_routes[previous_day]
            )

            current_routes_day = (
                daily_routes[current_day]
            )

            for route_id, current_data in current_routes_day.items():

                if route_id not in previous_routes_day:
                    continue

                current_fare = (
                    current_data["average_fare"]
                )

                previous_fare = (
                    previous_routes_day[
                        route_id
                    ]["average_fare"]
                )

                if previous_fare <= 0:
                    continue

                daily_change = (
                    (
                        current_fare
                        - previous_fare
                    )
                    / previous_fare
                ) * 100

                rolling_changes.append(
                    daily_change
                )

        # ----------------------------------------------------
        # STANDARD DEVIATION
        # ----------------------------------------------------

        if rolling_changes:

            rolling_mean = (
                sum(rolling_changes)
                / len(rolling_changes)
            )

            variance = (
                sum(
                    (
                        value
                        - rolling_mean
                    ) ** 2
                    for value in rolling_changes
                )
                / len(rolling_changes)
            )

            volatility = variance ** 0.5

        else:

            volatility = 0.0

        # ----------------------------------------------------
        # VOLATILITY CATEGORY
        # ----------------------------------------------------

        if volatility >= 5:

            volatility_level = "High"

        elif volatility >= 2:

            volatility_level = "Medium"

        else:

            volatility_level = "Low"

        # ----------------------------------------------------
        # 3. ROUTES AFFECTED
        # ----------------------------------------------------

        routes_affected = sum(
            1
            for value in current_changes
            if abs(value) > 1
        )

        # ----------------------------------------------------
        # 4. Z-SCORE ANOMALIES
        # ----------------------------------------------------

        anomalies = []

        if len(current_changes) >= 2:

            mean_change = (
                sum(current_changes)
                / len(current_changes)
            )

            variance = (
                sum(
                    (
                        value
                        - mean_change
                    ) ** 2
                    for value in current_changes
                )
                / len(current_changes)
            )

            std_dev = variance ** 0.5

            if std_dev > 0:

                for route in route_changes:

                    change = (
                        route["change_percent"]
                    )

                    z_score = (
                        change - mean_change
                    ) / std_dev

                    if abs(z_score) > 2:

                        anomalies.append({
                            "route": route["route"],
                            "current_price":
                                route["current_price"],
                            "previous_price":
                                route["previous_price"],
                            "change_percent":
                                round(change, 2),
                            "z_score":
                                round(z_score, 2),
                            "difference":
                                round(
                                    route["current_price"]
                                    - route["previous_price"],
                                    2
                                )
                        })

        # ----------------------------------------------------
        # Sort anomalies by strongest deviation
        # ----------------------------------------------------

        anomalies.sort(
            key=lambda x: abs(x["z_score"]),
            reverse=True
        )

        # ----------------------------------------------------
        # 5. MARKET CONDITION
        # ----------------------------------------------------

        if (
            abs(average_change) >= 5
            or volatility >= 5
        ):

            condition = "Airfare Shock"
            icon = "🔴"

        elif volatility >= 2:

            condition = "High Volatility"
            icon = "🟠"

        elif average_change >= 1:

            condition = "Prices Rising"
            icon = "🟡"

        elif average_change <= -1:

            condition = "Prices Falling"
            icon = "🔵"

        else:

            condition = "Stable Market"
            icon = "🟢"

        # ----------------------------------------------------
        # RETURN
        # ----------------------------------------------------

        return {

            "available": True,

            "window": window,

            "current_date": current_date,

            "previous_date": previous_date,

            "condition": condition,

            "icon": icon,

            "average_change": round(
                average_change,
                2
            ),

            "volatility": round(
                volatility,
                2
            ),

            "volatility_level":
                volatility_level,

            "routes_affected":
                routes_affected,

            "anomalies_detected":
                len(anomalies),

            "routes_analyzed":
                len(current_changes),

            "anomalies":
                anomalies[:10],

            "route_changes":
                route_changes

        }

    finally:

        conn.close()
# ============================================================
# AIRFARE WEATHER
# ============================================================

@app.get("/api/weather")
def airfare_weather(window: int = 7):
    allowed_windows = [1, 7, 15, 30, 45]
    if window not in allowed_windows:
        window = 7

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            WITH dates AS (
                SELECT
                    MIN(booking_date) AS base_date,
                    MAX(booking_date) AS current_date
                FROM observations
                WHERE days_to_departure = ?
                  AND total_fare > 0
            ),
            route_prices AS (
                SELECT
                    r.route_id,
                    r.route_name,
                    AVG(CASE WHEN o.booking_date = d.base_date THEN o.total_fare END) AS base_price,
                    AVG(CASE WHEN o.booking_date = d.current_date THEN o.total_fare END) AS current_price
                FROM observations o
                JOIN routes r ON o.route_id = r.route_id
                CROSS JOIN dates d
                WHERE o.days_to_departure = ?
                  AND o.total_fare > 0
                GROUP BY r.route_id, r.route_name
            )
            SELECT
                route_id,
                route_name,
                base_price,
                current_price,
                ((current_price - base_price) / base_price) * 100 AS change_percent
            FROM route_prices
            WHERE base_price > 0 AND current_price > 0
            ORDER BY ABS(change_percent) DESC
        """, (window, window))

        rows = cursor.fetchall()
        anomalies = []
        for row in rows:
            base_price = float(row["base_price"])
            current_price = float(row["current_price"])
            change_percent = float(row["change_percent"])
            anomalies.append({
                "route": row["route_name"],
                "base_price": round(base_price, 2),
                "current_price": round(current_price, 2),
                "change_percent": round(change_percent, 2),
                "difference": round(current_price - base_price, 2),
                "booking_window_days": window
            })

        changes = [x["change_percent"] for x in anomalies]
        average_change = sum(changes) / len(changes) if changes else 0.0
        variance = (sum((x - average_change) ** 2 for x in changes) / len(changes)) if changes else 0.0
        volatility = variance ** 0.5
        affected = sum(1 for x in changes if abs(x) >= 1)
        detected = sum(1 for x in changes if abs(x) >= 1.5)

        if abs(average_change) >= 5 or volatility >= 6:
            condition, icon = "Airfare Shock", "🔴"
        elif volatility >= 3:
            condition, icon = "High Volatility", "🟠"
        elif average_change >= 1:
            condition, icon = "Prices Rising", "🟡"
        elif average_change <= -1:
            condition, icon = "Prices Falling", "🔵"
        else:
            condition, icon = "Stable Market", "🟢"

        if volatility >= 6:
            volatility_label = "Extreme"
        elif volatility >= 3:
            volatility_label = "High"
        elif volatility >= 1.5:
            volatility_label = "Medium"
        else:
            volatility_label = "Low"

        return {
            "window": window,
            "condition": condition,
            "icon": icon,
            "average_change": round(average_change, 2),
            "volatility": round(volatility, 2),
            "volatility_label": volatility_label,
            "routes_affected": affected,
            "anomalies_count": detected,
            "anomalies": anomalies
        }
    finally:
        conn.close()


# ============================================================
# STATISTICS
# ============================================================

@app.get("/api/statistics")
def statistics():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM observations
        """)

        observations = cursor.fetchone()["count"]

        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM routes
        """)

        routes = cursor.fetchone()["count"]

        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM sources
        """)

        sources = cursor.fetchone()["count"]

        cursor.execute("""
            SELECT
                MIN(total_fare) AS min_fare,
                MAX(total_fare) AS max_fare,
                AVG(total_fare) AS avg_fare
            FROM observations
            WHERE total_fare > 0
        """)

        fare_stats = cursor.fetchone()

        return {

            "observations":
                observations,

            "routes":
                routes,

            "sources":
                sources,

            "fare": {

                "minimum":
                    round(
                        float(
                            fare_stats["min_fare"]
                        ),
                        2
                    )
                    if fare_stats["min_fare"]
                    is not None
                    else None,

                "maximum":
                    round(
                        float(
                            fare_stats["max_fare"]
                        ),
                        2
                    )
                    if fare_stats["max_fare"]
                    is not None
                    else None,

                "average":
                    round(
                        float(
                            fare_stats["avg_fare"]
                        ),
                        2
                    )
                    if fare_stats["avg_fare"]
                    is not None
                    else None
            }
        }

    finally:
        conn.close()


# ============================================================
# COVERAGE
# ============================================================

@app.get("/api/coverage")
def coverage():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                days_to_departure,
                COUNT(*) AS observations,
                COUNT(
                    DISTINCT route_id
                ) AS routes
            FROM observations
            GROUP BY
                days_to_departure
            ORDER BY
                days_to_departure
        """)

        rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        conn.close()


# ============================================================
# DATA MODEL
# ============================================================

@app.get("/api/data-model")
def data_model():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        tables = [
            "routes",
            "sources",
            "observations",
            "index_data"
        ]

        result = {}

        for table in tables:

            cursor.execute(
                f"PRAGMA table_info({table})"
            )

            rows = cursor.fetchall()

            result[table] = [
                {
                    "name": row["name"],
                    "type": row["type"],
                    "notnull": row["notnull"],
                    "primary_key": row["pk"]
                }
                for row in rows
            ]

        return result

    finally:
        conn.close()


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000
    )