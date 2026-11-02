#!/usr/bin/env bash
# Build PWA + print Tailscale Serve steps for phone access.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

TAILSCALE=""
if command -v tailscale >/dev/null 2>&1; then
  TAILSCALE=tailscale
elif [[ -x /Applications/Tailscale.app/Contents/MacOS/Tailscale ]]; then
  TAILSCALE=/Applications/Tailscale.app/Contents/MacOS/Tailscale
fi

echo "==> Building client (API same-origin for Tailscale HTTPS)..."
cd "$ROOT/client"
VITE_API_BASE= npm run build

echo ""
echo "==> Start the server (keep this running):"
echo "    cd $ROOT/server"
echo "    source .venv/bin/activate"
echo "    PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port 8000"
echo ""
echo "    (Use 127.0.0.1 only — Tailscale Serve proxies to it; not exposed on public internet.)"
echo ""

if [[ -z "$TAILSCALE" ]]; then
  echo "==> Tailscale CLI not found."
  echo "    1. Install Tailscale: https://tailscale.com/download/mac"
  echo "    2. Sign in on Mac and on your phone (same account)."
  echo "    3. Re-run: $0"
  exit 0
fi

if ! "$TAILSCALE" status >/dev/null 2>&1; then
  echo "==> Open the Tailscale app and log in, then re-run this script."
  exit 1
fi

TS_IP="$("$TAILSCALE" ip -4 2>/dev/null | head -1 || true)"
DNS="$("$TAILSCALE" status --json 2>/dev/null | python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
    self=d.get('Self',{})
    dns=self.get('DNSName','')
    print(dns.rstrip('.'))
except Exception:
    pass
" 2>/dev/null || true)"

echo "==> Tailscale node IP: ${TS_IP:-unknown}"
echo ""
echo "==> Enable HTTPS on your tailnet (run once, in a second terminal):"
echo "    $TAILSCALE serve --bg --https=443 http://127.0.0.1:8000"
echo ""
echo "    Or foreground (logs in terminal):"
echo "    $TAILSCALE serve --https=443 http://127.0.0.1:8000"
echo ""
echo "==> On your phone (Tailscale connected, same account):"
if [[ -n "$DNS" ]]; then
  echo "    Open: https://${DNS}/"
else
  echo "    Open: https://<your-machine-name>.<tailnet>.ts.net/"
  echo "    (Find name in Tailscale app → this Mac → DNS name)"
fi
echo ""
echo "    Allow microphone when prompted."
echo "    Share → Add to Home Screen (optional PWA install)."
echo ""
echo "==> To stop Serve later:"
echo "    $TAILSCALE serve reset"
