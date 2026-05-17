# CircleTalk Launch Checklist

## Google OAuth

- Create a Google OAuth Client.
- Configure the Wasp redirect URI for the production domain.
- Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.
- Confirm signup stores and checks verified email data as expected.

## Stripe

- Create Hobby and Pro subscription products.
- Create the one-time `Credits10` product.
- Set `PAYMENTS_HOBBY_SUBSCRIPTION_PLAN_ID`.
- Set `PAYMENTS_PRO_SUBSCRIPTION_PLAN_ID`.
- Set `PAYMENTS_CREDITS_10_PLAN_ID`.
- Configure Customer Portal.
- Configure webhook endpoint `/payments-webhook`.
- Set `STRIPE_WEBHOOK_SECRET`.
- Test duplicate webhook delivery and confirm credits/subscription changes are idempotent.

## Wasp

- Set `WASP_SERVER_URL`.
- Set `JWT_SECRET`.
- Set `DATABASE_URL`.
- Run migrations.
- Confirm `/roundtable` is `authRequired`.
- Confirm unauthenticated users cannot access private roundtable operations.

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
- User can buy credits.
- Stripe webhook increases credits after payment.
- Duplicate Stripe webhook does not increase credits twice.
- User can create a roundtable session.
- Stream completes successfully.
- Messages and artifacts are saved.
- Credits are deducted according to entitlement rules.
- Follow-up works.
- Logged-out users cannot access private pages.
