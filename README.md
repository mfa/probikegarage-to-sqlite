# ProBikeGarage to JSON

A Python tool to download and save ProBikeGarage data to JSON files for analysis and backup purposes.

## Overview

This tool connects to the ProBikeGarage API to download your bike and component data, saving it locally as JSON files. ProBikeGarage is a bike maintenance tracking application that helps cyclists manage their bikes and components.

## Features

- Downloads detailed bike information including usage statistics
- Retrieves retired components data
- Fetches non-installed components inventory
- Saves all data as formatted JSON files for easy analysis
- Built-in error handling for network and API issues

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd probikegarage-to-sqlite
```

## Usage

### Basic Usage

Run the script with the `--update` flag to download data:

```bash
uv run main.py --update
```

### With Token Parameter

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

The tool will download three JSON files to the current directory:
- `bikes.json` - Detailed information about your bikes including usage statistics
- `components-retired.json` - Components that have been retired from service
- `components-notinstalled.json` - Components in your inventory that are not currently installed

## Authentication

The tool uses a bearer token for API authentication. You'll need to obtain your own token from ProBikeGarage:

1. Log into your ProBikeGarage account in a web browser
2. Open developer tools and monitor network requests
3. Find API calls and extract the `Authorization: Bearer` token
4. Use the token either via `--token` parameter or in `.secret.json` file

⚠️ **Security Note**: The bearer token provides access to your ProBikeGarage data. Keep it secure and don't share it. Add `.secret.json` to your `.gitignore` to avoid accidentally committing it.

## Data Structure

### Bikes Data
Contains detailed bike information including:
- Bike ID, name, and user information
- Strava integration details (if connected)
- Usage statistics (rides, distance, moving time, elevation gain)
- Component information and maintenance records

### Components Data
Includes component details such as:
- Component ID, name, and type
- Installation and retirement dates
- Usage tracking and maintenance history
- Brand and model information

## Dependencies

- **click** - Command-line interface framework
- **httpx** - HTTP client for API requests

## Alternative Download Method

A shell script version is also included (`download.sh`) for manual data retrieval using curl commands.

## Contributing

Feel free to submit issues and feature requests. This is a simple tool for personal data backup and analysis.

## License

This project is provided as-is for personal use. Respect ProBikeGarage's terms of service when using their API.
