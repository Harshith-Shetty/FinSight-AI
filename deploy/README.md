# Azure DevOps releases to EC2

Production currently declares two application containers, API and Celery worker, with external PostgreSQL, Redis and Qdrant. Each application has its own pipeline, Docker Hub repository and immutable image digest. They share a Dockerfile but deploy independently. No database image is built or database volume reset.

## Azure setup

1. Create two Docker Hub repositories, such as `yourname/finsight-api` and `yourname/finsight-worker`. Set `dockerHubRepository` in each pipeline entry to your actual repository.
2. Create two Azure YAML pipelines from this GitHub repository: API uses `azure-pipelines.yml`; Celery uses `azure-pipelines-worker.yml`.
3. Create Docker Registry service connection `finsight-dockerhub` using a Docker Hub access token with push permission. Create SSH connection `finsight-ec2` for your existing EC2 deployment user. Authorize both pipelines.
4. Create environment `finsight-production`, add an **exclusive lock** check, and optionally a production approval. Both pipelines must use this environment to serialize deployments.
5. Create variable group `finsight-production` and authorize both pipelines. Add `PRODUCTION_ENV_JSON` as a **secret**, using `runtime.example.json` as a starting point. Copy all actual existing settings, including the existing SECRET_KEY, without rotating it unintentionally. Add `UPLOADS_VOLUME` and `COMPOSE_PROJECT_NAME` using the existing production values. Set `AZURE_DEPLOY_ENABLED` to `false` initially.

Runtime JSON supports other existing application settings too. Celery broker and result backend default to REDIS_URL when omitted. Values are rendered as literal Compose raw environment values, never sourced as shell commands. Secrets are transferred over SSH to private release directories and excluded from build artifacts and Docker context.

## EC2 prerequisites

Use Docker with Compose **2.30 or newer**, Bash and `flock`. The SSH user needs Docker access without sudo and network access to the hosted services. For private repositories, log Docker into Docker Hub on EC2 with a read-only token. Hosted Azure agents must be able to reach EC2 SSH; a self-hosted agent with private connectivity is another option. The default build assumes x86-64 EC2; adjust the build platform before using ARM.

Find existing resource names on EC2:

```bash
docker inspect -f '{{index .Config.Labels "com.docker.compose.project"}}' finsight-api
docker inspect -f '{{range .Mounts}}{{if eq .Destination "/app/uploads"}}{{.Name}}{{end}}{{end}}' finsight-api
```

Use those exact names in the variable group. The upload volume must already exist; it is declared external and is never deleted. The worker must use the same established project and volume as the API.

## Handover and releases

Build both pipelines with deployment disabled first. Set GitHub repository variable `DEPLOYMENT_PROVIDER=azure` to disable the existing GitHub deployment job, and wait for any active GitHub deployment to finish. Then set Azure `AZURE_DEPLOY_ENABLED=true`. Run the API pipeline from main first, then the worker pipeline for initial adoption.

API-only route changes trigger only the API pipeline; worker changes currently trigger both because API routes import task definitions. Core, models, services, migrations, dependencies and deployment tooling trigger both. A manual Celery release deploys only Celery; separating task implementations from API imports would allow narrower automatic worker triggers. Each pipeline builds, checks and pushes its own image, then deploys only that service using its digest and `--no-deps`. Changing either service never restarts the other. PostgreSQL, Redis and Qdrant stay external.

API releases run Alembic before replacing the API. Worker releases never run migrations. Shared changes must remain compatible with the old API/worker and database schema: pipelines build independently and their completion order is not guaranteed. For migration-dependent worker changes, use environment approvals to release API first and approve worker only after migrations succeed. Use additive migrations and separate later removal of old fields.

To update endpoints, edit the secret JSON in Azure and run the affected service pipeline from main. Run both if both need the new settings. Existing containers retain their environment until their own release. These pipelines perform in-place replacement, not zero-downtime deployment. Celery gets up to 31 minutes to drain; changes needing stronger task delivery guarantees require application-level handling.

Failed migrations prevent API replacement. Failed health checks fail the release and do not mark it successful; they do not automatically restore the previous container. EC2 stores separate `last-successful-api-release` and `last-successful-worker-release` pointers under `~/finsight-releases`. An operator can rerun a previous service release script only after checking schema compatibility; database migrations are not automatically reversed. Release directories contain private runtime settings: restrict host access and apply a retention policy after preserving rollback releases.

## Local checks

```bash
python -m unittest tests.test_citations tests.test_release_config -v
bash -n deploy/release.sh
```

Live build, Docker Hub publication and EC2 verification require the Azure connections and variables above. No production deployment is performed by adding these files.

References: [Azure Docker task](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/docker-v2?view=azure-pipelines), [SSH task](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/ssh-v0?view=azure-pipelines), [Compose raw environment files](https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/).
