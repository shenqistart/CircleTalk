# CircleTalk Deployment

CircleTalk production has two services:

- Wasp/Open SaaS web app from `apps/open-saas/app`.
- Private FastAPI AI Worker from `apps/backend`.

The Wasp app is the only public user-facing entrypoint. The Worker should be private network reachable by Wasp only, with `/health` available for platform health checks.

## Wasp/Open SaaS

Configure:

- `WASP_SERVER_URL`
- `JWT_SECRET`
- `DATABASE_URL`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `STRIPE_API_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `PAYMENTS_HOBBY_SUBSCRIPTION_PLAN_ID`
- `PAYMENTS_PRO_SUBSCRIPTION_PLAN_ID`
- `PAYMENTS_CREDITS_10_PLAN_ID`
- `ADMIN_EMAILS`
- `AI_WORKER_URL`
- `AI_WORKER_SHARED_SECRET`
- `ROUNDTABLE_STREAM_TOKEN_SECRET`

Run Prisma/Wasp migrations before serving production traffic.

## FastAPI AI Worker

Configure:

- `APP_ENV=production`
- `AI_WORKER_SHARED_SECRET`
- `ALLOWED_ORIGINS` set to the Wasp app origin only
- `ENABLE_LEGACY_ROUNDTABLE_API=false`
- `ROUNDTABLE_LLM_ENABLED=true`
- `ROUNDTABLE_LLM_MODEL`
- `OPENAI_API_KEY` or `ROUNDTABLE_LLM_API_KEY`
- `ROUNDTABLE_LLM_BASE_URL` when using an OpenAI-compatible provider

The Worker must reject `/internal/roundtable/*` requests without the shared secret. Production CORS must not use wildcard origins with credentials.

## Legacy Frontend

`apps/frontend` is a legacy Vite React demo. Do not configure it as a production web service, and do not use it as the SaaS entrypoint.
