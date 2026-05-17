# CircleTalk Deployment

CircleTalk production uses Render Blueprint resources:

- Wasp/Open SaaS API server from `apps/open-saas/app`.
- Wasp/Open SaaS static client from `apps/open-saas/app`.
- Private FastAPI AI Worker from `apps/backend`.
- Render Postgres for Wasp persistence.

`apps/frontend` is a legacy Vite demo. Do not deploy it as a production service.

## Render Blueprint

Use the root `render.yaml` to create the production stack from the release
branch. The blueprint intentionally splits Wasp into server and client because
Wasp 0.21 generates deployable output in `.wasp/out`, with the server and static
client deployed separately.

Default Render URLs used by the blueprint:

- Wasp server: `https://circletalk-wasp-server.onrender.com`
- Wasp client: `https://circletalk-wasp-client.onrender.com`
- Worker: private service `http://circletalk-ai-worker:8000`

If Render assigns different service URLs, update `WASP_SERVER_URL`,
`WASP_WEB_CLIENT_URL`, `REACT_APP_API_URL`, `ZPAY_NOTIFY_URL`,
`ZPAY_RETURN_URL`, and Worker `ALLOWED_ORIGINS`, then redeploy the affected
services.

## Wasp Server

Configure:

- `NODE_ENV=production`
- `WASP_SERVER_URL`
- `WASP_WEB_CLIENT_URL`
- `JWT_SECRET`
- `DATABASE_URL`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `PAYMENT_PROVIDER=zpay`
- `ZPAY_PID`
- `ZPAY_KEY`
- `ZPAY_NOTIFY_URL` set to `https://<wasp-server>/payments/zpay/notify`
- `ZPAY_RETURN_URL` set to `https://<wasp-client>/checkout`
- `PAYMENTS_CREDITS_10_AMOUNT_CNY=9.90`
- `ADMIN_EMAILS`
- `AI_WORKER_URL` set to the Worker private URL
- `AI_WORKER_SHARED_SECRET`
- `ROUNDTABLE_STREAM_TOKEN_SECRET`

The Wasp server startup runs Prisma production migrations before serving
traffic.

## Wasp Client

Configure safe client variables only:

- `REACT_APP_API_URL` set to the Wasp server public URL
- `REACT_APP_CREDITS_10_PRICE_LABEL=¥9.90`

The static site must rewrite all routes to `/index.html` so authenticated SPA
routes such as `/roundtable` and `/checkout` reload correctly.

## FastAPI AI Worker

Configure:

- `APP_ENV=production`
- `AI_WORKER_SHARED_SECRET`
- `ALLOWED_ORIGINS` set to the Wasp client origin only
- `ENABLE_LEGACY_ROUNDTABLE_API=false`
- `ROUNDTABLE_LLM_ENABLED=true`
- `ROUNDTABLE_LLM_MODEL`
- `OPENAI_API_KEY` or `ROUNDTABLE_LLM_API_KEY`
- `ROUNDTABLE_LLM_BASE_URL` when using an OpenAI-compatible provider

The Worker is a private service. It should not have a public `onrender.com`
domain. Wasp reaches it over Render private networking, and `/internal/roundtable/*`
must reject requests without the shared secret.

## Production Verification

After deploy:

- Open `/`, `/pricing`, and `/login` on the Wasp client.
- Configure Google OAuth redirect URI:
  `https://<wasp-server>/auth/google/callback`.
- Configure ZPAY notify URL:
  `https://<wasp-server>/payments/zpay/notify`.
- Configure ZPAY return URL:
  `https://<wasp-client>/checkout`.
- Log in with Google and confirm `/roundtable` is private.
- Run create session -> stream -> artifacts -> follow-up.
- Confirm messages/artifacts persist and credits settle correctly.
- Send duplicate ZPAY notify payloads in a controlled test and confirm credits
  are added once.
