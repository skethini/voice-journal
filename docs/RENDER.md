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

---

## Port scan timeout (“bind to 0.0.0.0?”)

Render’s proxy must hit **`0.0.0.0:$PORT`**. If the app only listens on **`127.0.0.1`**, deploy fails with a port scan timeout.

| Cause | Fix |
|-------|-----|
| **Dockerfile path** = `Dockerfile` (home server image — localhost only) | Set **`Dockerfile.cloud`** |
| **Docker command** / **Start command** uses `127.0.0.1` | **Clear** the override |
| Python runtime with README dev command | Switch to **Docker** + `Dockerfile.cloud` |

**Settings → Build & Deploy:** Dockerfile path **`Dockerfile.cloud`**, Docker command **empty**.

Push latest `main` (includes `scripts/docker-start-render.sh` in the cloud image), then **Clear build cache & deploy**.

---

## Entries disappeared after redeploy

Render’s **free** web service disk is **ephemeral**: each deploy or restart can wipe `/data`, including `journal.db`.

| Fix | What to do |
|-----|------------|
| **Persistent disk (recommended)** | Upgrade to **Starter** (or higher), attach a disk mounted at **`/data`**, set **`PERSISTENT_DISK=true`**. The repo’s `render.yaml` blueprint includes this. |
| **Backups** | In the app, **Settings → Download full backup (zip)** after important entries. Restore by replacing `journal.db` on a self-hosted copy or keep archives in iCloud/Drive. |
| **In-app warning** | If `RENDER` is set without `PERSISTENT_DISK`, Settings shows a red alert explaining the risk. |

After attaching a disk, redeploy once and download a backup so you have a copy outside Render too.

### Automatic server-side backups (built in)

With **`AUTO_BACKUP=true`** (default):

| When | What |
|------|------|
| After each analyzed entry | Refreshes **`DATA_DIR/backups/journal-latest.zip`** (DB + markdown) |
| Every night (~3am server time) | Adds a **dated** zip; old dated zips pruned after **`BACKUP_RETAIN_DAYS`** (default 14) |
| On server start | Refreshes `journal-latest.zip` if the DB exists |

Backups live under **`/data/backups`** when `DATA_DIR=/data` on a **persistent disk** — they survive redeploys like the DB.

On **ephemeral** free tier, automatic backups still help until the next wipe, but you need **Settings → Download full backup** (or sync zips off-server) for true “always” safety. Optional **`AGE_RECIPIENT`** adds encrypted nightly archives (requires `age` on the server).
