# Group App

## Persistent storage on Render

The app uses PostgreSQL whenever the `DATABASE_URL` environment variable is set.
It creates the required `people` table automatically on the first request and
seeds the regular-member list when the table is empty.

On Render, create a PostgreSQL database and add its internal database URL to the
web service as the `DATABASE_URL` environment variable. Redeploy the service
after saving the variable.

Without `DATABASE_URL`, the app falls back to local JSON files for development.
Local JSON files are not persistent on Render.
