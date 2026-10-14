# Luna

All your Google Nest cameras on one page. [go2rtc](https://github.com/AlexxIT/go2rtc) runs in Docker, pulls the live streams through the Google Smart Device Management (SDM) API, and serves a static grid page from `www/`. There is no build step.

Features: auto-sized grid, hide and reorder cameras, click to spotlight one camera (with sound), auto-cycle, snapshots, fullscreen, and a kiosk mode for a wall display.

## Requirements

- Docker and Python 3
- Nest cameras linked to a Google Home account (not a legacy Nest account). Only SDM-supported cameras work.
- A [Device Access](https://developers.google.com/nest/device-access) project (one-time US$5 fee) and a Google Cloud OAuth client

## Setup

1. **Device Access and OAuth.** Create a Device Access project and a Google Cloud OAuth client of type *Web application* with redirect URI `https://www.google.com`. Link the OAuth client ID to the Device Access project.
2. **Get a refresh token.** Open this URL in a browser, approve access, and copy the `code` parameter from the redirect URL:

   ```
   https://nestservices.google.com/partnerconnections/<PROJECT_ID>/auth?redirect_uri=https://www.google.com&access_type=offline&prompt=consent&client_id=<CLIENT_ID>&response_type=code&scope=https://www.googleapis.com/auth/sdm.service
   ```

   Exchange it for a token:

   ```
   curl -X POST https://www.googleapis.com/oauth2/v4/token \
     -d client_id=<CLIENT_ID> -d client_secret=<CLIENT_SECRET> \
     -d code=<CODE> -d grant_type=authorization_code \
     -d redirect_uri=https://www.google.com
   ```

   Keep the `refresh_token` from the response. If the OAuth consent screen is in *Testing*, the token expires after 7 days. Publish the app to avoid that.
3. **Configure.**

   ```
   cp .env.example .env                    # fill in the four NEST_* values
   cp cameras.example.json cameras.json    # set id, name and device_id per camera
   ```

   Get the device IDs from the SDM API (`GET https://smartdevicemanagement.googleapis.com/v1/enterprises/<PROJECT_ID>/devices`).
4. **Run.**

   ```
   ./generate.py          # cameras.json + .env -> go2rtc.yaml
   docker compose up -d
   ```

Open `http://localhost:1984/`.

## Usage

- **Cameras menu:** show or hide cameras and reorder them. Choices are saved in the browser.
- **Click a tile** to spotlight it and hear its sound. Click again or press Esc to go back.
- **Auto-cycle:** set it in the menu, or use `?cycle=<seconds>`.
- **Kiosk mode:** `?kiosk=1` hides the controls and cursor, keeps the screen awake and reloads every 6 hours. Browsers keep sound blocked until the first click.
- **Player mode:** WebRTC by default. `?mode=webrtc,mse` or `?mode=mse` overrides it.

## Updating

After changing `cameras.json`, run `./generate.py` and `docker compose restart`. To update go2rtc, run `docker compose pull` and `docker compose up -d --force-recreate`. A plain restart keeps the old image.

## Security

- `.env` and `go2rtc.yaml` contain your credentials and are gitignored. Never commit them. `cameras.json` is ignored too, because it lists your device IDs.
- go2rtc's API and the page have no login. Keep port 1984 on your LAN, or put it behind a VPN or an authenticating proxy.

## Notes

- The image is `alexxit/go2rtc:master`, not `latest`. Version 1.9.14 left WebRTC tiles stuck on "loading".
- The container uses host networking because WebRTC is unreliable behind Docker's NAT.

See `CLAUDE.md` for the architecture.
