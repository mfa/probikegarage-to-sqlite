"""Download functionality for ProBikeGarage API data."""

import json
from pathlib import Path

import httpx


def _get_api_headers(bearer_token):
    """Get standard headers for ProBikeGarage API requests."""
    return {
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


def _download_json(client, url, headers, description="file"):
    """Download JSON data from URL with error handling."""
    try:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        print(f"HTTP error downloading {description}: {e}")
        return None
    except httpx.RequestError as e:
        print(f"Request error downloading {description}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error for {description}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error downloading {description}: {e}")
        return None


def download_data(bearer_token, output_dir="data"):
    """Download ProBikeGarage data to JSON files."""
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True)

    headers = _get_api_headers(bearer_token)

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

            data = _download_json(client, url, headers, filename)
            if data is not None:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"Saved {filepath}")
                success_count += 1

    print(f"Download complete: {success_count}/{len(urls_and_files)} files saved")
    return success_count == len(urls_and_files)


def download_component_details(bearer_token, output_dir="data/component_details"):
    """Download detailed information for all components with appropriate update strategies."""
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Load all component files
    component_files = {
        "retired": "data/components-retired.json",
        "installed": "data/components-installed.json",
        "not_installed": "data/components-notinstalled.json",
    }

    all_components = []
    for component_type, filepath in component_files.items():
        if Path(filepath).exists():
            with open(filepath, "r", encoding="utf-8") as f:
                components = json.load(f)
                for component in components:
                    component["_source_type"] = component_type
                all_components.extend(components)
        else:
            print(
                f"Warning: {filepath} not found, skipping {component_type} components"
            )

    headers = _get_api_headers(bearer_token)

    success_count = 0
    skipped_count = 0
    updated_count = 0

    with httpx.Client() as client:
        for component in all_components:
            component_id = component["id"]
            component_name = component.get("name", "unknown")
            component_source_type = component["_source_type"]
            component_api_type = component.get("type", "unknown")

            # Create filename with component type: uuid--type.json
            safe_type = component_api_type.replace("/", "-").replace(" ", "-")
            output_file = Path(output_dir) / f"{component_id}--{safe_type}.json"

            # Different strategies based on component type
            if component_source_type == "retired":
                # Retired components: only download if file doesn't exist
                if output_file.exists():
                    skipped_count += 1
                    continue
            else:
                # Active components (installed/not_installed): always update
                if output_file.exists():
                    updated_count += 1

            # Download component details and installations
            component_url = f"https://api.probikegarage.com/components/{component_id}"
            installations_url = (
                f"https://api.probikegarage.com/components/{component_id}/installations"
            )

            # Download both datasets
            component_data = _download_json(
                client, component_url, headers, f"{component_name} component"
            )
            installations_data = _download_json(
                client, installations_url, headers, f"{component_name} installations"
            )

            # Only save if both downloads succeeded
            if component_data is not None and installations_data is not None:
                # Combine the data
                combined_data = {
                    "component": component_data,
                    "installations": installations_data,
                }

                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(combined_data, f, indent=2, ensure_ascii=False)

                success_count += 1

    print(
        f"Component details download complete: {success_count} downloaded, {updated_count} updated, {skipped_count} skipped"
    )
    return True


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
        except json.JSONDecodeError as e:
            print(f"Error reading .secret.json: {e}")
            return None

    return None
