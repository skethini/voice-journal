# Simple & free-ish cloud setup

You wanted **less hassle than Tailscale + Mac**, and **“reasonably private”** (not maximum paranoia). This mode trades some privacy for simplicity.

## What changes

| | **Home Mac / VPS (original)** | **Cloud mode (this doc)** |
|--|-------------------------------|---------------------------|
| Server | Your hardware | Render / similar (~**$0** free tier) |
| Audio transcription | Stays on your machine | **OpenAI Whisper API** (audio sent to OpenAI) |
| Embeddings | Local model | **OpenAI embeddings API** (text only) |
| Journal analysis | OpenAI (text) | Same |
| Who can open the app | Tailscale only | **Anyone with URL** → use a **passcode** |
| Mac must be on | Yes (unless VPS) | **No** |

**Still reasonable for many people:** HTTPS, passcode lock, no public social features, obscure URL. **Not** “audio never leaves my hardware.”

**Cost:** Render free tier is **$0** but sleeps when idle (first open can take ~30s). OpenAI charges small amounts for Whisper + chat (often a few cents per entry).

---

## One-time setup (~10 minutes)

### 1. Passcode hash (on your Mac)

```bash
cd ~/Projects/voice-journal/server
source .venv/bin/activate
PYTHONPATH=. python scripts/hash_passcode.py 'pick-a-long-passcode'
```

Copy the output → you'll paste as `PASSCODE_HASH`.

### 2. Deploy on Render (free)

1. Push this repo to GitHub (you already have `skethini/voice-journal`).
2. Go to [render.com](https://render.com) → sign up → **New +** → **Web Service**.
3. Connect **voice-journal** repo.
4. Settings:
   - **Root directory:** leave **empty** (repo root, not `server`)
   - **Language:** Docker  
   - **Dockerfile path:** `Dockerfile.cloud`  
   - **Plan:** Free  
5. **Environment variables** (from `.env.example.cloud`):

   | Key | Value |
   |-----|--------|
   | `LLM_API_KEY` | your OpenAI key |
   | `LLM_MODEL` | `gpt-4o-mini` |
   | `WHISPER_PROVIDER` | `openai` |
   | `EMBED_PROVIDER` | `openai` |
   | `WHISPER_MODEL` | `whisper-1` |
   | `PASSCODE_HASH` | from step 1 |
   | `SESSION_SECRET` | long random string |
   | `PUBLIC_URL` | `https://YOUR-SERVICE.onrender.com` (fill after first deploy) |

6. **Create Web Service** → wait for deploy → copy your `https://….onrender.com` URL.
7. Update `PUBLIC_URL` in Render env to that URL → redeploy if needed.

### 3. Phone

1. Safari → your `https://….onrender.com` URL (cellular is fine).
2. Enter **passcode** on first visit.
3. Allow **microphone** → record.
4. **Add to Home Screen** if you want.

**Turn off Mac Tailscale Serve** if you’re fully switching:

```bash
/Applications/Tailscale.app/Contents/MacOS/Tailscale serve reset
```

---

## Port scan timeout / “bind to 0.0.0.0”

Render’s load balancer must reach your app on **`0.0.0.0:$PORT`**, not `127.0.0.1`.

| Mistake | Fix |
|---------|-----|
| **Dockerfile path** is `Dockerfile` (home/Tailscale image binds **127.0.0.1**) | Set **Dockerfile path** to **`Dockerfile.cloud`** |
| **Start command** / **Docker command** overrides with `--host 127.0.0.1` | **Clear** start/docker command (use image default) |
| Python runtime start command from README | Use Docker, or `--host 0.0.0.0 --port $PORT` |

Correct docker command if you must override:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

(WITH `PYTHONPATH=/app` and working directory `/app` — prefer empty override and `Dockerfile.cloud`.)

---

Usually one of these:

1. **Runtime is Python, not Docker** → switch to **Docker** and set **Dockerfile path** to `Dockerfile.cloud`, **or** pull latest repo (includes root `requirements.txt` for Python builds).
2. **Root directory** is set to `server` → clear it (leave blank so paths like `server/requirements-cloud.txt` resolve).
3. **Start command** runs `pip install -r requirements.txt` from the wrong folder → leave start command empty for Docker.

---

- **Sleep:** Render free spins down after ~15 minutes idle. First tap may be slow; recording still works after wake.
- **Disk:** Free tier storage can **reset on redeploy**. Fine for trying; for years of entries use Render paid disk or export zip periodically from Settings.
- **OpenAI:** Audio goes to OpenAI for transcription; check their [API data policy](https://openai.com/policies).

---

## Stay on local privacy but $0 forever

If you want **audio on your own box** and no monthly fee, use **Oracle Cloud Always Free** (VPS) with the main `Dockerfile` + Tailscale — see `docs/ALWAYS_ON.md`. Setup is harder than Render.

---

## Switch back to local Whisper on Mac

In `.env`:

```env
WHISPER_PROVIDER=local
EMBED_PROVIDER=local
WHISPER_MODEL=small
```

Use `server/requirements.txt` (includes faster-whisper). No code fork needed.
