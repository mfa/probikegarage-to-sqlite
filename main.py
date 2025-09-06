import typer

from download import download_component_details, download_data, load_bearer_token
from sqlite_converter import convert_to_sqlite


def main(
    update: bool = typer.Option(
        False, "--update", help="Download and update the data files"
    ),
    token: str = typer.Option(
        None, "--token", help="Bearer token for ProBikeGarage API authentication"
    ),
    to_sqlite: str = typer.Option(
        None,
        "--to-sqlite",
        help="Convert JSON files to SQLite database (specify database path)",
    ),
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
        print('Example .secret.json: {"bearer_token": "your-token-here"}')
        return

    # Download main data files first
    success = download_data(bearer_token)
    if not success:
        print("Some downloads failed. Check the error messages above.")
        return

    # Download component details after main data is available
    print("\nDownloading component details...")
    download_component_details(bearer_token)
    print("All downloads completed successfully!")


if __name__ == "__main__":
    typer.run(main)
