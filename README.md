# CircleTalk

CircleTalk is a production-oriented SaaS for private AI roundtable discussions. The production web entrypoint is the Wasp/Open SaaS app in `apps/open-saas/app`; the FastAPI app in `apps/backend` is a private AI Worker used only by the Wasp server.

## Production Architecture

- `apps/open-saas/app` is the only production user-facing application.
- Wasp owns Google Auth, users, Stripe billing, credits, roundtable sessions, messages, artifacts, usage records, and admin operations.
- `apps/backend` is a private FastAPI AI Worker. It accepts already-authorized server-to-server requests from Wasp and streams Roundtable worker SSE events.
- The Worker does not own browser auth, payment state, credit settlement, or session persistence.
- Worker internal endpoints under `/internal/roundtable/*` require `AI_WORKER_SHARED_SECRET`.
- `apps/frontend` is a legacy Vite React demo and is not part of default production build or deploy.

```text
bedrock/
├── apps/
│   ├── open-saas/app/          # Production CircleTalk Wasp/Open SaaS app
│   ├── backend/                # Private FastAPI AI Worker
│   └── frontend/               # Legacy Vite demo, not production
├── packages/
│   ├── core/                   # Python shared infrastructure
│   ├── llm/                    # Roundtable LLM orchestration
│   └── knowledge/              # Knowledge package
├── docs/                       # Technical docs and launch checklist
└── .agents/                    # Codex skills and project gates
```

## Local Development

Start Postgres:

```bash
docker compose -f docker-compose.dev.yml up -d postgres
```

Start the Wasp/Open SaaS app:

```bash
cd apps/open-saas/app
wasp start db
wasp db migrate-dev
wasp start
```

Start the private AI Worker:

```bash
pnpm dev:worker
```

The Wasp server needs `AI_WORKER_URL=http://localhost:8000` and the same `AI_WORKER_SHARED_SECRET` value that is configured on the Worker. The Worker should set `ALLOWED_ORIGINS` to the Wasp app origin in production; for local development use `http://localhost:3000,http://localhost:3001`.

## Required Configuration

Google OAuth:

- Create a Google OAuth client.
- Configure the Wasp callback URL for your deployment.
- Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in the Wasp server environment.

Stripe:

- Create subscription prices for Hobby and Pro.
- Create a one-time payment price for `Credits10`.
- Set `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET`, `PAYMENTS_HOBBY_SUBSCRIPTION_PLAN_ID`, `PAYMENTS_PRO_SUBSCRIPTION_PLAN_ID`, and `PAYMENTS_CREDITS_10_PLAN_ID`.
- Configure the webhook endpoint at `/payments-webhook`.

Secrets:

- Set `JWT_SECRET` for Wasp production.
- Set `ROUNDTABLE_STREAM_TOKEN_SECRET` for signed one-time stream tokens.
- Set `AI_WORKER_SHARED_SECRET` on both Wasp and the private Worker.
- Never commit real secrets. Use `.env.example`, `apps/open-saas/app/.env.server.example`, and `apps/open-saas/app/.env.client.example` as placeholders only.

LLM Worker:

- Set `APP_ENV=production` in production.
- Set `ALLOWED_ORIGINS` to the Wasp app origin only.
- Configure `ROUNDTABLE_LLM_ENABLED`, `ROUNDTABLE_LLM_MODEL`, and either `OPENAI_API_KEY` or `ROUNDTABLE_LLM_API_KEY` depending on the provider.

## Scripts

```bash
pnpm dev:saas        # Wasp/Open SaaS app
pnpm dev:worker      # FastAPI private Worker
pnpm lint:worker     # Ruff + Pyright for Python Worker/shared packages
pnpm test:worker     # Worker/backend tests
pnpm build           # Production Wasp/Open SaaS build, not legacy frontend
```

The old `apps/frontend` can still be run manually for archaeology, but it is not the production app and is excluded from root-level default build/deploy scripts.

## Deployment

Production requires two services:

- Wasp/Open SaaS web app from `apps/open-saas/app`.
- Private FastAPI AI Worker from `apps/backend`.

See [deployment docs](docs/deployment.md) and [launch checklist](docs/launch-checklist.md) before going live.

## Quality Gates

```bash
uv run pytest apps/backend/tests -q
uv run ruff check apps/backend/src packages/core/src packages/llm/src packages/knowledge/src apps/backend/tests
uv run pyright apps/backend/src
```

For Wasp, run install, Prisma migration/generate, typecheck/build, and smoke tests in an environment with Node, pnpm, and Wasp installed.
