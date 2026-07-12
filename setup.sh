#!/usr/bin/env bash
set -euo pipefail

# ── Colors ────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERR]${NC}   $*"; }

# ── Resolve project root ──────────────────────────────────────────
ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT/backend"
FRONTEND_DIR="$ROOT/frontend"

# ── Trap: cleanup on exit ─────────────────────────────────────────
cleanup() {
    info "Shutting down..."
    [ -n "${BACKEND_PID:-}" ] && kill "$BACKEND_PID" 2>/dev/null || true
    [ -n "${FRONTEND_PID:-}" ] && kill "$FRONTEND_PID" 2>/dev/null || true
    wait 2>/dev/null
    ok "Stopped."
}
trap cleanup EXIT INT TERM

# ── Usage ─────────────────────────────────────────────────────────
usage() {
    cat <<EOF
Usage: $0 [--install-only] [--backend-only] [--frontend-only]

  (no flags)        Install deps + start both backend (8000) and frontend (5173)
  --install-only    Only install deps, don't start servers
  --backend-only    Only start backend on port 8000
  --frontend-only   Only start frontend dev server on port 5173
EOF
    exit 0
}

INSTALL_ONLY=false; BACKEND_ONLY=false; FRONTEND_ONLY=false
for arg in "$@"; do
    case "$arg" in
        --help|-h) usage ;;
        --install-only) INSTALL_ONLY=true ;;
        --backend-only) BACKEND_ONLY=true ;;
        --frontend-only) FRONTEND_ONLY=true ;;
        *) err "Unknown flag: $arg"; usage ;;
    esac
done

# ── Prerequisite checks ───────────────────────────────────────────
info "Checking prerequisites..."

command -v python3 >/dev/null 2>&1 || { err "python3 not found. Install Python >= 3.13."; exit 1; }
ok "python3 $(python3 --version | cut -d' ' -f2)"

command -v uv >/dev/null 2>&1 || { err "uv not found. Install: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }
ok "uv $(uv --version | cut -d' ' -f2)"

if [ "$FRONTEND_ONLY" = false ] || [ "$BACKEND_ONLY" = false ]; then
    command -v node >/dev/null 2>&1 || { err "node not found. Install Node >= 22."; exit 1; }
    ok "node $(node --version)"

    command -v pnpm >/dev/null 2>&1 || { err "pnpm not found. Install: npm install -g pnpm"; exit 1; }
    ok "pnpm $(pnpm --version)"
fi

# ── Install backend deps ──────────────────────────────────────────
if [ "$FRONTEND_ONLY" = false ]; then
    echo ""
    info "Installing backend dependencies (uv sync)..."
    cd "$BACKEND_DIR"
    uv sync
    ok "Backend deps ready."
fi

# ── Install frontend deps ─────────────────────────────────────────
if [ "$BACKEND_ONLY" = false ]; then
    echo ""
    info "Installing frontend dependencies (pnpm install)..."
    cd "$FRONTEND_DIR"
    pnpm install --frozen-lockfile
    ok "Frontend deps ready."
fi

# ── Stop here if --install-only ───────────────────────────────────
if [ "$INSTALL_ONLY" = true ]; then
    echo ""
    ok "Installation complete. Run '$0' to start servers."
    exit 0
fi

# ── Start backend ─────────────────────────────────────────────────
if [ "$FRONTEND_ONLY" = false ]; then
    echo ""
    info "Starting backend on http://localhost:8000 ..."
    cd "$BACKEND_DIR"
    PYTHONPATH=. uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    ok "Backend PID: $BACKEND_PID"
fi

# ── Start frontend ────────────────────────────────────────────────
if [ "$BACKEND_ONLY" = false ]; then
    echo ""
    info "Starting frontend on http://localhost:5173 ..."
    cd "$FRONTEND_DIR"
    pnpm dev &
    FRONTEND_PID=$!
    ok "Frontend PID: $FRONTEND_PID"
fi

# ── Wait ──────────────────────────────────────────────────────────
echo ""
info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
info "  Backend  → http://localhost:8000"
info "  Frontend → http://localhost:5173"
info "  Health   → http://localhost:8000/health"
info "  Press Ctrl+C to stop all servers."
info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

wait
