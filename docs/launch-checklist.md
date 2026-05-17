# CircleTalk Launch Checklist

## Google OAuth

- Create a Google OAuth Client.
- Configure the Wasp redirect URI for the production domain.
- Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.
- Confirm signup stores and checks verified email data as expected.

## ZPAY / Alipay

- Confirm ZPAY merchant eligibility, settlement rules, refund rules, and whether CircleTalk credits are allowed.
- Set `PAYMENT_PROVIDER=zpay`.
- Set `ZPAY_PID` and `ZPAY_KEY`.
- Set `ZPAY_NOTIFY_URL` to `/payments/zpay/notify` on the Wasp server origin.
- Set `ZPAY_RETURN_URL` to `/checkout` on the Wasp client origin.
- Set `PAYMENTS_CREDITS_10_AMOUNT_CNY=9.90`.
- Confirm notify delivery uses a public URL; localhost requires a tunnel.
- Test duplicate ZPAY notify delivery and confirm credits are added only once.

## Wasp

- Set `WASP_SERVER_URL`.
- Set `WASP_WEB_CLIENT_URL`.
- Set `JWT_SECRET`.
- Set `DATABASE_URL`.
- Run migrations.
- Confirm `/roundtable` is `authRequired`.
- Confirm unauthenticated users cannot access private roundtable operations.
- Confirm the static client has `REACT_APP_API_URL` pointing at the Wasp server.
- Confirm static route rewrites send `/roundtable` and `/checkout` to `/index.html`.

## Worker

- Set `AI_WORKER_URL`.
- Set `AI_WORKER_SHARED_SECRET`.
- Set `ALLOWED_ORIGINS` to the Wasp app origin.
- Set LLM provider environment variables.
- Verify `/health`.
- Verify requests without a valid shared secret cannot access `/internal/roundtable/*`.

## Smoke Tests

- User can log in with Google.
- New user receives the expected initial credits.
- User can buy credits with Alipay.
- ZPAY notify increases credits after payment.
- Duplicate ZPAY notify does not increase credits twice.
- User can create a roundtable session.
- Stream completes successfully.
- Messages and artifacts are saved.
- Credits are deducted according to entitlement rules.
- Follow-up works.
- Logged-out users cannot access private pages.
