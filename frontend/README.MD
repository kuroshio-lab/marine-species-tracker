# Marine Species Tracker Frontend

This is the frontend application for the Marine Species Tracker, built with Next.js and designed to provide an intuitive user interface for interacting with marine species observation data.

## Technologies Used

*   **Next.js**: A React framework for building server-side rendered and static web applications.
*   **React**: A JavaScript library for building user interfaces.
*   **TypeScript**: A typed superset of JavaScript that compiles to plain JavaScript.
*   **Radix UI**: A collection of unstyled, accessible UI components.
*   **Leaflet**: An open-source JavaScript library for mobile-friendly interactive maps.
*   **Tailwind CSS**: A utility-first CSS framework for rapidly styling components.
*   **Zod**: A TypeScript-first schema declaration and validation library.
*   **React Hook Form**: A performant, flexible, and extensible forms library for React.

## Project Structure

This project is part of a monorepo, with the backend managed separately. The entire application is orchestrated using Docker Compose (`docker-compose.yml`) in the root directory.

### `src` Folder Overview

The `src` directory contains the core application logic and UI components:

*   **`app/`**: This directory holds the Next.js page components and layout.
    *   `AppContent.tsx`: Main application content.
    *   `layout.tsx`: Root layout for the application.
    *   `page.tsx`: The main landing page.
    *   `forgot-password/`, `reset-password/`, `sign-in/`, `sign-up/`, `verify-email/`: Directories containing pages related to user authentication flows.
*   **`components/`**: Reusable UI components used throughout the application, including the `ObservationModal.tsx` for adding and editing observations.
*   **`hooks/`**: Custom React hooks for encapsulating reusable logic, such as `useLoading.tsx`.
*   **`lib/`**: Utility functions and API clients.
    *   `api.ts`: For interacting with the backend API.
    *   `observation.ts`: Specific functions for observation-related API calls.
    *   `species.ts`: Specific functions for species-related API calls.
    *   `utils.ts`: General utility functions.
*   **`middleware.ts`**: Next.js middleware for handling requests before they are completed.
*   **`styles/`**: Global stylesheets.
    *   `globals.css`: Contains global CSS rules, Tailwind CSS imports, and custom CSS variables for theming.
*   **`types/`**: TypeScript type definitions.
    *   `form.ts`: Type definitions for form structures.
    *   `geojson.ts`: Type definitions for GeoJSON data.
    *   `observation.ts`: Type definitions for observation data.
    *   `r3f.d.ts`: Type definitions for `react-three-fiber`.
    *   `user.ts`: Type definitions for user data.

## Configuration

### `frontend/next.config.js`

This file configures Next.js. Key configurations include:

*   `reactStrictMode: true`: Enables React's Strict Mode for highlighting potential problems in an application.
*   `output: 'standalone'`: Optimizes the build for deployment as a standalone application.
*   `images.domains`: Specifies allowed domains for image optimization, including `localhost` for development.
*   `env`: Defines environment variables accessible in the browser, such as `NEXT_PUBLIC_API_URL`, which defaults to `http://localhost:8000`.

### Styling (`frontend/tailwind.config.js` and `frontend/src/styles/globals.css`)

*   **`tailwind.config.js`**: This is the Tailwind CSS configuration file, where custom themes, colors (e.g., `ocean` brand colors, `semantic` colors for success/warning/error), fonts, and other design tokens are defined. It also includes the `tailwindcss-animate` plugin.
*   **`src/styles/globals.css`**: This file imports the Inter font, Tailwind's base, components, and utilities, and defines custom CSS variables for `radix-ui` and various brand/semantic colors used by Tailwind. It also includes specific styles for Leaflet popups to ensure consistent rendering.

## Core Logic

### `frontend/src/middleware.ts`

The `middleware.ts` file in the frontend handles authentication and routing protection. It acts as a gatekeeper for routes, ensuring that only authenticated users can access protected parts of the application.

*   **Exclusion List**: It first checks if the requested `pathname` is part of an exclusion list (e.g., `/sign-in`, `/sign-up`, `/forgot-password`, `/verify-email`, `/reset-password/*`, and static assets like `/_next/` or `/models/`). These routes are publicly accessible.
*   **Authentication Check**: For all other routes, the middleware proxies the incoming `cookie` header to the backend's `/api/v1/auth/profiles/me/` endpoint. This backend endpoint, as described in the `backend/README.md`, is responsible for validating the user's JWT (JSON Web Token) stored in an `HttpOnly` cookie.
*   **Redirection**: If the backend returns a non-200 status (indicating the user is not authenticated), the middleware redirects the user to the `/sign-in` page.
*   **Cookie-Based Authentication**: This middleware is crucial for the application's login-locked nature, as it enforces authentication using the secure, `HttpOnly` cookies managed by the backend.

### `frontend/src/lib/api.ts`

This file configures the Axios HTTP client (`api`) used for all API communication with the backend. It's central to how the frontend handles authenticated requests and token refreshing.

*   **Base URL and Credentials**: The `axios.create` call sets the base URL for API requests and ensures `withCredentials: true`, which is essential for sending and receiving `HttpOnly` cookies (containing JWTs) with every request.
*   **CSRF Token Handling**: An `interceptor.request` is used to automatically retrieve the CSRF (Cross-Site Request Forgery) token from cookies (`csrftoken`) and include it in the `X-CSRFToken` header for all outgoing requests. This protects against CSRF attacks.
*   **JWT Refresh Mechanism**: The `interceptor.response` is critical for handling expired JWT access tokens:
    *   **401 Unauthorized Detection**: It intercepts `401 Unauthorized` responses from the backend, indicating an expired access token.
    *   **Token Refresh Request**: If a 401 is detected and it's not already a refresh token request, it attempts to obtain a new access token by calling the backend's `/v1/auth/token/refresh/` endpoint. The `refresh_token` is automatically sent via an `HttpOnly` cookie.
    *   **Request Queueing**: To prevent race conditions, if multiple requests fail with a 401 while a token refresh is in progress, they are queued (`failedQueue`) and re-attempted once a new access token is successfully obtained.
    *   **Logout on Refresh Failure**: If the refresh token request itself fails (e.g., the refresh token is expired or invalid), the user is redirected to the `/sign-in` page, effectively logging them out.
    *   **Seamless User Experience**: This mechanism ensures that users remain authenticated without needing to re-enter their credentials as long as their refresh token is valid, providing a seamless experience even when access tokens expire.
    
### `frontend/src/components/MapComponent.tsx`

The `MapComponent.tsx` is a central component responsible for displaying marine species observations on an interactive Leaflet map.

*   **Map Initialization**: It initializes a Leaflet `MapContainer` with a default position, zoom level, and OpenStreetMap tile layer.
*   **Dynamic Observation Loading**: The map dynamically loads observations based on the current map view (center, zoom level) and applies filtering parameters (species name, common name, date range).
    *   `loadAllMapObservations` function: This `useCallback` function is responsible for fetching observations from the backend API using `fetchMapObservations`. It incorporates debouncing to prevent excessive API calls during map interactions (zoom, move).
    *   **Radius Calculation**: `calculateRadius` dynamically adjusts the radius for observation queries based on the current zoom level, ensuring relevant data is fetched without overwhelming the map with too many markers in a global view.
*   **Marker Rendering**: It iterates through `GeoJsonFeature` data (representing observations) and renders `Marker` components on the map. Each observation is displayed with three copies across the longitude to create a seamless world map experience.
*   **Custom Marker Icons**: Observations are rendered with custom `L.divIcon` markers, which change color based on the observation's source and validation status:
    *   **External Observations**: Displayed with a primary brand blue icon.
    *   **Validated User Observations**: Displayed with a semantic success green icon.
    *   **Pending User Observations**: Displayed with a semantic warning yellow icon.
*   **Popups**: Each marker has an associated `Popup` that displays a `MiniObservationCard` when clicked, providing detailed information about the observation.
*   **Popup Auto-Panning**: A custom logic is implemented to ensure that when a popup is opened, the map automatically pans to keep the entire popup card within the viewport, preventing it from being cut off. This logic also temporarily disables observation reloading to maintain the popup's state.
*   **Map Event Handling**: The `MapEventsHandler` hook uses `useMapEvents` to listen for `zoomend` and `moveend` events, triggering a debounced reload of observations to keep the map data up-to-date with the visible area.


## Development

The frontend development server can be started using `npm run dev` (defined in `frontend/package.json`). This leverages Next.js's development server with hot-reloading.

The `docker-compose.yml` file in the root directory handles the setup and coordination of both the frontend and backend services within Docker containers, ensuring they can communicate correctly.
