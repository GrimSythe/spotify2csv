"""Command-line interface for spotify2csv."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
import webbrowser
from pathlib import Path
from typing import Any

import spotipy
from spotipy.cache_handler import CacheFileHandler
from spotipy.exceptions import SpotifyOauthError
from spotipy.oauth2 import SpotifyPKCE

from . import __version__

DEFAULT_REDIRECT_URI = "http://127.0.0.1:8888/callback"
DEFAULT_OUTPUT = Path("liked_songs.csv")
DEFAULT_CACHE = Path(".spotify_cache-pkce")
DEFAULT_CONFIG = Path(".spotify2csv.json")
SCOPE = "user-library-read"
DASHBOARD_URL = "https://developer.spotify.com/dashboard"
REPOSITORY_URL = "https://github.com/GrimSythe/spotify2csv"
PROFILE_URL = "https://github.com/GrimSythe"

ASCII_TITLE = (
    r"  ____              _   _  __       ____   ____ __     __",
    r" / ___| _ __   ___ | |_(_)/ _|_   _|___ \ / ___|\ \   / /",
    r" \___ \| '_ \ / _ \| __| | |_| | | | __) | |     \ \ / / ",
    r"  ___) | |_) | (_) | |_| |  _| |_| |/ __/| |___   \ V /  ",
    r" |____/| .__/ \___/ \__|_|_|  \__, |_____|\____|   \_/   ",
    r"       |_|                     |___/                       ",
)


def render_banner() -> str:
    """Return the dependency-free terminal interface banner."""
    content = [
        *ASCII_TITLE,
        "",
        "Export your Spotify Liked Songs to CSV",
        "",
        f"Repository: {REPOSITORY_URL}",
        f"Profile:    {PROFILE_URL}",
        "",
        "Designed by GrimSythe",
    ]
    minimum_width = max(len(line) for line in content) + 4
    terminal_width = shutil.get_terminal_size(fallback=(88, 24)).columns
    width = max(minimum_width, min(terminal_width, 100))
    inner_width = width - 2

    lines = ["+" + "-" * inner_width + "+"]
    for index, line in enumerate(content):
        if index < len(ASCII_TITLE):
            rendered = line.center(inner_width)
        elif line == "Designed by GrimSythe":
            rendered = line.rjust(inner_width - 1) + " "
        else:
            rendered = " " + line.ljust(inner_width - 1)
        lines.append(f"|{rendered}|")
    lines.append("+" + "-" * inner_width + "+")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spotify2csv",
        description="Export your Spotify Liked Songs to a UTF-8 CSV file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="CSV destination (default: liked_songs.csv)",
    )
    parser.add_argument(
        "--client-id",
        default=os.environ.get("SPOTIPY_CLIENT_ID"),
        help="Spotify app Client ID (or set SPOTIPY_CLIENT_ID)",
    )
    parser.add_argument(
        "--redirect-uri",
        default=os.environ.get("SPOTIPY_REDIRECT_URI", DEFAULT_REDIRECT_URI),
        help=f"OAuth redirect URI (default: {DEFAULT_REDIRECT_URI})",
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=DEFAULT_CACHE,
        help="OAuth token cache path (default: .spotify_cache-pkce)",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Open the Spotify dashboard and save a Client ID for future runs",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Print the login URL instead of opening a browser automatically",
    )
    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Hide the ASCII interface (useful for scripts)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def load_saved_client_id(config_path: Path = DEFAULT_CONFIG) -> str | None:
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return None
    client_id = data.get("client_id") if isinstance(data, dict) else None
    return client_id.strip() if isinstance(client_id, str) and client_id.strip() else None


def save_client_id(client_id: str, config_path: Path = DEFAULT_CONFIG) -> None:
    temporary = config_path.with_suffix(config_path.suffix + ".tmp")
    temporary.write_text(
        json.dumps({"client_id": client_id}, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(config_path)


def run_setup(config_path: Path = DEFAULT_CONFIG) -> int:
    print("\nSpotify app setup")
    print("-----------------")
    print("1. Create or open your app in the Spotify Developer Dashboard.")
    print(f"2. Add this exact Redirect URI: {DEFAULT_REDIRECT_URI}")
    print("3. Save the app settings and copy its Client ID (not the Client Secret).")
    print(f"\nOpening {DASHBOARD_URL}\n")
    webbrowser.open(DASHBOARD_URL)

    try:
        client_id = input("Paste your Spotify app Client ID: ").strip()
    except EOFError:
        client_id = ""
    if not client_id:
        print("Setup cancelled; no Client ID was saved.", file=sys.stderr)
        return 2
    if any(character.isspace() for character in client_id):
        print("That Client ID contains spaces. Copy only the Client ID value.", file=sys.stderr)
        return 2

    try:
        save_client_id(client_id, config_path)
    except OSError as error:
        print(f"Could not save the Client ID: {error}", file=sys.stderr)
        return 1

    print(f"\nSetup complete. Client ID saved locally in {config_path.resolve()}")
    print("Run Spotify2CSV to sign in and export your library.")
    return 0


def make_client(
    client_id: str,
    redirect_uri: str,
    cache_path: Path,
    open_browser: bool = True,
) -> spotipy.Spotify:
    auth_manager = SpotifyPKCE(
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=SCOPE,
        cache_handler=CacheFileHandler(cache_path=str(cache_path)),
        open_browser=open_browser,
    )
    return spotipy.Spotify(auth_manager=auth_manager)


def export_liked_songs(client: Any, output: Path) -> int:
    """Fetch every saved track and write it to *output*. Returns row count."""
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    rows: list[tuple[str, str, str]] = []
    page = client.current_user_saved_tracks(limit=50)

    while page:
        for item in page.get("items", []):
            track = item.get("track")
            if not track:
                continue
            artists = ", ".join(
                artist.get("name", "") for artist in track.get("artists", [])
            )
            album = track.get("album") or {}
            rows.append((track.get("name", ""), artists, album.get("name", "")))

        print(f"Fetched {len(rows)} songs...", flush=True)
        page = client.next(page) if page.get("next") else None

    temporary = output.with_suffix(output.suffix + ".tmp")
    try:
        with temporary.open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["name", "artist", "album"])
            writer.writerows(rows)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)

    return len(rows)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.no_banner:
        print(render_banner())
    if args.setup:
        return run_setup()

    client_id = args.client_id or load_saved_client_id()
    if not client_id and sys.stdin.isatty():
        try:
            client_id = input("\nPaste your Spotify app Client ID: ").strip()
        except EOFError:
            client_id = ""
    if not client_id:
        print(
            "Error: set SPOTIPY_CLIENT_ID or pass --client-id. "
            "See README.md for setup instructions.",
            file=sys.stderr,
        )
        return 2

    try:
        client = make_client(
            client_id,
            args.redirect_uri,
            args.cache,
            open_browser=not args.no_browser,
        )
        count = export_liked_songs(client, args.output)
    except KeyboardInterrupt:
        print("\nCancelled; the existing output file was not changed.", file=sys.stderr)
        return 130
    except SpotifyOauthError as error:
        print(
            "Spotify authentication failed. Run `spotify2csv --setup` and confirm "
            f"that {args.redirect_uri} is registered exactly.\nDetails: {error}",
            file=sys.stderr,
        )
        return 1
    except spotipy.SpotifyException as error:
        print(f"Spotify API error: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"File error: {error}", file=sys.stderr)
        return 1

    print(f"Done. Wrote {count} songs to {args.output.expanduser().resolve()}")
    return 0
