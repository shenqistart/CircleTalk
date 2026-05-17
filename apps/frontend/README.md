# Legacy Vite Frontend

This app is retained only for reference while CircleTalk finishes the migration to Wasp/Open SaaS.

- It is not the production user entrypoint.
- It is excluded from root-level default `dev`, `build`, `lint`, and `test` scripts.
- Production web development should happen in `apps/open-saas/app`.

Run it only when you intentionally need to inspect legacy behavior:

```bash
pnpm dev:legacy-frontend
```
