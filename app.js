const API = "http://127.0.0.1:8000";

let selectedWindow = 7;

let indexChart = null;
let airlineChart = null;
let windowChart = null;

let latestFlights = [];


// =========================================================
// HELPERS
// =========================================================

function number(value, fallback = 0) {

    const n = Number(value);

    return Number.isFinite(n)
        ? n
        : fallback;
}


function money(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "N/A";
    }

    const n = Number(value);

    if (!Number.isFinite(n)) {
        return "N/A";
    }

    return `₹${Math.round(n).toLocaleString("en-IN")}`;
}


function escapeHTML(value) {

    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function formatDate(dateString) {

    if (!dateString) {
        return "--";
    }

    const date =
        new Date(dateString + "T00:00:00");

    if (Number.isNaN(date.getTime())) {
        return "--";
    }

    return date.toLocaleDateString(
        "en-IN",
        {
            day: "numeric",
            month: "short",
            year: "numeric"
        }
    );
}


// =========================================================
// CURRENT INDEX
// =========================================================

async function loadCurrentIndex() {

    try {

        const response = await fetch(
            `${API}/api/index/current?window=${selectedWindow}`
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        const index = number(
            data.overall_index,
            100
        );

        const change = index - 100;


        // =========================================
        // INDEX VALUE
        // =========================================

        const currentIndex =
            document.getElementById("currentIndex");

        if (currentIndex) {
            currentIndex.textContent =
                index.toFixed(2);
        }


        // =========================================
        // CHANGE
        // =========================================

        const changeElement =
            document.getElementById("indexChange");

        if (changeElement) {

            if (change > 0) {

                changeElement.textContent =
                    `↑ ${change.toFixed(2)}%`;

                changeElement.style.color =
                    "#12a579";

            } else if (change < 0) {

                changeElement.textContent =
                    `↓ ${Math.abs(change).toFixed(2)}%`;

                changeElement.style.color =
                    "#ef5b67";

            } else {

                changeElement.textContent =
                    "↑ 0.00%";

                changeElement.style.color =
                    "#12a579";
            }
        }


        // =========================================
        // MESSAGE
        // =========================================

        const message =
            document.getElementById("indexMessage");

        if (message) {

            if (change > 0) {

                message.textContent =
                    `Overall fares are ${change.toFixed(2)}% higher than the base period.`;

            } else if (change < 0) {

                message.textContent =
                    `Overall fares are ${Math.abs(change).toFixed(2)}% lower than the base period.`;

            } else {

                message.textContent =
                    "Overall fares are at the base-period level.";
            }
        }


        // =========================================
        // BASE PERIOD
        // =========================================

        const baseDate =
            document.getElementById("baseDate");

        if (baseDate) {

            baseDate.textContent =
                formatDate(
                    data.base_period_date
                );
        }


        // =========================================
        // DATA AS OF
        // =========================================

        const dataAsOf =
            document.getElementById("dataAsOf");

        if (dataAsOf) {

            dataAsOf.textContent =
                formatDate(
                    data.period_date
                );
        }


        console.log(
            "Airfare Price Index:",
            data
        );

    } catch (error) {

        console.error(
            "Current index error:",
            error
        );

    }
}
// =========================================================
// STATISTICS
// =========================================================

async function loadStatistics() {
    try {
        const response = await fetch(
            `${API}/api/statistics`
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        console.log(
            "Statistics loaded:",
            data
        );

        // ==============================
        // TOTAL FLIGHTS / OBSERVATIONS
        // ==============================

        const totalFlights =
            document.getElementById(
                "totalFlights"
            );

        if (totalFlights) {
            totalFlights.textContent =
                Number(
                    data.observations || 0
                ).toLocaleString("en-IN");
        }

        // ==============================
        // ROUTES
        // ==============================

        const totalRoutes =
            document.getElementById(
                "totalRoutes"
            );

        if (totalRoutes) {
            totalRoutes.textContent =
                Number(
                    data.routes || 0
                ).toLocaleString("en-IN");
        }

        // ==============================
        // AIRLINES
        // ==============================

        const totalAirlines =
            document.getElementById(
                "totalAirlines"
            );

        if (totalAirlines) {

            const flightResponse =
                await fetch(
                    `${API}/api/flights?limit=1000`
                );

            if (!flightResponse.ok) {
                throw new Error(
                    `Flights API HTTP ${flightResponse.status}`
                );
            }

            const flightData =
                await flightResponse.json();

            const flights =
                Array.isArray(
                    flightData.flights
                )
                    ? flightData.flights
                    : [];

            const airlines =
                new Set(
                    flights
                        .map(
                            flight =>
                                flight.airline
                        )
                        .filter(Boolean)
                );

            totalAirlines.textContent =
                airlines.size;
        }

    } catch (error) {

        console.error(
            "Statistics loading error:",
            error
        );
    }
}
// =========================================================
// INDEX HISTORY
// =========================================================

async function loadIndexChart() {
    try {
        const response = await fetch(
            `${API}/api/index/history?window=${selectedWindow}&limit=365`
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        const rows = Array.isArray(data)
            ? data
            : (data.history || []);

        if (!rows.length) {
            console.warn("No fare trend data returned.");
            return;
        }

        const labels = rows.map(row =>
            row.period_date || row.date || ""
        );

        const values = rows.map(row =>
            number(
                row.fisher_index ??
                row.fisher ??
                row.price_index ??
                row.overall_index,
                100
            )
        );

        const canvas = document.getElementById("indexChart");

        if (!canvas) {
            console.warn("indexChart canvas not found.");
            return;
        }

        if (indexChart) {
            indexChart.destroy();
        }

        indexChart = new Chart(canvas, {
            type: "line",

            data: {
                labels: labels,

                datasets: [
                    {
                        label: "Fisher Index",
                        data: values,

                        borderWidth: 3,
                        tension: 0.35,

                        pointRadius: 3,
                        pointHoverRadius: 6,

                        fill: true,

                        backgroundColor:
                            "rgba(22,119,237,0.08)",

                        borderColor:
                            "#1677ed"
                    },

                    {
                        label: "Base = 100",

                        data: labels.map(() => 100),

                        borderWidth: 1,

                        borderDash: [5, 5],

                        pointRadius: 0,

                        borderColor:
                            "#9b8ff1"
                    }
                ]
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,

                interaction: {
                    intersect: false,
                    mode: "index"
                },

                plugins: {
                    legend: {
                        display: false
                    },

                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${number(
                                    context.parsed.y
                                ).toFixed(2)}`;
                            }
                        }
                    }
                },

                scales: {
                    x: {
                        ticks: {
                            maxTicksLimit: 8
                        },

                        grid: {
                            color:
                                "rgba(120,145,175,0.12)"
                        }
                    },

                    y: {
                        beginAtZero: false,

                        grid: {
                            color:
                                "rgba(120,145,175,0.15)"
                        }
                    }
                }
            }
        });

        console.log(
            `Fare Trend loaded from backend for D-${selectedWindow}`,
            rows
        );

    } catch (error) {
        console.error(
            "Fare Trend error:",
            error
        );
    }
}
// =========================================================
// ROUTE DATA
// =========================================================

async function loadRoutes(window = selectedWindow) {

    selectedWindow = window;

    try {

        const response = await fetch(
            `${API}/api/routes/index?window=${window}`
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        let routes = Array.isArray(data)
            ? data
            : data.route_indices ?? [];

        /*
         * IMPORTANT:
         * The API can return multiple historical index records
         * for the same route.
         *
         * We only want ONE row per route:
         * the latest period_date.
         */
        const latestRoutes = new Map();
        const d45Response = await fetch(
    `${API}/api/routes/index?window=45`
);

const d45Data = await d45Response.json();

const d45Routes = Array.isArray(d45Data)
    ? d45Data
    : d45Data.route_indices ?? [];

const d45Map = new Map();

d45Routes.forEach(route => {
    const key =
        route.route_id ??
        route.route ??
        `${route.origin}-${route.destination}`;

    if (!d45Map.has(key)) {
        d45Map.set(
            key,
            number(route.current_price ?? route.base_price, 0)
        );
    }
});
        routes.forEach(route => {

            const routeKey =
                route.route_id ??
                route.route ??
                `${route.origin}-${route.destination}`;

            const existing =
                latestRoutes.get(routeKey);

            if (
                !existing ||
                String(route.period_date || "") >
                String(existing.period_date || "")
            ) {
                latestRoutes.set(
                    routeKey,
                    route
                );
            }

        });

        routes = Array.from(
            latestRoutes.values()
        );

        /*
         * Sort by route weight if available.
         */
        routes.sort(
            (a, b) =>
                Number(b.weight || 0) -
                Number(a.weight || 0)
        );

        const table =
            document.getElementById(
                "routeTable"
            );

        if (!table) {
            return;
        }

        table.innerHTML = "";

        if (!routes.length) {

            table.innerHTML = `
                <tr>
                    <td
                        colspan="6"
                        class="loading"
                    >
                        No route index data available.
                    </td>
                </tr>
            `;

            return;
        }

        routes.forEach(route => {
                const routeKey =
                route.route_id ??
                route.route ??
                `${route.origin}-${route.destination}`;
            const index =
                number(
                    route.route_index ??
                    route.price_index,
                    100
                );

            const current =
                number(
                    route.current_price,
                    0
                );

 

            /*
             * Percentage difference between
             * current and baseline fare.
             */
            // D-45 is the reference fare
const referenceFare =
    d45Map.get(routeKey) ?? 0;

// Selected booking-window fare
const selectedFare = current;

// Premium compared with D-45
const premium =
    referenceFare > 0
        ? ((selectedFare - referenceFare) / referenceFare) * 100
        : 0;

// Booking-window-aware fairness
const fairness =
    Math.max(
        0,
        Math.min(
            100,
            100 - Math.max(0, premium) * 2
        )
    );

            let fairnessClass = "fair-good";
            let statusClass = "fair";
            let statusText = "Fair";

            if (fairness < 60) {

                fairnessClass =
                    "fair-low";

                statusClass =
                    "overpriced";

                statusText =
                        premium > 0
                            ? "Overpriced"
                             : "Unusually Low";

            } else if (fairness < 80) {

                fairnessClass =
                    "fair-mid";

                statusClass =
                    "high";

                statusText =
                    premium > 0
                        ? "Slightly High"
                        : "Slightly Low";
            }

            const routeName =
                route.route ??
                `${route.origin} → ${route.destination}`;

            const row =
                document.createElement(
                    "tr"
                );

            row.innerHTML = `
                <td>
                    ${escapeHTML(routeName)}
                </td>

                <td>
                    <strong>
                        ${index.toFixed(2)}
                    </strong>
                </td>

                <td>
                    ${money(current)}
                </td>

                <td>
                    ${money(referenceFare)}
                </td>

                <td>
                    <span
                        class="fairness-pill ${fairnessClass}"
                    >
                        ${Math.round(fairness)} / 100
                    </span>
                </td>

                <td>
                    <span
                        class="status ${statusClass}"
                    >
                        ${statusText}
                    </span>
                </td>
            `;

            table.appendChild(row);
        });

        /*
         * Update anomaly section using
         * the same latest route records.
         */
        updateAnomalies();

    } catch (error) {

        console.error(
            "Route error:",
            error
        );

        const table =
            document.getElementById(
                "routeTable"
            );

        if (table) {

            table.innerHTML = `
                <tr>
                    <td
                        colspan="6"
                        class="loading"
                    >
                        Unable to load route data.
                    </td>
                </tr>
            `;
        }
    }
}

// =========================================================
// ANOMALIES
// =========================================================

async function updateAnomalies() {
    const count = document.getElementById("anomalyCount");
    const container = document.getElementById("anomalyList");

    try {
        const response = await fetch(
            `${API}/api/airfare-weather?window=${selectedWindow}`
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // Use the actual Z-score anomaly count
        if (count) {
            count.textContent = data.anomalies_detected ?? 0;
        }

        if (!container) {
            return;
        }

        const anomalies = data.anomalies ?? [];

        if (!anomalies.length) {
            container.innerHTML = `
                <div class="loading">
                    No unusual fares detected for D-${selectedWindow}.
                </div>
            `;
            return;
        }

        container.innerHTML = "";

        anomalies.forEach(anomaly => {
            const item = document.createElement("div");

            item.className = "anomaly-row";

            item.innerHTML = `
                <div class="anomaly-top">
                    <span class="anomaly-route">
                        ⚠ ${escapeHTML(anomaly.route)}
                    </span>

                    <span class="anomaly-fare">
                        ${anomaly.change_percent >= 0 ? "+" : ""}
                        ${anomaly.change_percent.toFixed(2)}%
                    </span>
                </div>

                <div class="anomaly-detail">
                    Current ${money(anomaly.current_price)}
                    vs previous ${money(anomaly.previous_price)}
                    (${anomaly.z_score >= 0 ? "+" : ""}
                    Z-score ${anomaly.z_score.toFixed(2)})
                </div>
            `;

            container.appendChild(item);
        });

    } catch (error) {
        console.error("Anomaly error:", error);

        if (count) {
            count.textContent = "--";
        }

        if (container) {
            container.innerHTML = `
                <div class="loading">
                    Unable to analyze anomalies.
                </div>
            `;
        }
    }
}
// =========================================================
// FLIGHT OBSERVATIONS
// =========================================================

async function loadFlights() {

    try {

        const response =
            await fetch(
                `${API}/api/flights?limit=100`
            );


        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }


        const data =
            await response.json();


        latestFlights =
            data.flights ??
            data.observations ??
            [];


        renderLatestFlights();

        buildAirlineChart();


    } catch (error) {

        console.error(
            "Flight data error:",
            error
        );


        const container =
            document.getElementById(
                "latestFlights"
            );


        if (container) {

            container.innerHTML = `
                <div class="loading">
                    Flight sample unavailable.
                </div>
            `;
        }
    }
}


// =========================================================
// LATEST FLIGHTS
// =========================================================

function renderLatestFlights() {

    const container =
        document.getElementById(
            "latestFlights"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    latestFlights
        .slice(0, 6)
        .forEach(flight => {

            const airline =
                flight.airline ??
                "--";


            const route =
                flight.route ??
                (
                    flight.route_origin &&
                    flight.route_destination
                        ? `${flight.route_origin} → ${flight.route_destination}`
                        : "--"
                );


            const fare =
                flight.total_fare ??
                null;


            const departure =
                flight.departure_time ??
                "--";


            const row =
                document.createElement(
                    "div"
                );


            row.className =
                "flight-row";


            row.innerHTML = `

                <span class="flight-airline">
                    ${escapeHTML(
                        airline
                    )}
                </span>

                <span class="flight-route">
                    ${escapeHTML(
                        route
                    )}
                </span>

                <span class="flight-fare">
                    ${money(fare)}
                </span>

                <span class="flight-time">
                    ${escapeHTML(
                        departure
                    )}
                </span>

            `;


            container.appendChild(row);

        });
}


// =========================================================
// AIRLINE CHART
// =========================================================

function buildAirlineChart() {

    if (!latestFlights.length) {
        return;
    }


    const groups = {};


    latestFlights.forEach(flight => {

        const airline =
            flight.airline ??
            "Unknown";


        const fare =
            Number(
                flight.total_fare
            );


        if (!Number.isFinite(fare) || fare <= 0) {
            return;
        }


        if (!groups[airline]) {

            groups[airline] = {
                total: 0,
                count: 0
            };
        }


        groups[airline].total += fare;

        groups[airline].count++;

    });


    const labels =
        Object.keys(groups);


    const values =
        labels.map(
            airline =>
                groups[airline].count
                    ? groups[airline].total /
                      groups[airline].count
                    : 0
        );


    const canvas =
        document.getElementById(
            "airlineChart"
        );


    if (!canvas) {
        return;
    }


    if (airlineChart) {
        airlineChart.destroy();
    }


    airlineChart =
        new Chart(
            canvas,
            {

                type: "bar",

                data: {

                    labels,

                    datasets: [

                        {
                            label:
                                "Average Fare",

                            data:
                                values,

                            borderRadius: 7,

                            backgroundColor:
                                "#287df0"
                        }
                    ]
                },

                options: {

                    responsive: true,

                    maintainAspectRatio:
                        false,

                    plugins: {

                        legend: {
                            display: false
                        },

                        tooltip: {

                            callbacks: {

                                label:
                                    context =>
                                        money(
                                            context.parsed.y
                                        )
                            }
                        }
                    },

                    scales: {

                        y: {

                            beginAtZero: true,

                            ticks: {

                                callback:
                                    value =>
                                        `₹${Number(value).toLocaleString("en-IN")}`
                            }
                        }
                    }
                }
            }
        );
}


// =========================================================
// BOOKING WINDOW EFFECT
// =========================================================

async function buildWindowChart() {
    try {
        const response = await fetch(
            `${API}/api/index/booking-window-effect`
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        /*
         * Backend returns:
         *
         * {
         *   "windows": [
         *      {
         *          "days_to_departure": 45,
         *          "average_fare": 4955.82,
         *          "observations": 4500,
         *          "change_percent": 0
         *      }
         *   ]
         * }
         */

        const rows = Array.isArray(data.windows)
            ? data.windows
            : [];

        if (!rows.length) {
            console.warn(
                "Booking Window Effect: no data returned."
            );
            return;
        }

        /*
         * Sort:
         * D-45 → D-30 → D-15 → D-7 → D-1
         */

        rows.sort(
            (a, b) =>
                Number(b.days_to_departure) -
                Number(a.days_to_departure)
        );

        const labels = rows.map(
            row => `D-${row.days_to_departure}`
        );

        const fares = rows.map(
            row => number(
                row.average_fare,
                0
            )
        );

        const canvas =
            document.getElementById(
                "windowChart"
            );

        if (!canvas) {
            console.warn(
                "windowChart canvas not found."
            );
            return;
        }

        if (windowChart) {
            windowChart.destroy();
        }

        windowChart = new Chart(
            canvas,
            {
                type: "line",

                data: {
                    labels: labels,

                    datasets: [
                        {
                            label:
                                "Average Fare",

                            data:
                                fares,

                            borderWidth: 3,

                            tension: 0.35,

                            pointRadius: 5,

                            pointHoverRadius: 7,

                            fill: true,

                            backgroundColor:
                                "rgba(22,119,237,0.08)",

                            borderColor:
                                "#1677ed"
                        }
                    ]
                },

                options: {
                    responsive: true,

                    maintainAspectRatio:
                        false,

                    interaction: {
                        intersect: false,
                        mode: "index"
                    },

                    plugins: {
                        legend: {
                            display: false
                        },

                        tooltip: {
                            callbacks: {
                                title:
                                    function(context) {
                                        return context[0]
                                            .label;
                                    },

                                label:
                                    function(context) {
                                        return (
                                            "Average Fare: " +
                                            money(
                                                context.raw
                                            )
                                        );
                                    }
                            }
                        }
                    },

                    scales: {
                        x: {
                            grid: {
                                color:
                                    "rgba(120,145,175,0.12)"
                            }
                        },

                        y: {
                            beginAtZero: false,

                            ticks: {
                                callback:
                                    function(value) {
                                        return (
                                            "₹" +
                                            Number(value)
                                                .toLocaleString(
                                                    "en-IN"
                                                )
                                        );
                                    }
                            },

                            grid: {
                                color:
                                    "rgba(120,145,175,0.12)"
                            }
                        }
                    }
                }
            }
        );

        console.log(
            "Booking Window Effect loaded from backend:",
            rows
        );

    } catch (error) {
        console.error(
            "Booking Window Effect error:",
            error
        );
    }
}
// =========================================================
// WINDOW BUTTONS
// =========================================================

function setupWindowButtons() {

    document
        .querySelectorAll(".window-btn")
        .forEach(button => {

            button.addEventListener(
                "click",
                async function() {

                    // ---------------------------------
                    // UPDATE SELECTED WINDOW
                    // ---------------------------------

                    selectedWindow =
                        Number(
                            this.dataset.window
                        );


                    // ---------------------------------
                    // UPDATE ACTIVE BUTTON
                    // ---------------------------------

                    document
                        .querySelectorAll(
                            ".window-btn"
                        )
                        .forEach(btn => {

                            btn.classList.remove(
                                "active"
                            );

                        });


                    this.classList.add(
                        "active"
                    );


                    // ---------------------------------
                    // REFRESH DATABASE-DRIVEN CARDS
                    // ---------------------------------

                    await Promise.all([

                        loadCurrentIndex(),

                        loadAirfareWeather(),

                        loadRoutes(
                            selectedWindow
                        ),

                        calculateOverallFairness(),

                        loadIndexChart()

                    ]);

                }
            );

        });

}

// =========================================================
// FAIRNESS SCORE
// =========================================================

async function calculateOverallFairness() {

    try {

        const response =
            await fetch(
                `${API}/api/routes/index?window=${selectedWindow}`
            );


        if (!response.ok) {
            return;
        }


        const data =
            await response.json();


        const routes =
            Array.isArray(data)
                ? data
                : data.route_indices ?? [];


        if (!routes.length) {
            return;
        }
const d45Response =
    await fetch(
        `${API}/api/routes/index?window=45`
    );

const d45Data =
    await d45Response.json();

const d45Routes =
    Array.isArray(d45Data)
        ? d45Data
        : d45Data.route_indices ?? [];

const d45Map = new Map();

d45Routes.forEach(route => {

    const key =
        route.route_id ??
        route.route ??
        `${route.origin}-${route.destination}`;

    if (!d45Map.has(key)) {

        d45Map.set(
            key,
            number(
                route.current_price ??
                route.base_price,
                0
            )
        );

    }

});

const scores =
    routes.map(route => {

        const routeKey =
            route.route_id ??
            route.route ??
            `${route.origin}-${route.destination}`;

        const current =
            number(
                route.current_price
            );

        /*
         * D-45 is the reference fare
         */
        const referenceFare =
            d45Map.get(routeKey) ?? 0;

        /*
         * If D-45 data is unavailable,
         * do not penalize the route.
         */
        if (!referenceFare) {
            return 100;
        }

        /*
         * Premium compared with D-45
         */
        const premium =
            (
                (current - referenceFare) /
                referenceFare
            ) * 100;

        /*
         * Booking-window-aware fairness
         *
         * Higher fare than D-45
         * = lower fairness.
         *
         * Cheaper than D-45
         * = no penalty.
         */
        return Math.max(
            0,
            Math.min(
                100,
                100 - Math.max(0, premium) * 2
            )
        );

    });

        const score =
            scores.reduce(
                (a, b) =>
                    a + b,
                0
            ) /
            scores.length;


        const scoreElement =
            document.getElementById(
                "fairnessScore"
            );


        if (scoreElement) {

            scoreElement.textContent =
                Math.round(score);
        }


        let status =
            "Generally Fair";


        if (score < 60) {

            status =
                "Unusual Pricing";

        } else if (score < 80) {

            status =
                "Mixed";
        }


        const statusElement =
            document.getElementById(
                "fairnessStatus"
            );


        if (statusElement) {

            statusElement.textContent =
                status;
        }


        const textElement =
            document.getElementById(
                "fairnessText"
            );


        if (textElement) {

            textElement.textContent =
                score >= 80
                    ? "Average fare is close to the typical observed range."
                    : "Some fares are showing larger-than-usual deviations from the base period.";
        }


    } catch (error) {

        console.error(
            "Fairness error:",
            error
        );
    }
}


// =========================================================
// INDIA AIRFARE WEATHER
// =========================================================

// =========================================================
// INDIA AIRFARE WEATHER
// =========================================================

async function loadAirfareWeather() {

    const icon =
        document.getElementById(
            "airfareWeatherIcon"
        );

    const condition =
        document.getElementById(
            "airfareWeatherCondition"
        );

    const status =
        document.getElementById(
            "airfareWeatherStatus"
        );

    const average =
        document.getElementById(
            "weatherAverageChange"
        );

    const volatility =
        document.getElementById(
            "weatherVolatility"
        );

    const routesAffected =
        document.getElementById(
            "weatherRoutesAffected"
        );

    const anomaliesCount =
        document.getElementById(
            "weatherAnomalies"
        );

    if (!condition) return;

    try {

        const response = await fetch(
            `${API}/api/airfare-weather?window=${selectedWindow}`
        );

        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }

        const data =
            await response.json();

        if (!data.available) {

            if (icon)
                icon.textContent = "⚪";

            condition.textContent =
                data.condition ||
                "Data Unavailable";

            if (status)
                status.textContent =
                    data.condition ||
                    "Unavailable";

            if (average)
                average.textContent = "—";

            if (volatility)
                volatility.textContent = "—";

            if (routesAffected)
                routesAffected.textContent = "—";

            if (anomaliesCount)
                anomaliesCount.textContent = "—";

            return;
        }

        // ---------------------------------------------
        // MARKET CONDITION
        // ---------------------------------------------

        if (icon)
            icon.textContent =
                data.icon || "🟢";

        condition.textContent =
            data.condition;

        if (status)
            status.textContent =
                data.condition;

        // ---------------------------------------------
        // AVERAGE FARE CHANGE
        // ---------------------------------------------

        const avg =
            Number(
                data.average_change
            );

        if (average) {

            average.textContent =
                `${avg >= 0 ? "+" : "−"}${Math.abs(avg).toFixed(1)}%`;

        }

        // ---------------------------------------------
        // VOLATILITY
        // ---------------------------------------------

        if (volatility) {

            volatility.textContent =
                data.volatility_level ||
                "Low";

        }

        // ---------------------------------------------
        // ROUTES AFFECTED
        // ---------------------------------------------

        if (routesAffected) {

            routesAffected.textContent =
                data.routes_affected;

        }

        // ---------------------------------------------
        // ANOMALIES
        // ---------------------------------------------

        if (anomaliesCount) {

            anomaliesCount.textContent =
                data.anomalies_detected;

        }

        console.log(
            `Airfare Weather D-${selectedWindow}:`,
            data
        );

    } catch (error) {

        console.error(
            "Airfare Weather error:",
            error
        );

        if (icon)
            icon.textContent = "⚪";

        condition.textContent =
            "Data Unavailable";

        if (status)
            status.textContent =
                "Unavailable";

        if (average)
            average.textContent = "—";

        if (volatility)
            volatility.textContent = "—";

        if (routesAffected)
            routesAffected.textContent = "—";

        if (anomaliesCount)
            anomaliesCount.textContent = "—";
    }
}// =========================================================
// DASHBOARD
// =========================================================

async function loadDashboard() {

    console.log(
        "Loading Airfare Price Index..."
    );

    await Promise.all([
        loadCurrentIndex(),
        loadStatistics(),
        loadIndexChart(),
        loadRoutes(selectedWindow),
        loadFlights(),
        buildWindowChart(),
        calculateOverallFairness(),
        loadAirfareWeather()
    ]);

}


// =========================================================
// START
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        setupWindowButtons();

        loadDashboard();

    }
);

// =========================================================
// START
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        setupWindowButtons();

        loadDashboard();

    }
);