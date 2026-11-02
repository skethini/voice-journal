# Render deploy checklist

Render’s dashboard labels differ from generic “runtime” wording. Use this map.

## Option A — New Web Service (manual)

1. Dashboard → **+ New** → **Web Service**
2. Connect **skethini/voice-journal**
3. On the **create** form:

| Field on Render | What to set |
|-----------------|-------------|
| **Name** | `voice-journal` (anything) |
| **Region** | closest to you |
| **Branch** | `main` |
| **Root Directory** | leave **blank** |
| **Language** | **Docker** (not Python — pick Docker even though the app is Python) |
| **Dockerfile Path** | `Dockerfile.cloud` |
| **Instance type** | **Free** |

4. **Do not fill** Build Command or Start Command when Language = Docker (leave blank). Render uses the Dockerfile `CMD`.

5. **Environment** → add variables from `.env.example.cloud` (at minimum `LLM_API_KEY`, `LLM_MODEL`, `PASSCODE_HASH`, `SESSION_SECRET`, `PUBLIC_URL`).

6. Click **Deploy Web Service**.

### If you already created the service as Python

1. Open the service → **Settings** (left sidebar)
2. **Build & Deploy** section → **Edit** next to Language / build settings if available  
   - Some accounts must **delete the service and recreate** with **Language: Docker** — Python services show **Build Command** / **Start Command** instead of Dockerfile Path.
3. Or switch via **Settings → Build & Deploy → Dockerfile Path** only appears when runtime is Docker.

**Sign you picked Python by mistake:** you see `pip install -r requirements.txt` as the build command and no **Dockerfile Path** field.

**Fix:** create a **new** Web Service with **Language: Docker** and `Dockerfile.cloud`.

### After the service exists

**Settings → Build & Deploy**

| Field | Value |
|-------|--------|
| **Root Directory** | empty |
| **Dockerfile Path** | `Dockerfile.cloud` |
| **Docker Command** (under Advanced) | empty unless deploy fails — then `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

**Settings → Health Checks** (if present)

| Field | Value |
|-------|--------|
| **Health Check Path** | `/health` |

**Environment** (left sidebar) → all secrets and `WHISPER_PROVIDER=openai`, etc.

**Manual Deploy** → **Clear build cache & deploy** after GitHub updates.

---

## Option B — Blueprint (uses `render.yaml` in repo)

1. **+ New** → **Blueprint**
2. Connect repo **voice-journal** (must include `render.yaml` on `main`)
3. Render creates the service from the blueprint — less clicking in the form
4. Still add secret env vars in the dashboard when prompted (`LLM_API_KEY`, `PASSCODE_HASH`, …)

---

## Push to GitHub first

Render builds from GitHub. Local fixes don’t apply until `git push origin main`.

Required files on `main`:

- `Dockerfile.cloud`
- `requirements-cloud.txt`
- `requirements.txt`

See `docs/SIMPLE_FREE.md` for passcode hash and phone usage.
