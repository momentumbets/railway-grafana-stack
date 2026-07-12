#!/usr/bin/env sh
set -eu

log() {
  printf '%s %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$*"
}

REPO="${MB_STACK_GRAFANA_CONFIG_REPO:-momentumbets/mb-stack}"
REF="${MB_STACK_GRAFANA_CONFIG_REF:-main}"
SOURCE_PATH="${MB_STACK_GRAFANA_CONFIG_PATH:-grafana/gitops}"
DASH_DEST="${MB_STACK_GRAFANA_DASHBOARDS_DEST:-/var/lib/grafana/dashboards/mb-stack}"
DASH_PROV_DEST="${MB_STACK_GRAFANA_DASHBOARD_PROVISIONING_DEST:-/etc/grafana/provisioning/dashboards}"
ALERT_PROV_DEST="${MB_STACK_GRAFANA_ALERT_PROVISIONING_DEST:-/etc/grafana/provisioning/alerting}"
REQUIRED="${MB_STACK_GRAFANA_CONFIG_REQUIRED:-false}"
TOKEN="${MB_STACK_GRAFANA_CONFIG_TOKEN:-${GITHUB_TOKEN:-}}"
DATA_DIR="${GF_PATHS_DATA:-/var/lib/grafana}"
TMP_DIR="$(mktemp -d "${DATA_DIR%/}/mb-stack-grafana.XXXXXX")"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

fail_or_warn() {
  if [ "$REQUIRED" = "true" ]; then
    log "ERROR: $*"
    exit 1
  fi
  log "WARN: $*"
}

start_grafana() {
  exec "$@"
}

log "Loading Momentum Bets Grafana config from ${REPO}@${REF}:${SOURCE_PATH}"

ZIP_FILE="$TMP_DIR/repo.zip"
API_URL="https://api.github.com/repos/${REPO}/zipball/${REF}"
if [ -n "$TOKEN" ]; then
  if ! curl -fsSL \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer ${TOKEN}" \
    -o "$ZIP_FILE" \
    "$API_URL"; then
    fail_or_warn "failed to download ${REPO}@${REF} with token"
    start_grafana "$@"
  fi
else
  if ! curl -fsSL \
    -H "Accept: application/vnd.github+json" \
    -o "$ZIP_FILE" \
    "$API_URL"; then
    fail_or_warn "failed to download public archive ${REPO}@${REF}; set MB_STACK_GRAFANA_CONFIG_TOKEN or GITHUB_TOKEN if the repo is private"
    start_grafana "$@"
  fi
fi

UNZIP_DIR="$TMP_DIR/unzip"
mkdir -p "$UNZIP_DIR"
if command -v unzip >/dev/null 2>&1; then
  if ! unzip -q "$ZIP_FILE" -d "$UNZIP_DIR"; then
    fail_or_warn "failed to unzip ${REPO}@${REF} archive"
    start_grafana "$@"
  fi
elif command -v python3 >/dev/null 2>&1; then
  if ! python3 - "$ZIP_FILE" "$UNZIP_DIR" <<'PY'
import sys, zipfile
zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])
PY
  then
    fail_or_warn "failed to unzip ${REPO}@${REF} archive with python3"
    start_grafana "$@"
  fi
else
  fail_or_warn "neither unzip nor python3 is available to extract ${REPO}@${REF} archive"
  start_grafana "$@"
fi

ARCHIVE_ROOT="$(find "$UNZIP_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
if [ -z "$ARCHIVE_ROOT" ] || [ ! -d "$ARCHIVE_ROOT/$SOURCE_PATH" ]; then
  fail_or_warn "${SOURCE_PATH} not found in ${REPO}@${REF}"
  start_grafana "$@"
fi

SRC="$ARCHIVE_ROOT/$SOURCE_PATH"
mkdir -p "$DASH_DEST" "$DASH_PROV_DEST" "$ALERT_PROV_DEST"

if [ -d "$SRC/dashboards" ]; then
  rm -rf "$DASH_DEST"
  mkdir -p "$DASH_DEST"
  cp -R "$SRC/dashboards/." "$DASH_DEST/"
  log "Copied dashboards from ${SOURCE_PATH}/dashboards to ${DASH_DEST}"
else
  fail_or_warn "${SOURCE_PATH}/dashboards is missing"
fi

if [ -d "$SRC/provisioning/dashboards" ]; then
  cp -R "$SRC/provisioning/dashboards/." "$DASH_PROV_DEST/"
  log "Copied dashboard provisioning files to ${DASH_PROV_DEST}"
else
  fail_or_warn "${SOURCE_PATH}/provisioning/dashboards is missing"
fi

if [ -d "$SRC/provisioning/alerting" ]; then
  cp -R "$SRC/provisioning/alerting/." "$ALERT_PROV_DEST/"
  log "Copied alert provisioning files to ${ALERT_PROV_DEST}"
else
  fail_or_warn "${SOURCE_PATH}/provisioning/alerting is missing"
fi

log "Momentum Bets Grafana GitOps config load complete"
start_grafana "$@"
