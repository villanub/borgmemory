#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Borg — one-command installer
# Usage:  bash install.sh
#         BORG_HOME=/custom/path bash install.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── colours ──────────────────────────────────────────────────────────────────
if [[ -t 1 ]]; then
  BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'
  GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'
else
  BOLD=''; DIM=''; RESET=''; GREEN=''; YELLOW=''; RED=''; CYAN=''
fi

# ── helpers ───────────────────────────────────────────────────────────────────
step()  { echo -e "\n${BOLD}${CYAN}▸ ${*}${RESET}"; }
ok()    { echo -e "  ${GREEN}✓${RESET}  ${*}"; }
warn()  { echo -e "  ${YELLOW}⚠${RESET}  ${*}"; }
die()   { echo -e "\n  ${RED}✗  ERROR:${RESET} ${*}" >&2; exit 1; }
confirm() {
  local prompt="${1}"
  read -r -p "  ${prompt} [y/N] " reply
  [[ "${reply,,}" == "y" ]]
}

# ── banner ────────────────────────────────────────────────────────────────────
echo -e "${BOLD}"
echo '┌────────────────────────────────────────────────────────┐'
echo '│                  Borg — Installer                      │'
echo '│         Self-hosted AI memory for your projects        │'
echo '└────────────────────────────────────────────────────────┘'
echo -e "${RESET}"

# ═════════════════════════════════════════════════════════════════════════════
# STEP 1 — Detect OS / architecture
# ═════════════════════════════════════════════════════════════════════════════
step "1/8  Detecting platform"

OS=""
ARCH=""
case "$(uname -s)" in
  Darwin) OS="macos" ;;
  Linux)
    if grep -qi microsoft /proc/version 2>/dev/null; then
      OS="wsl"
    else
      OS="linux"
    fi
    ;;
  MINGW*|MSYS*|CYGWIN*) OS="windows" ;;
  *) die "Unsupported operating system: $(uname -s)" ;;
esac

case "$(uname -m)" in
  arm64|aarch64) ARCH="arm64" ;;
  x86_64|amd64)  ARCH="amd64" ;;
  *) die "Unsupported architecture: $(uname -m)" ;;
esac

ok "Platform: ${OS} / ${ARCH}"

if [[ "${OS}" == "windows" ]]; then
  echo ""
  echo "  Windows (native) is not directly supported."
  echo "  Please install WSL 2 and re-run this script inside it:"
  echo "    https://learn.microsoft.com/en-us/windows/wsl/install"
  exit 1
fi

# ═════════════════════════════════════════════════════════════════════════════
# STEP 2 — Ensure Docker is available
# ═════════════════════════════════════════════════════════════════════════════
step "2/8  Checking Docker"

install_docker_linux() {
  echo -e "  ${DIM}Docker not found — installing Docker Engine via get.docker.com …${RESET}"
  curl -fsSL https://get.docker.com | sh
  # Add current user to docker group so we can use Docker without sudo going forward.
  if id -nG | grep -qw docker; then
    ok "Already in docker group"
  else
    sudo usermod -aG docker "${USER}" 2>/dev/null || true
    warn "Added ${USER} to the 'docker' group."
    warn "You may need to log out and back in for group membership to take effect."
    warn "For this session, the installer will use 'sudo docker' if needed."
  fi
}

install_docker_macos() {
  local dmg_url
  if [[ "${ARCH}" == "arm64" ]]; then
    dmg_url="https://desktop.docker.com/mac/main/arm64/Docker.dmg"
  else
    dmg_url="https://desktop.docker.com/mac/main/amd64/Docker.dmg"
  fi

  local tmp_dmg="/tmp/Docker.dmg"
  echo -e "  ${DIM}Downloading Docker Desktop (${ARCH}) …${RESET}"
  curl -fL --progress-bar -o "${tmp_dmg}" "${dmg_url}"

  echo ""
  echo -e "  ${DIM}Mounting Docker Desktop installer …${RESET}"
  hdiutil attach "${tmp_dmg}" -quiet

  echo ""
  echo -e "  ${YELLOW}A Finder window may have opened with Docker Desktop."
  echo -e "  Drag Docker to your Applications folder and start it.${RESET}"
  echo ""
  read -r -p "  Press Enter once Docker Desktop is running and shows the whale icon … "

  hdiutil detach /Volumes/Docker 2>/dev/null || true
  rm -f "${tmp_dmg}"
}

DOCKER_CMD="docker"

if command -v docker &>/dev/null; then
  ok "Docker found: $(docker --version)"
else
  case "${OS}" in
    linux|wsl)
      install_docker_linux
      # Refresh docker command — might need sudo in this session
      if ! docker info &>/dev/null 2>&1; then
        DOCKER_CMD="sudo docker"
        warn "Using 'sudo docker' for this session"
      fi
      ;;
    macos)
      install_docker_macos
      ;;
  esac

  # Final check
  if ! ${DOCKER_CMD} info &>/dev/null 2>&1; then
    die "Docker is installed but not running.\nPlease start Docker and re-run this installer."
  fi
  ok "Docker is ready"
fi

# Verify Docker is actually responsive (it could be installed but not running)
if ! ${DOCKER_CMD} info &>/dev/null 2>&1; then
  die "Docker daemon is not running.\nPlease start Docker Desktop (macOS) or 'sudo systemctl start docker' (Linux) and re-run."
fi

# Prefer 'docker compose' (v2) over 'docker-compose' (v1)
COMPOSE_CMD=""
if ${DOCKER_CMD} compose version &>/dev/null 2>&1; then
  COMPOSE_CMD="${DOCKER_CMD} compose"
elif command -v docker-compose &>/dev/null; then
  COMPOSE_CMD="docker-compose"
  warn "Using legacy docker-compose v1; consider upgrading to Docker Compose v2"
else
  die "Docker Compose is not available. Install it and re-run:\n  https://docs.docker.com/compose/install/"
fi
ok "Compose command: ${COMPOSE_CMD}"

# ═════════════════════════════════════════════════════════════════════════════
# STEP 3 — Create install directory
# ═════════════════════════════════════════════════════════════════════════════
step "3/8  Setting up install directory"

INSTALL_DIR="${BORG_HOME:-${HOME}/.borg}"
export BORG_HOME="${INSTALL_DIR}"

if [[ -d "${INSTALL_DIR}" ]]; then
  ok "Install directory already exists: ${INSTALL_DIR}"
else
  mkdir -p "${INSTALL_DIR}"
  ok "Created: ${INSTALL_DIR}"
fi

mkdir -p "${INSTALL_DIR}/migrations"

# ═════════════════════════════════════════════════════════════════════════════
# STEP 4 — Download docker-compose file
# ═════════════════════════════════════════════════════════════════════════════
step "4/8  Downloading Borg configuration"

GITHUB_RAW="https://raw.githubusercontent.com/villanub/borgmemory/main"
COMPOSE_DEST="${INSTALL_DIR}/docker-compose.yml"

if [[ -f "${COMPOSE_DEST}" ]]; then
  warn "docker-compose.yml already exists — keeping existing file"
  warn "  (${COMPOSE_DEST})"
else
  echo -e "  ${DIM}Fetching docker-compose.basic.yml …${RESET}"
  if curl -fsSL "${GITHUB_RAW}/docker-compose.basic.yml" -o "${COMPOSE_DEST}"; then
    ok "Downloaded docker-compose.yml"
  else
    die "Failed to download docker-compose.basic.yml from GitHub.\nCheck your internet connection or the repo URL."
  fi
fi

# ═════════════════════════════════════════════════════════════════════════════
# STEP 5 — Download migration files
# ═════════════════════════════════════════════════════════════════════════════
step "5/8  Downloading database migrations"

MIGRATIONS=(
  "migrations/001_initial_schema.sql"
  "migrations/002_amendments.sql"
)

for migration in "${MIGRATIONS[@]}"; do
  dest="${INSTALL_DIR}/${migration}"
  filename="$(basename "${migration}")"
  if [[ -f "${dest}" ]]; then
    ok "${filename} already present — skipping"
  else
    echo -e "  ${DIM}Fetching ${filename} …${RESET}"
    if curl -fsSL "${GITHUB_RAW}/${migration}" -o "${dest}"; then
      ok "Downloaded ${filename}"
    else
      die "Failed to download ${migration}.\nCheck your internet connection or the repo URL."
    fi
  fi
done

# ═════════════════════════════════════════════════════════════════════════════
# STEP 6 — Configure environment
# ═════════════════════════════════════════════════════════════════════════════
step "6/8  Configuring environment"

ENV_FILE="${INSTALL_DIR}/.env"

if [[ -f "${ENV_FILE}" ]]; then
  warn ".env already exists — keeping existing credentials"
  warn "  (${ENV_FILE})"
  warn "  Delete it and re-run to reconfigure."
else
  echo ""
  echo -e "  ${BOLD}An OpenAI API key is required for Borg's embedding and chat features.${RESET}"
  echo -e "  ${DIM}Get one at: https://platform.openai.com/api-keys${RESET}"
  echo ""

  OPENAI_API_KEY=""
  while [[ -z "${OPENAI_API_KEY}" ]]; do
    read -r -p "  Paste your OpenAI API key: " OPENAI_API_KEY
    OPENAI_API_KEY="${OPENAI_API_KEY// /}"   # strip accidental spaces
    if [[ -z "${OPENAI_API_KEY}" ]]; then
      warn "API key cannot be empty. Please try again."
    fi
  done

  cat > "${ENV_FILE}" <<EOF
# Borg — environment configuration
# Generated by install.sh on $(date -u '+%Y-%m-%dT%H:%M:%SZ')
OPENAI_API_KEY=${OPENAI_API_KEY}
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o-mini
EOF

  chmod 600 "${ENV_FILE}"
  ok ".env written (mode 600)"
fi

# ═════════════════════════════════════════════════════════════════════════════
# STEP 7 — Pull images, start services, wait for health
# ═════════════════════════════════════════════════════════════════════════════
step "7/8  Starting Borg services"

cd "${INSTALL_DIR}"

echo -e "  ${DIM}Pulling Docker images (this may take a minute on first run) …${RESET}"
${COMPOSE_CMD} --env-file "${ENV_FILE}" pull

echo -e "  ${DIM}Starting services …${RESET}"
${COMPOSE_CMD} --env-file "${ENV_FILE}" up -d

echo ""
echo -e "  ${DIM}Waiting for Borg to become healthy (up to 60 s) …${RESET}"

HEALTH_URL="http://localhost:8080/health"
TIMEOUT=60
ELAPSED=0
HEALTHY=false

while [[ ${ELAPSED} -lt ${TIMEOUT} ]]; do
  if curl -sf "${HEALTH_URL}" | grep -q '"ok"' 2>/dev/null; then
    HEALTHY=true
    break
  fi
  printf "  ."
  sleep 2
  ELAPSED=$(( ELAPSED + 2 ))
done

echo ""

if [[ "${HEALTHY}" == "true" ]]; then
  ok "Borg is healthy at ${HEALTH_URL}"
else
  warn "Borg did not respond within ${TIMEOUT}s."
  warn "Services may still be starting up. Check with:"
  warn "  ${COMPOSE_CMD} -f ${COMPOSE_DEST} logs -f"
  warn "Re-run this script once Docker is healthy to re-check."
fi

# ═════════════════════════════════════════════════════════════════════════════
# STEP 8 — Install the Borg CLI (pipx preferred, pip fallback)
# ═════════════════════════════════════════════════════════════════════════════
step "8/8  Installing the Borg CLI"

BORG_PKG_SPEC="git+https://github.com/villanub/borgmemory.git"

if command -v pipx &>/dev/null; then
  if pipx list 2>/dev/null | grep -q "borg"; then
    pipx upgrade borg || pipx reinstall borg || true
  else
    pipx install "${BORG_PKG_SPEC}"
  fi
  ok "Borg CLI installed via pipx"
elif command -v pip3 &>/dev/null || command -v pip &>/dev/null; then
  PIP_CMD=$(command -v pip3 || command -v pip)
  if ${PIP_CMD} install --user "${BORG_PKG_SPEC}" 2>/dev/null; then
    ok "Borg CLI installed via ${PIP_CMD} --user"
    warn "Make sure ~/.local/bin is on your PATH (or use pipx for better isolation)"
  else
    warn "Could not install the Borg CLI automatically."
    warn "Install it manually with:  pipx install ${BORG_PKG_SPEC}"
  fi
else
  warn "Python pip/pipx not found — skipping CLI install."
  warn "Install the CLI with:  pipx install ${BORG_PKG_SPEC}"
fi

# ═════════════════════════════════════════════════════════════════════════════
# Success banner
# ═════════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${BOLD}${GREEN}"
echo '┌────────────────────────────────────────────────────────┐'
echo '│              Borg is installed and running!            │'
echo '└────────────────────────────────────────────────────────┘'
echo -e "${RESET}"
echo -e "  ${BOLD}Next steps:${RESET}"
echo ""
echo -e "  ${CYAN}1.${RESET}  Initialise Borg in a project:"
echo -e "       ${DIM}cd your-project && borg init${RESET}"
echo ""
echo -e "  ${CYAN}2.${RESET}  Start using memory:"
echo -e "       ${DIM}borg learn 'Just set up Borg'${RESET}"
echo ""
echo -e "  ${DIM}Config & data live in: ${INSTALL_DIR}${RESET}"
echo -e "  ${DIM}API:                   http://localhost:8080${RESET}"
echo -e "  ${DIM}Docs:                  http://localhost:8080/docs${RESET}"
echo ""
