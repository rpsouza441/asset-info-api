# Asset Information API

## Overview

The **Asset Information API** is a Python-powered service designed to provide insights into stock and asset data, including market prices, asset classifications, and detailed information. Built using Flask and Flasgger, this API features interactive documentation and token-based authentication to ensure secure and accessible financial data.

## Features

- **Retrieve Detailed Stock Information:** Access granular data like prices, volumes, and highs/lows for multiple stock tickers.
- **Fetch Market Prices:** Quickly retrieve current market prices for a given list of tickers.
- **Classify Assets:** Automatically categorize assets as FII, ETF, or UNIT.
- **Detailed Asset Info:** Extended attributes, including business summaries and classifications.
- **Secure Endpoints:** Bearer token-based authentication for restricted access.
- **Interactive Documentation:** Swagger UI for seamless exploration and testing.

---

## API Documentation

The API documentation is hosted via Swagger UI at the `/docs` endpoint. Explore all available endpoints and test requests directly from the interface.

---

## Setup

### Prerequisites
- Python 3.10 or higher
- Redis for caching
- Docker (optional)

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/asset-info-api.git
   cd asset-info-api
