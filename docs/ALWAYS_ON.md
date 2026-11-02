# Always-on server (no Mac required)

Your phone talks to **whatever machine runs the journal API**. That does not have to be your Mac—it must just be **on and reachable** (usually via Tailscale).

| Host | Mac needed? |
|------|-------------|
| Mac + Tailscale Serve (what you use now) | Mac must stay on |
| **Linux VPS** + Docker + Tailscale | Mac can be off |
| Home Raspberry Pi / NUC | Mac can be off |

Audio still never goes to the LLM vendor; only **text** does. The server holds SQLite, Whisper, and exports.

## Recommended: small private VPS (~$5–6/mo)

Examples: Hetzner CX22, DigitalOcean basic, Linode nanode. Pick a region you’re comfortable with.

### 1. Create an Ubuntu 24.04 server

Note its public IP (SSH). Lock down SSH keys; no need to expose port 8000 to the public internet.

### 2. Install Tailscale on the VPS

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Log in with the **same Tailscale account** as your phone.

### 3. Install Docker on the VPS

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
# log out and back in
```

### 4. Deploy the app

On the VPS (or push image from CI later):

```bash
git clone https://github.com/skethini/voice-journal.git
cd voice-journal
cp .env.example .env
nano .env   # LLM_MODEL, LLM_API_KEY, SESSION_SECRET, PASSCODE_HASH, etc.
docker compose up -d --build
```

Data lives in the Docker volume `journal-data` (DB + markdown exports). Back it up with `docker compose exec journal tar czf - /data` or volume snapshots.

### 5. HTTPS for your phone (Tailscale Serve on the VPS)

On the **VPS** (not your Mac):

```bash
sudo tailscale serve --bg --https=443 http://127.0.0.1:8000
tailscale serve status
```

Open the **`https://….ts.net`** URL on your phone (Tailscale on). Bookmark or Add to Home Screen.

**Turn off** Mac Serve when using the VPS so you’re not confused by two URLs:

```bash
# on Mac
/Applications/Tailscale.app/Contents/MacOS/Tailscale serve reset
```

### 6. Optional: migrate data from your Mac

Copy your existing journal to the VPS:

```bash
# on Mac (stop local server first)
tar czf journal-data.tgz -C ~/Projects/voice-journal/server data

# to VPS
scp journal-data.tgz you@vps-ip:~
# on VPS, after first `docker compose up` created the volume:
docker compose down
docker run --rm -v voice-journal_journal-data:/data -v "$HOME":/backup alpine \
  sh -c "cd /data && tar xzf /backup/journal-data.tgz --strip-components=1"
docker compose up -d
```

Adjust paths if your Mac `DATA_DIR` differs.

## What stays the same on the phone

Same PWA, same passcode, same recording flow—only the **HTTPS hostname** changes (VPS MagicDNS name instead of `sumedhas-macbook-air…`).

## What does *not* work

- **Mac asleep/off** with server still only on the Mac → phone dead (fix: move server to VPS).
- **Fully offline LLM on phone** → not in this design; something always-on runs Whisper + API.
- **Public URL without Tailscale** → out of scope for v1; keep using Serve on the tailnet.

## Mac role after migration

Use the Mac only for **development** (`npm run dev` + local uvicorn) if you want. Production traffic goes to the VPS URL.
