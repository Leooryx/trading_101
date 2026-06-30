"""Interactively configure local Alpaca API credentials."""

from __future__ import annotations

from getpass import getpass
from pathlib import Path

from dotenv import dotenv_values, set_key


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"


def ask_required_secret(prompt: str) -> str:
    """Prompt for a non-empty value without displaying it on screen."""
    while True:
        value = getpass(prompt).strip()
        if value:
            return value
        print("This value is required.")


def ask_yes_no(prompt: str, *, default: bool) -> bool:
    """Ask a yes/no question and return the selected value."""
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        answer = input(f"{prompt} {suffix} ").strip().lower()
        if not answer:
            return default
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please answer yes or no.")


def main() -> None:
    """Collect credentials and save them to the project's local .env file."""
    print("Alpaca API access configuration")
    print("The values entered will be hidden and saved only in .env.\n")

    existing = dotenv_values(ENV_FILE) if ENV_FILE.exists() else {}
    has_credentials = bool(
        existing.get("ALPACA_API_KEY") or existing.get("ALPACA_SECRET_KEY")
    )
    if has_credentials and not ask_yes_no(
        "Credentials already exist. Do you want to replace them?",
        default=False,
    ):
        print("Configuration unchanged.")
        return

    api_key = ask_required_secret("Alpaca API key: ")
    secret_key = ask_required_secret("Alpaca secret key: ")
    paper = ask_yes_no("Use the paper trading account?", default=True)

    ENV_FILE.touch(exist_ok=True)
    set_key(ENV_FILE, "ALPACA_API_KEY", api_key)
    set_key(ENV_FILE, "ALPACA_SECRET_KEY", secret_key)
    set_key(ENV_FILE, "ALPACA_PAPER", "true" if paper else "false")

    print(f"\nCredentials saved in {ENV_FILE}")
    print("You can now inspect the account with check_account_state.py.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nConfiguration cancelled.")
