import json
from pathlib import Path

import typer
import httpx
import sqlite_utils


def convert_to_sqlite(db_path="pbg.db"):
    """Convert JSON files to SQLite database with normalized tables."""
    db = sqlite_utils.Database(db_path)

    # Load JSON files
    json_files = {
        "bikes": "data/bikes.json",
        "components_retired": "data/components-retired.json",
        "components_notinstalled": "data/components-notinstalled.json",
        "components_installed": "data/components-installed.json",
    }

    data = {}
    for key, filename in json_files.items():
        if Path(filename).exists():
            with open(filename, "r", encoding="utf-8") as f:
                data[key] = json.load(f)
                print(f"Loaded {len(data[key])} records from {filename}")
        else:
            print(f"Warning: {filename} not found, skipping")
            data[key] = []

    # Create bikes table
    bikes_records = []
    usage_records = []
    strava_records = []

    for bike in data.get("bikes", []):
        # Main bike record
        bike_record = {
            "id": bike["id"],
            "name": bike["name"],
            "user_id": bike["user_id"],
            "default": bike.get("default", False),
            "picture_attachment_id": bike.get("picture_attachment_id"),
            "picture_url": bike.get("picture_url"),
            "retired_at": bike.get("retired_at"),
        }
        bikes_records.append(bike_record)

        # Usage data
        if "usage" in bike and bike["usage"]:
            usage_record = {"bike_id": bike["id"]}
            usage_record.update(bike["usage"])
            usage_records.append(usage_record)

        # Strava data
        if "strava_bike" in bike and bike["strava_bike"]:
            strava_record = {"bike_id": bike["id"]}
            strava_record.update(bike["strava_bike"])
            strava_records.append(strava_record)

    # Create components table
    components_records = []
    component_usage_records = []

    # Add installed components from bikes
    for bike in data.get("bikes", []):
        if "components" in bike:
            for component in bike["components"]:
                # Main component record (installed)
                component_record = {
                    "id": component["id"],
                    "name": component["name"],
                    "type": component["type"],
                    "notes": component.get("notes", ""),
                    "user_id": component["user_id"],
                    "status": "installed",
                    "bike_id": bike["id"],  # Track which bike it's installed on
                    "parent_component_id": None,  # Component installed directly on bike
                    "retired_at": (
                        component.get("retired_at")
                        if component.get("retired_at") != "0001-01-01T00:00:00Z"
                        else None
                    ),
                }
                components_records.append(component_record)

                # Component usage data - current usage
                if "usage" in component and component["usage"]:
                    usage_record = {
                        "component_id": component["id"],
                        "usage_type": "current",
                    }
                    usage_record.update(component["usage"])
                    component_usage_records.append(usage_record)

                # Component usage data - initial usage (baseline when component was installed)
                if "initial_usage" in component and component["initial_usage"]:
                    initial_usage_record = {
                        "component_id": component["id"],
                        "usage_type": "initial",
                    }
                    initial_usage_record.update(component["initial_usage"])
                    component_usage_records.append(initial_usage_record)

    # Add components from the separate installed components file
    for component in data.get("components_installed", []):
        # Determine parent-child relationships from current_installations
        parent_component_id = None
        bike_id = component.get("bike_id") if component.get("bike_id") else None
        
        # Check if this component is installed on another component
        if "current_installations" in component and component["current_installations"]:
            for installation in component["current_installations"]:
                if installation.get("target_type") == "component":
                    parent_component_id = installation.get("target_id")
                    # If installed on a component, use that component's bike_id (if available)
                    if not bike_id and installation.get("bike_id"):
                        bike_id = installation.get("bike_id")
                elif installation.get("target_type") == "bike":
                    bike_id = installation.get("target_id")
                    parent_component_id = None
        
        # Main component record (installed)
        component_record = {
            "id": component["id"],
            "name": component["name"],
            "type": component["type"],
            "notes": component.get("notes", ""),
            "user_id": component["user_id"],
            "status": "installed",
            "bike_id": bike_id,
            "parent_component_id": parent_component_id,
            "retired_at": (
                component.get("retired_at")
                if component.get("retired_at") != "0001-01-01T00:00:00Z"
                else None
            ),
        }
        components_records.append(component_record)

        # Component usage data - current usage
        if "usage" in component and component["usage"]:
            usage_record = {
                "component_id": component["id"],
                "usage_type": "current",
            }
            usage_record.update(component["usage"])
            component_usage_records.append(usage_record)

        # Component usage data - initial usage (baseline when component was installed)
        if "initial_usage" in component and component["initial_usage"]:
            initial_usage_record = {
                "component_id": component["id"],
                "usage_type": "initial",
            }
            initial_usage_record.update(component["initial_usage"])
            component_usage_records.append(initial_usage_record)

    # Add retired and not-installed components
    all_components = data.get("components_retired", []) + data.get(
        "components_notinstalled", []
    )

    for component in all_components:
        # Main component record
        component_record = {
            "id": component["id"],
            "name": component["name"],
            "type": component["type"],
            "notes": component.get("notes", ""),
            "user_id": component["user_id"],
            "status": (
                "retired"
                if component in data.get("components_retired", [])
                else "not_installed"
            ),
            "bike_id": None,  # Not currently installed on any bike
            "parent_component_id": None,  # Not currently installed on any component
            "retired_at": (
                component.get("retired_at")
                if component.get("retired_at") != "0001-01-01T00:00:00Z"
                else None
            ),
        }
        components_records.append(component_record)

        # Component usage data - current usage
        if "usage" in component and component["usage"]:
            usage_record = {"component_id": component["id"], "usage_type": "current"}
            usage_record.update(component["usage"])
            component_usage_records.append(usage_record)

        # Component usage data - initial usage (baseline when component was installed)
        if "initial_usage" in component and component["initial_usage"]:
            initial_usage_record = {
                "component_id": component["id"],
                "usage_type": "initial",
            }
            initial_usage_record.update(component["initial_usage"])
            component_usage_records.append(initial_usage_record)

    # Drop existing tables to handle schema changes
    tables_to_recreate = [
        "bikes",
        "bike_usage",
        "bike_strava",
        "components",
        "component_usage",
    ]
    for table_name in tables_to_recreate:
        if table_name in db.table_names():
            db[table_name].drop()

    # Insert data into database
    if bikes_records:
        db["bikes"].insert_all(bikes_records)
        print(f"Inserted {len(bikes_records)} bikes")

    if usage_records:
        db["bike_usage"].insert_all(usage_records)
        print(f"Inserted {len(usage_records)} bike usage records")

    if strava_records:
        db["bike_strava"].insert_all(strava_records)
        print(f"Inserted {len(strava_records)} Strava bike records")

    if components_records:
        db["components"].insert_all(components_records)
        print(f"Inserted {len(components_records)} components")

    if component_usage_records:
        db["component_usage"].insert_all(component_usage_records)
        print(f"Inserted {len(component_usage_records)} component usage records")

    # Create indexes for better performance
    try:
        db["bikes"].create_index(["user_id"], if_not_exists=True)
        db["components"].create_index(["user_id"], if_not_exists=True)
        db["components"].create_index(["type"], if_not_exists=True)
        db["components"].create_index(["bike_id"], if_not_exists=True)
        db["components"].create_index(["parent_component_id"], if_not_exists=True)
        db["bike_usage"].create_index(["bike_id"], if_not_exists=True)
        db["component_usage"].create_index(["component_id"], if_not_exists=True)
        print("Created database indexes")
    except Exception as e:
        print(f"Note: Could not create some indexes: {e}")

    # Create views for easier querying
    try:
        # Drop view if it exists
        db.execute("DROP VIEW IF EXISTS component_summary")

        # Create component summary view
        component_summary_sql = """
        CREATE VIEW component_summary AS
        SELECT
            c.name,
            c.type,
            c.status,
            b.name as bike,
            c.retired_at,
            cu_current.rides,
            ROUND(cu_current.distance / 1000.0, 2) as distance_km,
            ROUND(cu_current.moving_time / 3600.0, 2) as moving_time_hours,
            cu_current.elevation_gain
        FROM components c
        LEFT JOIN bikes b ON c.bike_id = b.id
        LEFT JOIN component_usage cu_current ON c.id = cu_current.component_id AND cu_current.usage_type = 'current'
        """

        db.execute(component_summary_sql)
        print("Created component_summary view")

        # Create component lifetime analysis view
        db.execute("DROP VIEW IF EXISTS component_lifetime_analysis")

        component_lifetime_analysis_sql = """
        CREATE VIEW component_lifetime_analysis AS
        SELECT
            type,
            -- Counts by status
            COUNT(*) as total_components,
            SUM(CASE WHEN status = 'installed' THEN 1 ELSE 0 END) as currently_installed,
            SUM(CASE WHEN status = 'retired' THEN 1 ELSE 0 END) as retired_count,
            SUM(CASE WHEN status = 'not_installed' THEN 1 ELSE 0 END) as inventory_count,
            
            -- Usage statistics for retired components (complete lifecycle)
            ROUND(AVG(CASE WHEN status = 'retired' THEN distance_km END), 2) as avg_km_at_retirement,
            ROUND(MIN(CASE WHEN status = 'retired' THEN distance_km END), 2) as min_km_at_retirement,
            ROUND(MAX(CASE WHEN status = 'retired' THEN distance_km END), 2) as max_km_at_retirement,
            ROUND(AVG(CASE WHEN status = 'retired' THEN moving_time_hours END), 2) as avg_hours_at_retirement,
            ROUND(AVG(CASE WHEN status = 'retired' THEN rides END), 0) as avg_rides_at_retirement,
            
            -- Current installed components statistics
            ROUND(AVG(CASE WHEN status = 'installed' THEN distance_km END), 2) as avg_km_currently_installed,
            ROUND(AVG(CASE WHEN status = 'installed' THEN moving_time_hours END), 2) as avg_hours_currently_installed,
            ROUND(AVG(CASE WHEN status = 'installed' THEN rides END), 0) as avg_rides_currently_installed,
            
            -- Retirement timeline (for components with retirement dates)
            MIN(DATE(retired_at)) as earliest_retirement,
            MAX(DATE(retired_at)) as latest_retirement,
            COUNT(CASE WHEN retired_at IS NOT NULL THEN 1 END) as components_with_retirement_dates,
            
            -- Replacement frequency (approximate)
            CASE 
                WHEN COUNT(CASE WHEN retired_at IS NOT NULL THEN 1 END) > 1 AND 
                     MIN(DATE(retired_at)) != MAX(DATE(retired_at)) THEN
                    ROUND(
                        CAST((JULIANDAY(MAX(retired_at)) - JULIANDAY(MIN(retired_at))) / 365.25 AS REAL) / 
                        (COUNT(CASE WHEN retired_at IS NOT NULL THEN 1 END) - 1), 
                        2
                    )
                ELSE NULL
            END as avg_years_between_replacements
            
        FROM component_summary
        GROUP BY type
        HAVING COUNT(*) > 0
        ORDER BY total_components DESC, retired_count DESC
        """

        db.execute(component_lifetime_analysis_sql)
        print("Created component_lifetime_analysis view")
    except Exception as e:
        print(f"Note: Could not create views: {e}")

    print(f"SQLite database created: {db_path}")
    return db_path


def download_data(bearer_token, output_dir="data"):
    """Download ProBikeGarage data to JSON files."""
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True)

    headers = {
        "accept": "*/*",
        "accept-language": "en-GB,en;q=0.9,de-DE;q=0.8,de;q=0.7",
        "authorization": f"Bearer {bearer_token}",
        "dnt": "1",
        "origin": "https://app.probikegarage.com",
        "priority": "u=1, i",
        "referer": "https://app.probikegarage.com/",
        "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        "sec-ch-ua-mobile": "?0",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    }

    urls_and_files = [
        ("https://api.probikegarage.com/detailed-bikes", f"{output_dir}/bikes.json"),
        (
            "https://api.probikegarage.com/components?sort=name&filter=retired",
            f"{output_dir}/components-retired.json",
        ),
        (
            "https://api.probikegarage.com/components?sort=name&filter=not-installed",
            f"{output_dir}/components-notinstalled.json",
        ),
        (
            "https://api.probikegarage.com/components?sort=name&filter=installed",
            f"{output_dir}/components-installed.json",
        ),
    ]

    success_count = 0
    with httpx.Client() as client:
        for url, filepath in urls_and_files:
            filename = Path(filepath).name
            print(f"Downloading {filename}...")
            try:
                response = client.get(url, headers=headers)
                response.raise_for_status()

                data = response.json()

                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                print(f"Saved {filepath}")
                success_count += 1

            except httpx.HTTPStatusError as e:
                print(f"HTTP error downloading {filename}: {e}")
            except httpx.RequestError as e:
                print(f"Request error downloading {filename}: {e}")
            except json.JSONDecodeError as e:
                print(f"JSON decode error for {filename}: {e}")
            except Exception as e:
                print(f"Unexpected error downloading {filename}: {e}")

    print(f"Download complete: {success_count}/{len(urls_and_files)} files saved")
    return success_count == len(urls_and_files)


def load_bearer_token(token_arg):
    """Load bearer token from command line argument or .secret.json file."""
    if token_arg:
        return token_arg

    secret_file = Path(".secret.json")
    if secret_file.exists():
        try:
            with open(secret_file, "r", encoding="utf-8") as f:
                secrets = json.load(f)
                return secrets.get("bearer_token")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error reading .secret.json: {e}")
            return None

    return None


def main(
    update: bool = typer.Option(False, "--update", help="Download and update the data files"),
    token: str = typer.Option(None, "--token", help="Bearer token for ProBikeGarage API authentication"),
    to_sqlite: str = typer.Option(None, "--to-sqlite", help="Convert JSON files to SQLite database (specify database path)")
):
    """Download ProBikeGarage data to JSON files and optionally convert to SQLite."""

    # Handle SQLite conversion
    if to_sqlite:
        convert_to_sqlite(to_sqlite)
        return

    if not update:
        print(
            "Use --update to download data files or --to-sqlite to convert existing files"
        )
        return

    bearer_token = load_bearer_token(token)
    if not bearer_token:
        print(
            "Error: No bearer token provided. Use --token option or create .secret.json file."
        )
        print(
            'Example .secret.json: {"bearer_token": "your-token-here"}'
        )
        return

    # Download data to the data directory
    success = download_data(bearer_token)
    if not success:
        print("Some downloads failed. Check the error messages above.")


if __name__ == "__main__":
    typer.run(main)
