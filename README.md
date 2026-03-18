# SeminarTimer

A minimal countdown timer for seminars and presentations. It renders as a slim always-on-top progress bar across **all connected monitors** and can be controlled locally (buttons in the bar) or remotely from any phone or browser on the same network.


The bar is green while time remains. Once the time is up it stays full and the color fades gradually from green to red over a configurable overtime window.

---

## Requirements

```bash
pip install flask screeninfo requests
```

---

## Usage

### 1 — Timer only (local control)

```bash
python3 timerbar.py --duration-seconds 600
```

A 25 px bar appears at the top of every monitor. Use the three buttons on the left:

| Button | Action |
|--------|--------|
| ▶ / ⏸ | Start / Pause |
| ↺      | Reset to full duration |
| ✕      | Quit |

### 2 — Timer + remote control

Run the Flask server on the presenter machine (or any reachable host):

```bash
python3 server.py --host 0.0.0.0 --port 5000
```

Then start the timer and point it at the server:

```bash
python3 timerbar.py --duration-seconds 600 --server-url http://<host>:5000
```

Open `http://<host>:5000/` on any device on the network to get a mobile-friendly control page with **START / PAUSE** and **RESET** buttons.

> **Security note:** The server has no built-in TLS or authentication. For anything beyond a trusted local network, place a reverse proxy (e.g. nginx) in front of it to handle HTTPS and access control.

---

## Options

### `timerbar.py`

| Flag | Default | Description |
|------|---------|-------------|
| `--duration-seconds` | `600` | Countdown duration in seconds |
| `--server-url` | _(none)_ | Base URL of the control server; enables remote polling |
| `--start-fade` | `15` | Seconds into overtime when color transition begins |
| `--end-fade` | `45` | Seconds into overtime when color transition ends (full red) |

### `server.py`

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `0.0.0.0` | Interface to bind to |
| `--port` | `5000` | Port to listen on |

---

## Running behind a reverse proxy (HTTPS + basic auth)

For use outside a trusted local network, use [Caddy](https://caddyserver.com/) as a lightweight reverse proxy. It obtains and renews TLS certificates automatically and needs only a single config file.

### 1 — Install Caddy

```bash
sudo apt install caddy
```

### 2 — Hash a password

```bash
caddy hash-password
```

Copy the printed `$2a$...` hash for use in the next step.

### 3 — Caddyfile

Create or edit `/etc/caddy/Caddyfile`:

```caddy
timer.example.com {
    basicauth {
        <username> <bcrypt-hash>
    }
    reverse_proxy 127.0.0.1:5000
}
```

Reload Caddy:

```bash
sudo systemctl reload caddy
```

Caddy automatically obtains a Let's Encrypt certificate for `timer.example.com` and redirects HTTP to HTTPS.

### 4 — Start the timer pointing at the public URL

```bash
python3 server.py --host 127.0.0.1 --port 5000   # bind only to localhost
python3 timerbar.py --duration-seconds 600 --server-url https://timer.example.com
```

The mobile control page is then available at `https://timer.example.com/` (password-protected).

---

## How it works

- `timerbar.py` opens a borderless, always-on-top tkinter window at the top of each monitor detected by `screeninfo`.
- When `--server-url` is provided, a background thread polls `GET /status` every 500 ms. The server resets `last_command` to `null` after each read so commands are only applied once.
- `server.py` is a tiny Flask app that exposes `/toggle` and `/reset` (POST from the web page) and `/status` (GET for the timer to poll).

