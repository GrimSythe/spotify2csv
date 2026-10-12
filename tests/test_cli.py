import csv

from spotify2csv.cli import (
    PROFILE_URL,
    REPOSITORY_URL,
    build_parser,
    export_liked_songs,
    main,
    render_banner,
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

    assert main([]) == 2
    assert "SPOTIPY_CLIENT_ID" in capsys.readouterr().err


def test_default_redirect_uri_is_loopback(monkeypatch):
    monkeypatch.delenv("SPOTIPY_REDIRECT_URI", raising=False)

    assert build_parser().parse_args([]).redirect_uri == "http://127.0.0.1:8888/callback"


def test_banner_contains_brand_credit_and_links():
    banner = render_banner()

    assert "Designed by GrimSythe" in banner
    assert REPOSITORY_URL in banner
    assert PROFILE_URL in banner
    assert banner.splitlines()[-2].rstrip().endswith("Designed by GrimSythe |")


def test_no_banner_suppresses_interface(monkeypatch, capsys):
    monkeypatch.delenv("SPOTIPY_CLIENT_ID", raising=False)

    assert main(["--no-banner"]) == 2
    output = capsys.readouterr()
    assert "Designed by GrimSythe" not in output.out
