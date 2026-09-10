# ✈️ SIH26056 — Real-Time Airfare Price Index for India

### Development of a Real-time Airfare Price Index for India through Automated Web Scraping of Airline and Online Travel Aggregator Portals for Augmentation of the Consumer Price Index (CPI)

> **Smart India Hackathon 2026 — Problem Statement SIH26056**

---

# 📌 Overview

Airfare prices in India are highly dynamic.

The price of the same route can change depending on:

- Airline
- Route
- Travel date
- Booking date
- Days remaining before departure
- Fare class
- Fare family
- Availability
- Taxes and fees
- Market conditions

Traditional flight-search platforms primarily answer:

> **"What is the current price of this flight?"**

This project attempts to answer a broader question:

> **"How are domestic airfare prices changing across routes, airlines and booking windows?"**

The system collects and standardizes airfare observations, stores them in a structured database, performs data-quality checks and anomaly detection, calculates route-level and aggregate airfare indices, evaluates fare fairness, and presents the results through a web dashboard.

The current implementation is a **prototype analytical system using controlled/sample airfare data**. The architecture is designed to support authorized airline, OTA, or other permitted airfare data sources in a production deployment.

---

# 🎯 Objectives

The project aims to:

1. Collect standardized airfare observations.
2. Normalize airfare data from different sources.
3. Store observations in a structured database.
4. Handle missing, duplicate and inconsistent observations.
5. Detect unusual airfare movements.
6. Analyze prices across different booking windows.
7. Calculate route-level airfare indices.
8. Calculate an aggregate airfare price index.
9. Compare current fares with typical/reference fares.
10. Generate a Fare Fairness Score.
11. Generate an Airfare Weather indicator.
12. Provide high-frequency airfare intelligence.
13. Explore how an airfare indicator could support future CPI augmentation research.

---

# 💡 Core Idea

Instead of treating an airfare as just:

```text
Flight → Price → Booking
