# Render and Vercel deployment

The root `render.yaml` provisions the FastAPI Docker service, managed PostgreSQL
16, and a 30 GB persistent artifact disk in Render's Ohio region. Vercel deploys
the `frontend/` directory separately.

## Render Blueprint

In Render, create a Blueprint from the GitHub repository. During initial setup,
provide:

- `MARKETLAB_ALLOWED_ORIGINS`: the exact Vercel production URL, without a path;
- `SEC_USER_AGENT`: a real name and contact email;
- `ALPHA_VANTAGE_API_KEY`: the provider key, or an empty value if production
  downloads will remain disabled.

The startup command prepares `/app/storage`, creates the PostgreSQL schema, and
binds FastAPI to Render's assigned port. The database is not publicly accessible.

The persistent disk begins empty. From the Render service shell, populate these
directories using a private transfer or object-storage download:

```text
/app/storage/data
/app/storage/reports
/app/storage/experiments
```

Do not commit research datasets or provider credentials to Git. The service will
return empty catalogs until the required report and experiment artifacts have
been transferred.

## Vercel

Import the same repository into Vercel and set the project root to `frontend`.
Configure both production environment variables with the Render service URL:

```text
MARKETLAB_API_URL=https://marketlab-api.onrender.com
NEXT_PUBLIC_MARKETLAB_API_URL=https://marketlab-api.onrender.com
```

After the Vercel URL is final, update `MARKETLAB_ALLOWED_ORIGINS` in Render and
redeploy the API. Verify `/health`, `/openapi.json`, the dashboard, Factor Lab,
ML Lab, report previews, and one small backtest request.
