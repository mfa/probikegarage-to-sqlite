import json
from pathlib import Path

import click
import httpx


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
            click.echo(f"Error reading .secret.json: {e}", err=True)
            return None
    
    return None


@click.command()
@click.option("--update", is_flag=True, help="Download and update the data files")
@click.option("--token", help="Bearer token for ProBikeGarage API authentication")
def main(update, token):
    """Download ProBikeGarage data to JSON files."""
    if not update:
        click.echo("Use --update to download data files")
        return

    bearer_token = load_bearer_token(token)
    if not bearer_token:
        click.echo("Error: No bearer token provided. Use --token option or create .secret.json file.", err=True)
        click.echo('Example .secret.json: {"bearer_token": "your-token-here"}', err=True)
        return

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
        ("https://api.probikegarage.com/detailed-bikes", "bikes.json"),
        (
            "https://api.probikegarage.com/components?sort=name&filter=retired",
            "components-retired.json",
        ),
        (
            "https://api.probikegarage.com/components?sort=name&filter=not-installed",
            "components-notinstalled.json",
        ),
    ]

    with httpx.Client() as client:
        for url, filename in urls_and_files:
            click.echo(f"Downloading {filename}...")
            try:
                response = client.get(url, headers=headers)
                response.raise_for_status()

                data = response.json()

                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                click.echo(f"Saved {filename}")

            except httpx.HTTPStatusError as e:
                click.echo(f"HTTP error downloading {filename}: {e}", err=True)
            except httpx.RequestError as e:
                click.echo(f"Request error downloading {filename}: {e}", err=True)
            except json.JSONDecodeError as e:
                click.echo(f"JSON decode error for {filename}: {e}", err=True)
            except Exception as e:
                click.echo(f"Unexpected error downloading {filename}: {e}", err=True)


if __name__ == "__main__":
    main()
