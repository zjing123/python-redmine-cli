#!/usr/bin/env bash
# install.sh — One-command installer for redmine-cli
#
# Usage:
#   curl -LsSf https://raw.githubusercontent.com/zjing123/python-redmine-cli/main/install.sh | sh
#   # or for private repos (SSH):
#   GIT_PROTO=ssh sh install.sh
#
# Environment variables:
#   GIT_PROTO    — "https" (default) or "ssh"
#   GITHUB_REPO  — Full repo URL override (e.g. git@github.com:user/repo.git)
set -euo pipefail

REPO_NAME="zjing123/python-redmine-cli"
GIT_PROTO="${GIT_PROTO:-https}"
GITHUB_REPO="${GITHUB_REPO:-}"

BOLD='\033[1m'
GREEN='\033[32m'
RED='\033[31m'
YELLOW='\033[33m'
RESET='\033[0m'

info()  { printf "${GREEN}✓${RESET} %s\n" "$*"; }
warn()  { printf "${YELLOW}!${RESET} %s\n" "$*"; }
error() { printf "${RED}✗${RESET} %s\n" "$*" >&2; }

# ── Step 1: Ensure uv is installed ────────────────────────────────
ensure_uv() {
    if command -v uv &>/dev/null; then
        info "uv already installed: $(uv --version)"
        return
    fi

    warn "uv not found, installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Source the env so uv is on PATH in this shell
    if [ -f "$HOME/.local/bin/env" ] && [ -z "${UV_ENV_SOURCED:-}" ]; then
        # shellcheck disable=SC1091
        . "$HOME/.local/bin/env"
        export UV_ENV_SOURCED=1
    fi

    # Fallback: add common uv locations to PATH
    for dir in "$HOME/.local/bin" "$HOME/.cargo/bin"; do
        case ":$PATH:" in
            *":$dir:"*) ;;
            *) export PATH="$dir:$PATH" ;;
        esac
    done

    if ! command -v uv &>/dev/null; then
        error "uv installation failed. Please install manually: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi

    info "uv installed: $(uv --version)"
}

# ── Step 2: Build the install URL ─────────────────────────────────
build_install_url() {
    if [ -n "$GITHUB_REPO" ]; then
        echo "git+$GITHUB_REPO"
        return
    fi

    case "$GIT_PROTO" in
        ssh)  echo "git+ssh://git@github.com/${REPO_NAME}.git" ;;
        *)    echo "git+https://github.com/${REPO_NAME}.git" ;;
    esac
}

# ── Step 3: Install or upgrade redmine-cli ────────────────────────
install_cli() {
    local url
    url="$(build_install_url)"

    if command -v redmine-cli &>/dev/null; then
        warn "redmine-cli already installed, upgrading..."
        uv tool install --force "$url"
    else
        info "Installing redmine-cli from ${url} ..."
        uv tool install "$url"
    fi
}

# ── Step 4: Verify ────────────────────────────────────────────────
verify() {
    if ! command -v redmine-cli &>/dev/null; then
        # Maybe not on PATH yet — try common locations
        for dir in "$HOME/.local/bin"; do
            case ":$PATH:" in
                *":$dir:"*) ;;
                *) export PATH="$dir:$PATH" ;;
            esac
        done
    fi

    if command -v redmine-cli &>/dev/null; then
        info "redmine-cli installed successfully!"
        printf "  %s\n\n" "$(redmine-cli --help | head -1)"
    else
        error "redmine-cli not found on PATH after install."
        echo "  You may need to restart your shell or run:" >&2
        echo "    export PATH=\"\$HOME/.local/bin:\$PATH\"" >&2
        exit 1
    fi
}

# ── Main ──────────────────────────────────────────────────────────
main() {
    printf "\n${BOLD}── redmine-cli installer ──${RESET}\n\n"

    ensure_uv
    install_cli
    verify

    info "Next step: redmine-cli config set --url <your-redmine-url> --api-key <your-key>"
}

main "$@"
