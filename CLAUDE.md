# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Luna shows 6 Google Nest cameras on one page. It runs [go2rtc](https://github.com/AlexxIT/go2rtc) in Docker, which pulls the streams through the Google Smart Device Management (SDM) API (`nest:` source) and serves a static grid page. There is no build step, linter or test suite.

## Commands

```
cp cameras.example.json cameras.json   # then set each device_id and name
cp .env.example .env     # fill in NEST_PROJECT_ID, NEST_CLIENT_ID, NEST_CLIENT_SECRET, NEST_REFRESH_TOKEN
./generate.py            # cameras.json + .env -> go2rtc.yaml
docker compose up -d     # start go2rtc (host networking)
docker compose restart   # after regenerating go2rtc.yaml
docker compose logs -f go2rtc
```

The grid is at `http://localhost:1984/` and the go2rtc admin UI is on the same port.

## Architecture

`cameras.json` is gitignored (it holds device IDs; `cameras.example.json` is the template) and is the single source of truth for the camera array (`id`, `name`, `device_id`). Two things consume it:

- `generate.py` reads it with `.env` and writes `go2rtc.yaml`, one `nest:?...&device_id=...` stream per camera, keyed by `id`. The generated file contains secrets and is gitignored, so never edit it by hand. Change `cameras.json` and regenerate.
- `www/index.html` fetches `cameras.json` at runtime and builds the grid. Each tile is a go2rtc `video-stream` element connected to `api/ws?src=<id>`. `docker-compose.yml` mounts `cameras.json` into `/www` next to the page for this reason.

The `id` in `cameras.json` must match the stream name in `go2rtc.yaml`, which `generate.py` guarantees. Adding a camera only means adding an entry to `cameras.json`. The grid sizes itself from the number of visible cameras (`ceil(sqrt(n))` columns). A "Cameras" menu in the page toggles each camera, saves the choice in `localStorage` (`luna.hidden`), and unmounts the `video-stream` of hidden cameras so their Nest session closes. Tiles can be reordered by dragging them or with the ▲▼ buttons in that menu. The order is saved in `localStorage` (`luna.order`) and applied with CSS `order` rather than by moving DOM nodes, since moving a `video-stream` restarts its stream.

Clicking a tile spotlights it (big tile plus a thumbnail strip); clicking it again, or Esc, goes back to the grid. Each tile has mute, snapshot (canvas capture of the `<video>`, downloaded as JPEG) and fullscreen buttons. The native `<video>` controls are turned off because they pause the live stream on click. The menu has an auto-cycle option that spotlights each visible camera in turn, saved as `luna.cycle`, with `?cycle=<seconds>` as a URL override. Only the spotlighted camera is unmuted, whether picked by a click or by auto-cycle, and the grid is muted. Browsers block unmuting before the first click or key press, so a kiosk started with `?cycle=` stays silent until someone clicks once. A watchdog in `www/index.html` checks every 2 s that each visible video's `currentTime` advances. A tile that has not started within 20 s, or has not advanced for 8 s after playing, gets its `video-stream` removed and remounted after a backoff of 5, 10, 20, 40, then 60 s, with a "Reconnecting" badge. It only helps when the stall is on the client side or the producer restarts when the last viewer leaves. `?kiosk=1` hides the menu and buttons, disables dragging, hides the idle cursor, requests a screen wake lock and reloads the page every 6 hours.

`go2rtc.yaml` sets `static_dir: /www`, so go2rtc no longer serves its built-in player. `www/video-stream.js` and `www/video-rtc.js` are copies from the go2rtc repo and must stay there.

`docker-compose.yml` uses `network_mode: host` on purpose, because WebRTC (port 8555) is unreliable behind Docker's NAT.

`site/` is separate from the app. It holds the static home page and privacy policy that Google's OAuth consent screen asks for, meant to be deployed on its own (for example on Vercel). It is not mounted in Docker and is gitignored (local only). It is deployed on Vercel from that folder (`npx vercel --prod --yes`).

## Gotchas

- `cameras.example.json` has `REPLACE_ME` device IDs, and `generate.py` refuses to run until they are replaced in your `cameras.json`.
- Only SDM-supported cameras work, and they must be linked to a Google Home account (not a legacy Nest account).
- go2rtc's API on port 1984 has no auth by default, so keep it LAN-only.
- `docker-compose.yml` uses `alexxit/go2rtc:master`, not `latest`. With 1.9.14 (`latest`), WebRTC viewers attached to an empty video receiver and tiles stayed on "loading" with only audio. `master` fixed it. Updating the image needs `docker compose pull` and `up -d --force-recreate`, because a plain `restart` keeps the old image.
- go2rtc `master` (c245815) can leave a Nest producer with two video receivers: an empty one that viewers attach to and a live one that nobody reads. Tiles then stay on "loading" while `/api/streams` shows `bytes` only on the second receiver. The page's recovery cannot fix this. It reproduces on fresh producers, so check with `curl localhost:1984/api/streams` (look at each producer's `receivers`). Dropping every viewer of a stream stops its producer.
- `GET /api/streams` returns each source URL, which includes the Nest client secret and refresh token, to anyone who can reach port 1984.
