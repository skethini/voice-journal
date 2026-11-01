# Private Voice Journal

A private, phone-first voice journal. Audio is transcribed on **your** server; only text goes to the LLM API you configure.

## Architecture

```
Phone (PWA) ── Tailscale / HTTPS ──► FastAPI + faster-whisper + SQLite
                                      └── LLM API (text only)
```

## Quick start (development)

### Server

```bash
cd server
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env   # set LLM_MODEL, LLM_API_KEY, optional PASSCODE_HASH
export LLM_PROVIDER=mock  # or openai / openrouter
uvicorn app.main:app --app-dir . --reload --host 127.0.0.1 --port 8000
```

Generate a passcode hash (optional):

```python
from app.auth import hash_passcode
print(hash_passcode("your-passcode"))
```

Set `PASSCODE_HASH=` in `.env`.

Requires **ffmpeg** on `PATH` for transcription.

### Client

```bash
cd client
npm install
npm run dev
```

Vite proxies `/api` → `http://127.0.0.1:8000`.

Build for production and serve static files behind the same Tailscale host as the API (or configure `VITE_API_BASE`).

## Production (Tailscale)

1. Enable full-disk encryption on the host.
2. Install Tailscale on the server and your phone.
3. Bind the API to the Tailscale IP only, e.g. in `.env`: `HOST=100.x.y.z`.
4. Serve HTTPS with [Tailscale Serve](https://tailscale.com/kb/1312/serve):

   ```bash
   tailscale serve https / http://127.0.0.1:8000
   ```

5. Do **not** expose a public port on the internet.

### systemd (example)

```ini
[Unit]
Description=Voice Journal API
After=network.target

[Service]
WorkingDirectory=/path/to/voice-journal/server
EnvironmentFile=/path/to/voice-journal/.env
ExecStart=/path/to/voice-journal/server/.venv/bin/uvicorn app.main:app --host 100.x.y.z --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## Backups

Set `AGE_RECIPIENT` to your age public key. A nightly job writes `journal-YYYYMMDD.tar.gz.age` under `BACKUP_DIR`.

Restore:

```bash
age -d -i key.txt backup.age | tar xzf -
```

## Configuration

| Variable | Purpose |
|----------|---------|
| `LLM_PROVIDER` | `openai`, `openrouter`, or `mock` (tests) |
| `LLM_MODEL` | Model id (required for real providers) |
| `LLM_API_KEY` | API key |
| `WHISPER_MODEL` | Default `small` |
| `DATA_DIR` | SQLite + markdown exports |
| `KEEP_AUDIO` | Default `false` — delete after transcription |
| `PASSCODE_HASH` | Argon2 hash for app passcode |
| `BACKUP_DIR` | Encrypted backup destination |
| `AGE_RECIPIENT` | age recipient for backups |

## Threat model (short)

Protects against vendor access to audio (audio stays local), casual network snooping (Tailscale + HTTPS), and undisciplined logging (transcripts are not logged).

Does **not** protect against a compromised host, malicious admin on the machine, or a determined nation-state attacker.

Verify your LLM provider’s data retention and training policy before sending real journal text.

## Tests

```bash
cd server
LLM_PROVIDER=mock pytest
```

## Milestones

See the implementation spec in project docs — pipeline, analysis, guidance/prompts, threads/synthesis, ask, and hardening are scaffolded with acceptance criteria to validate on your hardware (Whisper + real LLM).

## Manual recording checklist

- [ ] iOS Safari: record → upload → transcript appears
- [ ] Android Chrome: record → upload → transcript appears
- [ ] Offline: record → queue → online → upload succeeds
- [ ] PWA: Add to Home Screen, launch standalone
