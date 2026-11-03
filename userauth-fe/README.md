# Authentication Frontend

## Prerequisites

- Git, Node.js 20.9+ and npm
- The FastAPI backend running locally

## Setup

```bash
git clone https://github.com/vrutt/practical-task user-auth
cd user-auth/userauth-fe
npm install
```

Copy `.env.example` to `.env.local` and set `BACKEND_URL` to the backend URL, for example `http://127.0.0.1:8000`. Then run:

```bash
npm run dev
```

Open `http://localhost:3000`. Configure that origin in the backend's `CORS_ALLOWED_ORIGINS`.

## Structure

- `app/` — Next.js App Router pages and layouts.
- `components/` — reusable UI and protected layout.
- `assets/css/` — global styles and page or component stylesheets.
- `services/api/apiCalls/auth/` — auth API operations; add other features under `apiCalls/`.
- `services/api/client.ts` and `endpoints.ts` — shared HTTP handling, refresh and endpoint paths.
- `types/auth.ts` — auth payload, user, component and store interfaces; `types/index.ts` — shared response interfaces.
- `store/` — Zustand client state.
- `utils/constants.ts` — frontend validation rules and messages.

API calls use the same-origin `/api/v1` proxy, which forwards the same path to the backend (for example, `/api/v1/auth/login`). The backend sets HTTP-only cookies; the store contains only the current user's profile. The backend enforces access and roles. Swagger is available at `/api/docs`.

The protected layout owns session initialization: it shows a loading state, requests the current user, and redirects on a confirmed unauthorized response. It clears the stored user if initialization fails, and network failures show a retry option. The stored user is the last successfully verified identity, not proof that a session remains valid; protected APIs enforce access independently. If a logout response is uncertain, the app does not refresh or claim that logout succeeded. It asks the user to retry, keeping the last verified identity until logout succeeds or session initialization fails.

Refresh requests are coordinated within one browser tab. Separate tabs can race when rotating the same refresh token; a tab may need to sign in again. Profile timestamps are returned by the API with an explicit UTC offset.

## Adding a feature

1. Add its request, response and component interfaces in `types/`; extend the shared response interfaces where appropriate.
2. Add endpoint paths to `services/api/endpoints.ts` and API methods under `services/api/apiCalls/<feature>/` using the shared client.
3. Add components under `components/`, validation constants under `utils/`, and shared client state under `store/` only if needed.
4. Add a route or layout under `app/`; use the protected layout and backend authorization for private data.
5. Run `npm run lint`, `npm run format:check`, and `npm run build`. To fix formatting, run `npm run lint:fix` followed by `npm run format`.

## Rendering

Login and registration have statically generated shells. Protected pages render a static shell and fetch session-specific data on the client without caching; the guard does not replace backend authorization. ISR is unnecessary because the app has no periodically refreshed public data. If future pages need personalized server-rendered content, use request-time rendering and do not share cached user data.
