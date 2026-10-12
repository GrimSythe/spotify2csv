# spotify2csv

`spotify2csv` exports every track in your Spotify **Liked Songs** library to a
CSV file with `name`, `artist`, and `album` columns. It uses Spotify's official
Web API and asks only for permission to read your saved library.

It opens with a dependency-free ASCII interface containing the project links
and GrimSythe design credit. Use `--no-banner` when calling it from a script.

The export is UTF-8 with a byte-order mark, so names with accents and other
non-ASCII characters open cleanly in Excel as well as standard CSV tools.

## Requirements

- Python 3.9 or newer
- A Spotify account with access to the Web API
- A free app created in the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)

## Quick start

### 1. Create and configure a Spotify app

1. Open the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard),
   sign in, and create an app that uses the Web API.
2. Open the app's settings and add this exact Redirect URI:

   ```text
   http://127.0.0.1:8888/callback
   ```

3. Save the settings and copy the app's **Client ID**. `spotify2csv` uses the
   PKCE login flow, so it does not need or store your Client Secret.

Spotify requires the registered redirect URI and the URI used by this tool to
match exactly. Use `127.0.0.1`, not `localhost`.

### 2. Install spotify2csv

Open a terminal in this folder and create an isolated environment.

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -e .
```

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
```

### 3. Set your Client ID

PowerShell:

```powershell
$env:SPOTIPY_CLIENT_ID = "your_client_id_here"
```

Command Prompt:

```bat
set SPOTIPY_CLIENT_ID=your_client_id_here
```

macOS or Linux:

```bash
export SPOTIPY_CLIENT_ID="your_client_id_here"
```

This setting lasts for the current terminal session. You can also pass the
Client ID for one run with `--client-id`.

### 4. Export your library

```text
spotify2csv
```

Your browser will open the first time so you can approve read-only access. The
tool then writes `liked_songs.csv` in the current directory. Future runs reuse
the local `.spotify_cache` authorization file until you revoke access or remove
that file.

## Usage

```text
usage: spotify2csv [-h] [-o OUTPUT] [--client-id CLIENT_ID]
                   [--redirect-uri REDIRECT_URI] [--cache CACHE]
                   [--no-browser] [--no-banner] [--version]
```

Choose another output file:

```text
spotify2csv --output exports/my-liked-songs.csv
```

Run on a machine where a browser cannot open automatically:

```text
spotify2csv --no-browser
```

The tool will print an authorization URL for you to open manually.

Hide the ASCII interface for automation or redirected logs:

```text
spotify2csv --no-banner
```

You can also run the package or the legacy script directly:

```text
python -m spotify2csv
python export_liked_songs.py
```

Run `spotify2csv --help` for every option.

## Output

The CSV contains one row per available saved track:

```csv
name,artist,album
Song Title,"Artist One, Artist Two",Album Title
```

If an unavailable or removed track has no track data, the tool skips it. An
existing output file is replaced only after the full export has been fetched
and written successfully.

## Privacy and security

- The app requests only Spotify's `user-library-read` permission.
- Authentication uses Authorization Code with PKCE; no Client Secret is needed.
- `.spotify_cache` contains reusable account tokens. Do not share or commit it.
- Exported CSV files reveal your music library. They are ignored by Git by
  default, but you should review them before sharing.
- To disconnect the tool, remove its access in your Spotify account's app
  permissions and delete `.spotify_cache`.

Never publish a Client Secret or an existing `.spotify_cache` file. If either
has already been shared, rotate the secret in the Developer Dashboard and
revoke the app's access before continuing.

## Troubleshooting

### `set SPOTIPY_CLIENT_ID or pass --client-id`

Set the environment variable in the same terminal where you run the command,
or use `spotify2csv --client-id YOUR_ID`.

### `INVALID_CLIENT: Invalid redirect URI`

Confirm that the Spotify app has
`http://127.0.0.1:8888/callback` registered exactly, including the port and
`/callback` path.

### PowerShell blocks `Activate.ps1`

You can skip activation and call the environment's Python directly:

```powershell
.venv\Scripts\python.exe -m pip install -e .
$env:SPOTIPY_CLIENT_ID = "your_client_id_here"
.venv\Scripts\python.exe -m spotify2csv
```

### Start authentication over

Delete `.spotify_cache` and run the command again. Treat that cache as a
credential; do not send it to anyone while troubleshooting.

## Development

Install the test dependency and run the tests:

```text
python -m pip install -e ".[dev]"
python -m pytest
```

This project was created by GrimSythe and is not affiliated with Spotify.
Spotify is a trademark of Spotify AB.

- Project: [github.com/GrimSythe/spotify2csv](https://github.com/GrimSythe/spotify2csv)
- Creator: [github.com/GrimSythe](https://github.com/GrimSythe)
