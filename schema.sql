PRAGMA foreign_keys = ON;

-- ==================================================
-- DROP TABLES
-- ==================================================

DROP TABLE IF EXISTS index_data;
DROP TABLE IF EXISTS collection_runs;
DROP TABLE IF EXISTS observations;
DROP TABLE IF EXISTS routes;
DROP TABLE IF EXISTS sources;


-- ==================================================
-- SOURCES
-- ==================================================

CREATE TABLE sources (

    source_id INTEGER PRIMARY KEY AUTOINCREMENT,

    source_name TEXT NOT NULL UNIQUE,

    source_type TEXT NOT NULL,

    website TEXT,

    active INTEGER NOT NULL DEFAULT 1,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP

);


-- ==================================================
-- ROUTES
-- ==================================================

CREATE TABLE routes (

    route_id INTEGER PRIMARY KEY AUTOINCREMENT,

    route_name TEXT NOT NULL UNIQUE,

    origin TEXT NOT NULL,

    destination TEXT NOT NULL,

    weight REAL NOT NULL,

    is_active INTEGER NOT NULL DEFAULT 1

);


-- ==================================================
-- OBSERVATIONS
-- ==================================================

CREATE TABLE observations (

    observation_id INTEGER PRIMARY KEY AUTOINCREMENT,

    route_id INTEGER NOT NULL,

    source_id INTEGER NOT NULL,

    route_origin TEXT NOT NULL,

    route_destination TEXT NOT NULL,

    airline TEXT NOT NULL,

    airline_code TEXT,

    flight_number TEXT,

    travel_date TEXT NOT NULL,

    booking_date TEXT NOT NULL,

    days_to_departure INTEGER NOT NULL,

    fare_class TEXT NOT NULL,

    base_fare REAL,

    taxes REAL,

    total_fare REAL NOT NULL,

    currency TEXT NOT NULL DEFAULT 'INR',

    departure_time TEXT,

    arrival_time TEXT,

    duration_minutes INTEGER,

    stops INTEGER NOT NULL DEFAULT 0,

    aircraft_type TEXT,

    baggage_allowance TEXT,

    fare_family TEXT,

    booking_url TEXT,

    collected_at TEXT NOT NULL,

    FOREIGN KEY(route_id)
        REFERENCES routes(route_id),

    FOREIGN KEY(source_id)
        REFERENCES sources(source_id)

);


-- ==================================================
-- COLLECTION RUNS
-- ==================================================

CREATE TABLE collection_runs (

    run_id INTEGER PRIMARY KEY AUTOINCREMENT,

    source_id INTEGER NOT NULL,

    started_at TEXT NOT NULL,

    completed_at TEXT,

    status TEXT NOT NULL,

    routes_requested INTEGER NOT NULL DEFAULT 0,

    searches_completed INTEGER NOT NULL DEFAULT 0,

    observations_inserted INTEGER NOT NULL DEFAULT 0,

    observations_failed INTEGER NOT NULL DEFAULT 0,

    error_message TEXT,

    FOREIGN KEY(source_id)
        REFERENCES sources(source_id)

);


-- ==================================================
-- INDEX DATA
-- ==================================================

CREATE TABLE index_data (

    index_id INTEGER PRIMARY KEY AUTOINCREMENT,

    period_date TEXT NOT NULL,

    route_id INTEGER,

    days_to_departure INTEGER,

    price_index REAL,

    overall_index REAL,

    laspeyres_index REAL,

    paasche_index REAL,

    fisher_index REAL,

    FOREIGN KEY(route_id)
        REFERENCES routes(route_id)

);


-- ==================================================
-- OBSERVATION INDEXES
-- ==================================================

CREATE INDEX idx_observations_booking_date
ON observations(booking_date);

CREATE INDEX idx_observations_travel_date
ON observations(travel_date);

CREATE INDEX idx_observations_days
ON observations(days_to_departure);

CREATE INDEX idx_observations_route
ON observations(route_id);

CREATE INDEX idx_observations_source
ON observations(source_id);

CREATE INDEX idx_observations_airline
ON observations(airline_code);

CREATE INDEX idx_observations_collected
ON observations(collected_at);


-- ==================================================
-- DUPLICATE PROTECTION
-- ==================================================

CREATE UNIQUE INDEX idx_unique_observation
ON observations (
    source_id,
    route_id,
    airline_code,
    flight_number,
    travel_date,
    booking_date,
    fare_class,
    departure_time
);


-- ==================================================
-- COLLECTION RUN INDEXES
-- ==================================================

CREATE INDEX idx_collection_runs_source
ON collection_runs(source_id);

CREATE INDEX idx_collection_runs_started
ON collection_runs(started_at);


-- ==================================================
-- INDEX DATA INDEXES
-- ==================================================

CREATE INDEX idx_index_data_date
ON index_data(period_date);

CREATE INDEX idx_index_data_window
ON index_data(days_to_departure);

CREATE INDEX idx_index_data_route
ON index_data(route_id);