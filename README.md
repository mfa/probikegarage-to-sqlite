# ProBikeGarage to SQLite

A Python tool to download ProBikeGarage data and convert it to SQLite database for analysis and backup purposes.

This project used Anthropic Claude Sonnet 4 a lot to build this faster.

## Overview

This tool connects to the ProBikeGarage API to download your bike and component data, saving it locally as JSON files. ProBikeGarage is a bike maintenance tracking application that helps cyclists manage their bikes and components.

## Features

- Downloads detailed bike information including usage statistics
- Retrieves retired components data
- Fetches non-installed components inventory
- Saves all data as formatted JSON files for easy analysis
- **Converts JSON data to normalized SQLite database**
- Built-in error handling for network and API issues

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager

## Usage

### Basic Usage

Run the script with the `--update` flag to download data.
You can provide the bearer token directly via command line:

```bash
uv run main.py --update --token "your-bearer-token-here"
```

### Using Secret File

Alternatively, create a `.secret.json` file in the project directory:

```json
{
  "bearer_token": "your-bearer-token-here"
}
```

Then run:

```bash
uv run main.py --update
```

### Convert to SQLite Database

Convert the downloaded JSON files to a SQLite database:

```bash
uv run main.py --to-sqlite pbg.db
```

This creates a normalized SQLite database with the following tables:

#### Database Tables

- **bikes** - Basic bike information (id, name, user_id, default, retired_at, etc.)
- **bike_usage** - Detailed usage statistics for each bike (rides, distance, moving_time, elevation_gain, etc.)
- **bike_strava** - Strava integration data for bikes (strava_id, brand_name, model_name, etc.)
- **components** - Component information (id, name, type, notes, status, bike_id, retired_at)
  - status: `installed`, `retired`, or `not_installed`
  - bike_id: Links to bikes table for installed components (NULL for others)
  - retired_at: Date when component was retired (NULL for installed/not_installed)
- **component_usage** - Usage statistics for each component
  - usage_type: `current` (total usage) or `initial` (usage when component was installed)
  - Allows calculation of component-specific usage by subtracting initial from current

#### Database Views

- **component_summary** - Simplified view joining components with their usage data
  - Fields: name, type, status, bike, retired_at, rides, distance_km, moving_time_hours, elevation_gain
  - Distance converted to kilometers, moving time converted to hours for easier reading
  - Includes retirement dates for lifecycle analysis
  - Clean, focused view for easy component analysis

- **component_lifetime_analysis** - Comprehensive lifetime analysis by component type
  - Inventory counts: total_components, currently_installed, retired_count, inventory_count
  - Retirement metrics: avg/min/max km at retirement, avg hours/rides at retirement
  - Current usage: avg km/hours/rides for currently installed components
  - Timeline: earliest/latest retirement dates, replacement frequency
  - Perfect for maintenance planning and component lifecycle insights


### Explore with Datasette

Launch a web interface to explore your data interactively:

```bash
uv run datasette pbg.db
```

This will start a local web server (typically at http://localhost:8001) where you can:

- Browse all tables and their data
- Run custom SQL queries with syntax highlighting
- Export results as CSV, JSON, or other formats
- Create charts and visualizations
- Filter and sort data interactively

The Datasette interface makes it easy to explore patterns in your bike usage, component lifecycle, and maintenance data without writing SQL.

## Dependencies

- **click** - Command-line interface framework
- **httpx** - HTTP client for API requests
- **sqlite-utils** - SQLite database utilities for data conversion
- **datasette** - Web interface for exploring SQLite databases

## License

This project is provided as-is for personal use. Respect ProBikeGarage's terms of service when using their API.
