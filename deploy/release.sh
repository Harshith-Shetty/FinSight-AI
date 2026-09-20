#!/usr/bin/env bash
set -Eeuo pipefail
cd -- "$(dirname -- "$0")"
umask 077
exec 9>"../deployment.lock"
flock -n 9 || { echo "Another deployment is in progress." >&2; exit 1; }
chmod 600 app.env release.env
set -a
source ./release.env
set +a
: "${SERVICE_IMAGE:?}" "${UPLOADS_VOLUME:?}" "${COMPOSE_PROJECT_NAME:?}"
case "${SERVICE:?}" in api|worker) ;; *) echo "Invalid service" >&2; exit 1 ;; esac
docker volume inspect "$UPLOADS_VOLUME" >/dev/null
# Preserve the established Compose project and uploaded documents.
for container in finsight-api finsight-worker; do
if docker inspect "$container" >/dev/null 2>&1; then
  existing_project=$(docker inspect -f '{{index .Config.Labels "com.docker.compose.project"}}' "$container")
  existing_volume=$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/app/uploads"}}{{.Name}}{{end}}{{end}}' "$container")
  [[ "$existing_project" == "$COMPOSE_PROJECT_NAME" && "$existing_volume" == "$UPLOADS_VOLUME" ]] ||
    { echo "Project or uploads volume does not match the existing container. Deployment stopped." >&2; exit 1; }
fi
done
compose=(docker compose --env-file release.env -p "$COMPOSE_PROJECT_NAME" -f compose.yml)
"${compose[@]}" config --quiet
"${compose[@]}" pull "$SERVICE"
# Validate without including Pydantic input values in logs.
"${compose[@]}" run --rm --no-deps "$SERVICE" python -c '
import sys
try:
    from app.core.config import settings
except Exception:
    print("Runtime configuration is invalid; check Azure settings", file=sys.stderr)
    sys.exit(1)
'
# API owns migrations. Worker-only releases never change the database schema.
if [[ "$SERVICE" == api ]]; then
  "${compose[@]}" run --rm --no-deps api alembic upgrade head
fi
# No down, volume removal, prune or source-checkout reset.
"${compose[@]}" up -d --no-deps --no-build --wait --wait-timeout 360 "$SERVICE"
printf '%s\n' "$SERVICE_IMAGE" > "../last-successful-${SERVICE}-image"
printf '%s\n' "$PWD" > "../last-successful-${SERVICE}-release"
"${compose[@]}" ps
echo "$SERVICE is healthy."
