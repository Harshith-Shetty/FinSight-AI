#!/usr/bin/env bash

set -Eeuo pipefail

compose=(docker compose -f docker-compose.prod.yml)

echo "Building Docker images..."
"${compose[@]}" build

echo "Applying Database Migrations..."
"${compose[@]}" run --rm api alembic upgrade head

echo "Restarting containers..."
"${compose[@]}" up -d --remove-orphans

echo "Waiting for the API health check..."
for attempt in {1..20}; do
    health_status="$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}starting{{end}}' finsight-api 2>/dev/null || true)"
    if [[ "${health_status}" == "healthy" ]]; then
        "${compose[@]}" ps
        echo "Deployment completed successfully!"
        exit 0
    fi

    if [[ "${health_status}" == "unhealthy" ]]; then
        break
    fi

    sleep 5
done

"${compose[@]}" ps
"${compose[@]}" logs --tail=100 api
echo "Deployment failed because the API did not become healthy." >&2
exit 1
