# POSITIVE — Sovereign Intent Engine

> A self-hosted, privacy-first sanctuary for meditation, prayer, vision boards, gratitude journaling, and mindful reading. Runs entirely on your own hardware. No cloud. No ads. No data collection.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](docker-compose.yml)
[![Languages](https://img.shields.io/badge/Languages-16-orange.svg)](#languages)

---

## Features

### Meditation Timers
Countdown sessions with linked audio, relay notifications on completion via email, Discord, Rocket.Chat, or calendar (.ics).

### Repository of Light
Log Good Thoughts, Prayers (with answered tracking), and Gratitude entries. Edit, delete, and search across all entries.

### Vision Boards
Create image boards that render as standalone HTML files you can download and display anywhere — even offline.

### Library
Upload and stream MP3, MP4, PDF, and TXT files. Track reading progress page by page. Set scheduled reading reminders.

### Group Hub
- **Broadcast Messages** — admin sends a message that appears on everyone's dashboard
- **Shared Timer** — synchronized group countdown in real time
- **Group Reading** — admin sets text and page; members follow along
- **Community Prayer Wall** — post, support with prayer, mark answered

---

## 16 Languages — ~73% of World Population

| Flag | Language | Native Name | Speakers |
|------|----------|-------------|----------|
| 🇬🇧 | English | English | 1.5B |
| 🇨🇳 | Chinese | 中文 | 1.18B |
| 🇮🇳 | Hindi | हिन्दी | 609M |
| 🇪🇸 | Spanish | Español | 558M |
| 🇸🇦 | Arabic | العربية | 400M |
| 🇫🇷 | French | Français | 320M |
| 🇷🇺 | Russian | Русский | 255M |
| 🇧🇷 | Portuguese | Português | 250M |
| 🇵🇰 | Urdu | اردو | 230M |
| 🇩🇪 | German | Deutsch | 135M |
| 🇯🇵 | Japanese | 日本語 | 125M |
| 🇮🇷 | Persian/Farsi | فارسی | 110M |
| 🇰🇷 | Korean | 한국어 | 82M |
| 🇹🇷 | Turkish | Türkçe | 88M |
| 🇮🇹 | Italian | Italiano | 67M |
| 🇮🇱 | Hebrew | עברית | 9M |

Arabic, Hebrew, Urdu, and Persian automatically switch to right-to-left layout.

---

## Quick Start

### Requirements
- Docker + Docker Compose

### Deploy

```bash
git clone https://github.com/TemperalTemplar/positive.git
cd positive
cp .env.example .env
# Edit .env with your settings
docker compose up -d
```

Visit `http://localhost:8178`

Default login: `admin` / `positive2026` — **change immediately in Settings.**

### .env Configuration

```env
SECRET_KEY=your-long-random-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,localhost
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
PORT=8178

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=you@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=positive@yourdomain.com

DISCORD_WEBHOOK=
ROCKETCHAT_WEBHOOK=
```

### Reading Reminder Cron (optional)

```bash
0 * * * * docker exec positive_engine python manage.py send_reading_reminders
```

---

## Accessibility

- Full ARIA labels and screen reader support
- Skip to main content link
- Keyboard navigation — Escape closes modals, Tab trapped inside modals
- High contrast mode (HC button)
- Font size cycling — normal / large / extra large (A+ button)
- Minimum 44x44px touch targets

---

## Mobile & PWA

- Responsive hamburger navigation
- Installable on Android and iOS home screen
- Offline support via service worker

---

## Security

- Email verification
- Two-factor authentication (6-digit code, 10-minute expiry)
- Password reset via email
- Rate limiting on registration (5 attempts per hour)
- Full data export as ZIP

---

## User Roles

| Role | Permissions |
|------|------------|
| ARCHITECT | Broadcast, start group sessions, approve registrations |
| PRACTITIONER | Personal entries, library, timers, group participation |
| GUEST | Read-only access to shared content |

---

## Built-in Sample Content

8 texts from multiple traditions included out of the box:
- Box Breathing — 4-4-4-4 Guide
- Morning Intention Setting
- Psalm 23 — The Lord is My Shepherd
- Surah Al-Fatiha — The Opening
- Loving-Kindness Meditation — Metta
- The Serenity Prayer
- Gratitude Journaling — 5-Minute Practice
- Ho'oponopono — Hawaiian Forgiveness Prayer

---

## Contributing Translations

See [TRANSLATING.md](TRANSLATING.md) to add a new language.

---

## Philosophy

Positive is built on the belief that tools for inner life should be sovereign — owned by the people who use them, running on their own hardware, in their own language, free from surveillance and monetization.

Prayer, meditation, gratitude, and intention-setting are ancient human practices that belong to everyone.

---

## License

MIT © 2026 [TemperalTemplar](https://github.com/TemperalTemplar)
