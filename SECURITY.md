# Security policy

## Repository rules

- Never commit API keys, bot tokens, OAuth credentials, Supabase service-role keys,
  rendered private URLs, or `.env` files.
- Runtime configuration is loaded exclusively from environment variables. The
  committed `.env.example` contains names and placeholders only.
- Any credential committed to Git must be revoked and recreated immediately.
  Removing it from a later commit does not make the original value safe.

## Reporting and response

Report a suspected exposure privately to the repository owner. The response is:

1. revoke and recreate the credential;
2. remove the value from tracked source and deployment configuration;
3. audit provider access logs where available; and
4. consider rewriting public Git history after rotation.
