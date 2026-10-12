"""Command-line interface for spotify2csv."""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import spotipy
from spotipy.oauth2 import SpotifyPKCE

from . import __version__

DEFAULT_REDIRECT_URI = "http://127.0.0.1:8888/callback"
DEFAULT_OUTPUT = Path("liked_songs.csv")
DEFAULT_CACHE = Path(".spotify_cache")
SCOPE = "user-library-read"
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
        help="OAuth token cache path (default: .spotify_cache)",
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
        cache_path=str(cache_path),
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
    if not args.client_id:
        print(
            "Error: set SPOTIPY_CLIENT_ID or pass --client-id. "
            "See README.md for setup instructions.",
            file=sys.stderr,
        )
        return 2

    try:
        client = make_client(
            args.client_id,
            args.redirect_uri,
            args.cache,
            open_browser=not args.no_browser,
        )
        count = export_liked_songs(client, args.output)
    except KeyboardInterrupt:
        print("\nCancelled; the existing output file was not changed.", file=sys.stderr)
        return 130
    except spotipy.SpotifyException as error:
        print(f"Spotify API error: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"File error: {error}", file=sys.stderr)
        return 1

    print(f"Done. Wrote {count} songs to {args.output.expanduser().resolve()}")
    return 0
