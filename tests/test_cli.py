import csv
import json

from spotify2csv.cli import (
    PROFILE_URL,
    REPOSITORY_URL,
    build_parser,
    export_liked_songs,
    load_saved_client_id,
    main,
    render_banner,
    save_client_id,
)


class FakeSpotify:
    def __init__(self):
        self.pages = [
            {
                "items": [
                    {
                        "track": {
                            "name": "Song, With Comma",
                            "artists": [{"name": "Artist One"}, {"name": "Artist Two"}],
                            "album": {"name": "Album Name"},
                        }
                    },
                    {"track": None},
                ],
                "next": "page-2",
            },
            {
                "items": [
                    {
                        "track": {
                            "name": "Second Song",
                            "artists": [{"name": "Solo Artist"}],
                            "album": {"name": "Second Album"},
                        }
                    }
                ],
                "next": None,
            },
        ]

    def current_user_saved_tracks(self, limit):
        assert limit == 50
        return self.pages[0]

    def next(self, page):
        assert page is self.pages[0]
        return self.pages[1]


def test_export_liked_songs_writes_all_pages(tmp_path):
    output = tmp_path / "library.csv"

    count = export_liked_songs(FakeSpotify(), output)

    assert count == 2
    with output.open(newline="", encoding="utf-8-sig") as csv_file:
        assert list(csv.reader(csv_file)) == [
            ["name", "artist", "album"],
            ["Song, With Comma", "Artist One, Artist Two", "Album Name"],
            ["Second Song", "Solo Artist", "Second Album"],
        ]


def test_main_requires_client_id(monkeypatch, capsys):
    monkeypatch.delenv("SPOTIPY_CLIENT_ID", raising=False)
    monkeypatch.setattr("spotify2csv.cli.load_saved_client_id", lambda: None)

    assert main([]) == 2
    assert "SPOTIPY_CLIENT_ID" in capsys.readouterr().err


def test_default_redirect_uri_is_loopback(monkeypatch):
    monkeypatch.delenv("SPOTIPY_REDIRECT_URI", raising=False)

    assert build_parser().parse_args([]).redirect_uri == "http://127.0.0.1:8888/callback"
    assert build_parser().parse_args([]).cache.name == ".spotify_cache-pkce"


def test_banner_contains_brand_credit_and_links():
    banner = render_banner()

    assert "Designed by GrimSythe" in banner
    assert REPOSITORY_URL in banner
    assert PROFILE_URL in banner
    assert banner.splitlines()[-2].rstrip().endswith("Designed by GrimSythe |")


def test_no_banner_suppresses_interface(monkeypatch, capsys):
    monkeypatch.delenv("SPOTIPY_CLIENT_ID", raising=False)
    monkeypatch.setattr("spotify2csv.cli.load_saved_client_id", lambda: None)

    assert main(["--no-banner"]) == 2
    output = capsys.readouterr()
    assert "Designed by GrimSythe" not in output.out


def test_interactive_run_prompts_for_client_id(monkeypatch):
    class InteractiveInput:
        def isatty(self):
            return True

    monkeypatch.delenv("SPOTIPY_CLIENT_ID", raising=False)
    monkeypatch.setattr("spotify2csv.cli.load_saved_client_id", lambda: None)
    monkeypatch.setattr("sys.stdin", InteractiveInput())
    monkeypatch.setattr("builtins.input", lambda prompt: "prompted-client-id")

    captured = {}

    def fake_client(client_id, redirect_uri, cache_path, open_browser=True):
        captured["client_id"] = client_id
        return FakeSpotify()

    monkeypatch.setattr("spotify2csv.cli.make_client", fake_client)
    monkeypatch.setattr("spotify2csv.cli.export_liked_songs", lambda client, output: 2)

    assert main(["--no-banner"]) == 0
    assert captured["client_id"] == "prompted-client-id"


def test_saved_client_id_round_trip(tmp_path):
    config = tmp_path / ".spotify2csv.json"

    save_client_id("saved-client-id", config)

    assert load_saved_client_id(config) == "saved-client-id"
    assert json.loads(config.read_text(encoding="utf-8")) == {
        "client_id": "saved-client-id"
    }
