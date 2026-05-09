# POSITIVE — Sovereign Intent Engine

A self-hosted, privacy-first personal and group sanctuary for meditation, prayer, vision boards, gratitude journaling, and mindful reading. Runs entirely on your own hardware.

## Features

- **Meditation Timers** — countdown sessions with linked audio, relay notifications on completion
- **Repository of Light** — Good Thoughts, Prayers (with answered tracking), and Gratitude journal
- **Vision Board Creator** — upload images, generate a permanent standalone HTML file
- **Media Library** — upload and stream MP3s, MP4s, PDFs, and texts
- **Reading Hub** — track reading progress on uploaded texts
- **Relay Engine** — notify via Email, Discord, Rocket.Chat, and .ics Calendar on events
- **User System** — Architect / Practitioner / Guest roles, private vs shared entries
- **Group Focus** — shared library items, community vision boards, group gratitude feed

## Quick Start

### Requirements
- Docker and Docker Compose installed
- That's it.

### 1. Clone or download
```bash
git clone https://github.com/yourusername/positive.git
cd positive
```

### 2. Configure (optional)
```bash
cp .env.example .env
nano .env   # add Discord/email/RC webhooks if you want relays
```

### 3. Build and launch
```bash
docker compose up --build -d
```

### 4. Access
Open your browser: **http://localhost:8178**

Default login: `admin` / `positive2026`

**Change this password immediately** at http://localhost:8178/admin

---

## Adding Users

Log in as admin → http://yourserver:8178/admin → Users → Add User

Set their role in User Profiles (Architect = full admin, Practitioner = standard user).

## Relay Configuration

Edit `.env` and set:

```
DISCORD_WEBHOOK=https://discord.com/api/webhooks/your-webhook-url
ROCKETCHAT_WEBHOOK=https://your-rc-server/hooks/your-token
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=you@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

Then restart: `docker compose restart`

## Data & Backup

All data lives in two folders:
- `./data/` — SQLite database
- `./media/` — all uploaded files and generated vision boards

Back these up to keep everything safe. The Docker container itself is stateless.

## Ports

Default port is `8178`. Change it in `.env`:
```
PORT=9000
```

## Running on a Local Network

Find your server IP: `ip a` → look for `inet 192.168.x.x`

Access from any device on the network: `http://192.168.x.x:8178`

## Tech Stack

- Python / Django 5
- SQLite (portable, zero-config database)
- Gunicorn (production WSGI server)
- Docker (portable deployment)
- Zero JavaScript frameworks — plain HTML, CSS, vanilla JS

## License

MIT — do whatever you want with it. You own your data.
