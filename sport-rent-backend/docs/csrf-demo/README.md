# Local CSRF demo: change an account email

The profile's email form and the attacker's page both submit to the same account
endpoint. Normally, the endpoint requires the CSRF header sent by the profile
form. `CSRF_DEMO_ENABLED=true` removes that check for a local teaching demo.
The flag defaults to `false`. Use a local database and a disposable account.

## Run

1. Set up PostgreSQL and the backend as described in the main README. In the
   backend `.env`, set `CSRF_DEMO_ENABLED=true` and `AUTH_COOKIE_SECURE=false`.
   Apply migrations with `uv run --env-file .env alembic upgrade head`, then
   seed the products with `uv run --env-file .env python -m scripts.seed`.
   If products are already seeded, run just
   `uv run --env-file .env python -m scripts.seed_csrf_demo_comment`.
   Start the API at `http://127.0.0.1:8000`.
2. Start the frontend with `VITE_API_URL=http://127.0.0.1:8000` and open it at
   `http://127.0.0.1:5173`. Log in to a disposable account. In the account
   settings, note its current email. The profile form now saves email changes in
   the database through the same endpoint used in this demo.
3. From this directory, run `python -m http.server 9000 --bind 127.0.0.1`.
   In the **same browser**, open the `Rower szosowy` product page. In the
   comments, Mareczek has posted a supposed code `MAREK20`. Click the link in
   his comment.
4. The link opens `http://127.0.0.1:9000/attack.html`, which silently submits
   the cross-origin form. Return to the account settings and reload the page.
   The email now reads `attacker@example.com`.

Keep the hostname `127.0.0.1` consistent. The login sets a `SameSite=Lax`
refresh cookie for the API's `/auth` path. The attack page runs on another port
of the same site, so its form POST to `/auth/account/email` includes that cookie.
In normal mode, the endpoint also requires the `X-CSRF-Token` header. An HTML
form on another origin cannot add that header. With the demo flag enabled, the
endpoint trusts the cookie alone and accepts the attacker's form. This is an
intentionally insecure version of a real profile action, not a separate attack
only endpoint. The example omits email verification and password confirmation
to keep the CSRF mechanism visible.

Product comments are stored in the database. Signed-in users can add comments;
visitors can read them. Mareczek's comment is a demo fixture shown only while
`CSRF_DEMO_ENABLED=true`. The `MAREK20` text is bait, not a cart discount.

After the demo, set `CSRF_DEMO_ENABLED=false` and restart the backend. The
profile email setting still works, but requests without a CSRF header fail.
