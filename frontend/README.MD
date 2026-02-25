# Marine Species Tracker — Frontend

This is the frontend application for the Marine Species Tracker, built with Next.js and designed to provide an intuitive user interface for interacting with marine species observation data.

---

## Technologies Used

- **Next.js**: React framework for server-side rendering and static site generation.
- **React**: UI component library.
- **TypeScript**: Typed superset of JavaScript.
- **Axios**: HTTP client for all API communication with the backend.
- **Radix UI**: Unstyled, accessible UI component primitives.
- **Leaflet / React-Leaflet**: Interactive map rendering for observation data.
- **React Three Fiber / Drei / Three.js**: 3D rendering for decorative UI elements.
- **Tailwind CSS**: Utility-first CSS framework.
- **Zod**: TypeScript-first schema validation.
- **React Hook Form**: Performant form state management.
- **SWR**: Data fetching and caching.
- **Zustand**: Lightweight global state management.
- **date-fns**: Date utility library.
- **lucide-react**: Icon library.
- **@kuroshio-lab/components, @kuroshio-lab/ui, @kuroshio-lab/styles**: Internal Kuroshio Lab design system packages.

---

## Project Structure

This project is part of a monorepo. The entire application is orchestrated using Docker Compose (`docker-compose.yml`) in the root directory.

### `src` Folder Overview

```
src/
├── __tests__/          # Jest unit/integration tests
├── app/                # Next.js App Router pages and layout
├── components/         # Reusable UI components
├── hooks/              # Custom React hooks
├── lib/                # API clients and utility functions
├── middleware.ts        # Next.js middleware (auth guard)
├── styles/             # Global stylesheets
└── types/              # TypeScript type definitions
```

### `app/`

Next.js App Router directory — contains pages and the root layout.

| Path | Description |
|---|---|
| `layout.tsx` | Root layout, wraps all pages |
| `page.tsx` | Main landing/map page |
| `AppContent.tsx` | Core app shell rendered inside the layout |
| `opengraph-image.tsx` | Open Graph image generation |
| `sitemap.ts` | Sitemap generation |
| `sign-in/` | Login page |
| `sign-up/` | Registration page |
| `forgot-password/` | Password reset request page |
| `verify-email/` | Email verification page |
| `complete-researcher-profile/` | Researcher profile completion flow |

### `components/`

Reusable UI components used throughout the application.

| File | Description |
|---|---|
| `MapComponent.tsx` | Interactive Leaflet map with observation markers |
| `AuthLayout.tsx` | Shared layout wrapper for authentication pages |
| `ShadcnDynamicForm.tsx` | Dynamic form builder using Shadcn/Radix primitives |
| `SharkFin.tsx` | Decorative 3D shark fin component (React Three Fiber) |
| `UkiyoeWaves.tsx` | Decorative animated wave component (React Three Fiber) |

### `hooks/`

- `useLoading.tsx`: Custom hook for managing loading state.

### `lib/`

| File | Description |
|---|---|
| `api.ts` | Axios instance configuration, CSRF handling, and JWT refresh interceptor |
| `observation.ts` | API functions for observation-related calls |
| `species.ts` | API functions for species-related calls |
| `utils.ts` | General utility functions |

### `types/`

| File | Description |
|---|---|
| `form.ts` | Type definitions for form structures |
| `geojson.ts` | Type definitions for GeoJSON data |
| `observation.ts` | Type definitions for observation data |
| `user.ts` | Type definitions for user data |
| `r3f.d.ts` | Type augmentations for `react-three-fiber` |

---

## Configuration

### `next.config.js`

Key configurations:

- `reactStrictMode: true` — enables React Strict Mode.
- `output: 'standalone'` — optimizes the build for Docker/standalone deployment.
- `images.remotePatterns` — allowlists `localhost` for Next.js image optimization.
- `env.NEXT_PUBLIC_API_URL` — sets the backend URL (defaults to `http://localhost:8000`).

### Styling (`tailwind.config.js` and `src/styles/globals.css`)

- **`tailwind.config.js`**: Defines custom themes, `ocean` brand colors, semantic colors (success/warning/error), fonts, and includes the `tailwindcss-animate` plugin.
- **`globals.css`**: Imports the Inter font, Tailwind base/components/utilities, custom CSS variables for Radix UI and brand colors, and Leaflet popup style overrides.

---

## Core Logic

### `src/middleware.ts`

Handles authentication and route protection at the edge, before pages are rendered.

- **Public routes**: `/sign-in`, `/sign-up`, `/forgot-password`, `/verify-email`, `/reset-password/*`, and static assets (`/_next/`, `/models/`) are excluded from the auth check.
- **Auth check**: For all other routes, the middleware proxies the incoming `cookie` header to the backend's `/api/v1/auth/profiles/me/` endpoint to validate the user's JWT.
- **Redirection**: If the backend returns a non-200 response, the user is redirected to `/sign-in`.

### `src/lib/api.ts`

Configures the Axios HTTP client used for all backend API communication.

- **Base URL**: Set from `NEXT_PUBLIC_API_URL`. All requests go to `<API_URL>/api`.
- **Credentials**: `withCredentials: true` ensures `HttpOnly` cookies (JWTs) are sent with every request.
- **CSRF Handling**: A request interceptor reads the `csrftoken` cookie and injects it into the `X-CSRFToken` header on every outgoing request.
- **JWT Refresh**: A response interceptor handles `401 Unauthorized` errors:
  - Attempts to refresh the access token via `POST /api/v1/auth/token/refresh/` (refresh token sent via cookie).
  - Queues any concurrent failed requests (`failedQueue`) and retries them after a successful refresh.
  - On refresh failure, redirects the user to `/sign-in`.

### `src/components/MapComponent.tsx`

The central map component, rendering marine species observations on an interactive Leaflet map.

- **Initialization**: Renders a `MapContainer` with a default center, zoom, and OpenStreetMap tile layer.
- **Dynamic Loading**: Fetches observations via `fetchMapObservations` on map move/zoom events, with debouncing to avoid excessive API calls.
- **Radius Calculation**: Dynamically adjusts the query radius based on the current zoom level.
- **Marker Rendering**: Observations are rendered with custom `L.divIcon` markers, color-coded by source and validation status:
  - **External (OBIS/GBIF)**: Primary brand blue.
  - **Validated user observations**: Semantic success green.
  - **Pending user observations**: Semantic warning yellow.
- **Popups**: Each marker opens a `MiniObservationCard` popup on click.
- **Popup Auto-Panning**: The map automatically pans to keep opened popups fully within the viewport, and temporarily pauses observation reloading while a popup is open.
- **World Wrapping**: Each observation is rendered at three longitude offsets for a seamless world-wrap experience.

---

## Development

All available scripts (defined in `package.json`):

| Command | Description |
|---|---|
| `npm run dev` | Start the Next.js development server with hot-reloading |
| `npm run build` | Build the application for production |
| `npm run start` | Start the production server |
| `npm run lint` | Run ESLint |
| `npm run lint:fix` | Run ESLint and auto-fix issues |
| `npm run format` | Format all files with Prettier |
| `npm run check-format` | Check formatting without writing changes |
| `npm run type-check` | Run TypeScript type checking (no emit) |
| `npm run test` | Run Jest tests |
| `npm run test:watch` | Run Jest in watch mode |

The `docker-compose.yml` file in the root directory handles the full setup and coordination of frontend, backend, and database services.
