# Production deployment settings

The `Continuous Deployment` workflow deploys `main` to EC2 and rewrites the
server's `.env` file from the GitHub `production` environment before each
release. Change hosted service endpoints in GitHub and rerun the workflow; no
EC2 login is required.

Create a GitHub environment named `production` under **Settings > Environments**.

## Secrets

Add these encrypted secrets to the `production` environment:

- `DATABASE_URL`
- `REDIS_URL`
- `QDRANT_API_KEY`
- `SECRET_KEY`
- `GROQ_API_KEY`
- `POSTMARK_SERVER_TOKEN`

The existing connection secrets can remain repository secrets or be moved to
the environment:

- `EC2_HOST`
- `EC2_USERNAME`
- `EC2_SSH_KEY`

`DATABASE_URL` must use the SQLAlchemy asyncpg form, for example
`postgresql+asyncpg://user:password@host:5432/database`. `REDIS_URL` is also
used for the Celery broker and result backend.

## Variables

Add these non-secret variables to the same environment:

- `QDRANT_URL`
- `FRONTEND_URL`
- `POSTMARK_FROM_EMAIL`

Optional variables and workflow defaults:

- `DATABASE_SSL` defaults to `true`
- `LLM_PROVIDER` defaults to `groq`
- `GROQ_MODEL` defaults to `llama-3.3-70b-versatile`
- `OLLAMA_BASE_URL` defaults to empty
- `OLLAMA_MODEL` defaults to `llama3.2:3b`
- `POSTMARK_MESSAGE_STREAM` defaults to `outbound`

After changing a secret or variable, open **Actions > Continuous Deployment**
and choose **Run workflow**, or push a backend change to `main`.
