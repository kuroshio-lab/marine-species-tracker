# Marine Species Tracker — Backend (Django + GeoDjango + PostGIS)

This backend uses **Django** with **GeoDjango** and **PostGIS** for geospatial functionalities.
**All development and commands are intended to be run inside Docker containers** (not your host system).

---

## Dependency Management

This backend uses [Poetry](https://python-poetry.org/) instead of `requirements.txt` for all Python package management.

### How to install dependencies

- Dependencies are listed in `pyproject.toml` and `poetry.lock`.

- **Install everything (inside the backend container):**
  ```sh
  docker-compose run --rm backend poetry install
  ```

- **Add a new runtime dependency:**
  ```sh
  docker-compose run --rm backend poetry add <package-name>
  ```

- **Add a new development dependency:**
  ```sh
  docker-compose run --rm backend poetry add --dev <package-name>
  ```

## Quick Start

1. **Start all services (backend, frontend, PostGIS DB):**
    ```sh
    docker-compose up --build
    ```
    - The backend will be available at [http://localhost:8000](http://localhost:8000).
    - The PostGIS database will be available to containers as `db:5432`.

---

## Running Django Commands (always inside Docker)

**Examples:**

- **Django shell:**
    ```sh
    docker-compose exec backend python manage.py shell
    ```

- **Run migrations:**
    ```sh
    docker-compose exec backend python manage.py makemigrations
    docker-compose exec backend python manage.py migrate
    ```

- **Create a superuser:**
    ```sh
    docker-compose exec backend python manage.py createsuperuser
    ```

- **Run tests:**
    ```sh
    docker-compose exec backend pytest
    # or
    docker-compose exec backend python manage.py test
    ```

- **Admin interface:**
  [http://localhost:8000/admin](http://localhost:8000/admin)

- **Access Postgres shell (psql):**
    ```sh
    docker-compose exec db psql -U postgres -d marine_tracker
    ```

- **Rebuild backend image if you change dependencies:**
    ```sh
    docker-compose build backend
    docker-compose up
    ```

---

## ETL & Data Synchronization

The backend features a unified ETL pipeline that aggregates marine species data from **OBIS** and **GBIF**, enriched with taxonomic data from **WoRMS**.

For a detailed breakdown of the pipeline architecture, manual execution commands, and data quality filters, please refer to the dedicated documentation:

**[Detailed ETL Documentation (OBIS/GBIF/WoRMS)](species/ETL_README.MD)**

### EC2 Automation (Production)

On the production EC2 instance, data synchronization is fully automated via system-level cron jobs. These jobs execute the specialized bash scripts located in the `scripts/` directory to handle multi-provider sync and deduplication.

#### Cron Job Configuration

The following jobs are configured in `/etc/cron.d/species-tracker-refresh`:

| Frequency | Task | Command |
| :--- | :--- | :--- |
| **Monthly** | Incremental Sync | `scripts/sync_incremental.sh` |
| **Bi-Annual** | Full Historical Refresh | `scripts/sync_full_refresh.sh` |

**Example Cron Entries:**

```sh
# Monthly Incremental Refresh (1st day of month, 03:00 UTC)
0 3 1 * * ubuntu cd /opt/species-tracker && /bin/bash scripts/sync_incremental.sh >> /var/log/species_sync_incremental.log 2>&1

# Bi-Annual Full Refresh (Jan 1st & July 1st, 04:00 UTC)
0 4 1 1,7 * ubuntu cd /opt/species-tracker && echo "yes" | /bin/bash scripts/sync_full_refresh.sh >> /var/log/species_sync_full.log 2>&1
```

> **Note:** The Full Refresh uses `echo "yes" |` to automatically bypass the interactive confirmation prompt in the production environment.

---

## Spatial Library Setup (Important!)

- **All required system libraries** (`gdal`, `geos`, `proj`) are preinstalled _inside the backend Docker container_.
- **Ignore all spatial library errors** if running Django commands outside Docker — they do _not_ apply to this workflow.
- **Do not use your host Python/venv for backend tasks!**

---

## Database (PostGIS)

- The PostGIS database is set up by Docker as the `db` service.
- Default connection settings inside Docker:
    ```
    HOST: db
    PORT: 5432
    DATABASE: marine_tracker
    USER: postgres
    PASSWORD: postgres
    ```

---

## User Authentication & Custom User System

This backend implements a **custom user model** (see `users/` app) with role support and JWT (cookie-based) authentication via Django REST Framework + SimpleJWT.

### Highlights
- **Custom User Model**: Uses email as the primary identifier, with unique username and role fields. Extend or adjust in `users/models.py`.
- **Registration, Login, Logout, and Profile**: Complete user management endpoints.
- **JWT Auth via HttpOnly Cookies**, not localStorage/sessionStorage.
- **Security**: Production-grade, with SameSite, Secure, and HttpOnly cookie flags set appropriately (see `users/views.py`).

### Key Endpoints

| Endpoint | Method | Description | Requires Auth? |
|---|---|---|---|
| `/api/v1/auth/register/` | POST | User registration | No |
| `/api/v1/auth/login/` | POST | User login, sets JWT cookie | No |
| `/api/v1/auth/logout/` | POST | Removes JWT cookie | Yes |
| `/api/v1/auth/refresh/` | POST | Refresh access token using refresh cookie | No |
| `/api/v1/auth/user/` | GET | Current user detail | Yes |
| `/api/v1/auth/profiles/me/` | GET | Current user's profile | Yes |
| `/api/v1/auth/verify-email/` | POST | Verify user email with token | No |
| `/api/v1/auth/password-reset/` | POST | Request password reset email | No |
| `/api/v1/auth/password-reset/confirm/` | POST | Confirm password reset with new password | No |
| `/api/v1/auth/researcher/complete-profile/` | POST | Complete researcher profile setup | Yes |

**Login/Logout flow uses JWTs in cookies:**
- Tokens are validated by custom middleware on every protected API call, including logout.
- All protected endpoints (`IsAuthenticated`) require the `access_token` cookie.

### Password Reset Flow

The backend includes a complete password reset system that sends secure reset links via email and allows users to set new passwords. This system is designed to work with a frontend application that handles the user interface for password reset forms.

#### How It Works

1. **Password Reset Request**: User submits their email address to `/api/v1/auth/password-reset/`
   - Backend validates the email exists in the system
   - Generates a secure, time-limited token and user ID (base64 encoded)
   - Sends an email with a reset link containing the token and user ID
   - The reset link format is: `https://your-frontend-domain/reset-password/{uidb64}/{token}/`

2. **Password Reset Confirmation**: User clicks the email link and submits a new password to `/api/v1/auth/password-reset/confirm/`
   - Backend validates the token and user ID
   - Ensures new passwords match (confirmation field)
   - Updates the user's password in the database
   - Invalidates the reset token (one-time use only)

#### Email Configuration

- Uses [Resend](https://resend.com/) for production email sending (configured via `RESEND_API` env var in `core/settings.py`)
- Includes both HTML and plain text email templates
- Environment-specific domain configuration (localhost for development, production domain for live)
- Email templates are located in `users/templates/users/`

#### Security Features

- Tokens are cryptographically secure and time-limited (3-day timeout via `PASSWORD_RESET_TIMEOUT`)
- User IDs are base64 encoded for URL safety
- Passwords must be at least 8 characters long
- New password confirmation required
- Invalid tokens return generic error messages (prevents email enumeration)
- All reset endpoints are public (no authentication required)

#### Testing

Comprehensive tests are available in `users/test_users.py` covering:
- Successful password reset requests and confirmations
- Invalid email handling
- Invalid token/UID validation
- Password mismatch detection
- Password length validation

Run password reset tests with:
```bash
docker-compose exec backend pytest users/test_users.py -k "password_reset"
```

### Email Verification Flow

The backend includes email verification for new user accounts. Users must verify their email address before they can sign in.

#### How It Works

1. **User Registration**: User submits registration form to `/api/v1/auth/register/`
   - Creates an inactive user account
   - Generates a secure verification token
   - Sends verification email with link containing token
   - Registration response indicates email verification is required

2. **Email Verification**: User clicks verification link or enters token manually
   - POST to `/api/v1/auth/verify-email/` with token
   - Activates user account and marks email as verified
   - User can now sign in

3. **Login Protection**: Attempting to login with unverified email shows appropriate error message

#### Security Features
- Verification tokens expire after 24 hours
- Tokens are cryptographically secure (32-byte URL-safe)
- Users must be inactive and unverified to use verification endpoint
- Failed verification attempts don't reveal token validity

#### Existing Users
Existing users created before email verification was implemented remain active and can continue logging in. To maintain consistency, you can mark existing users as verified:

```bash
# Using Django management command (recommended)
docker-compose exec backend python manage.py mark_existing_users_verified

# Or using the shell script
docker-compose exec backend python manage.py shell < scripts/mark_existing_users_verified.py
```

The management command supports `--dry-run` and `--created-before` options for safer updates.

### Roles & Permissions
- Custom roles can be added/managed in `users/models.py` for future admin/moderator logic.
- [Django admin interface](http://localhost:8000/admin) gives you superuser/role management.

### Adding More User Endpoints
- See `users/views.py` for class-based views. Add new endpoints in `users/urls.py` as needed.

---

For more, see the in-code docstrings in `users/serializers.py`, `users/views.py`, and the OpenAPI docs at `/api/v1/docs/` (Swagger UI).

---

## Observations

The `observations` app manages user-submitted marine species sightings. All observation endpoints require authentication.

### Key Endpoints

| Endpoint | Method | Description | Requires Auth? |
|---|---|---|---|
| `/api/v1/observations/` | GET, POST | List own observations / create new | Yes |
| `/api/v1/observations/<id>/` | GET, PUT, PATCH, DELETE | Retrieve, update, or delete an observation | Yes (owner or researcher) |
| `/api/v1/observations/export/` | GET | Export observations as CSV/JSON | Yes |
| `/api/v1/observations/<id>/validate/` | POST | Validate an observation (researcher role) | Yes |
| `/api/v1/observations/curated/` | GET | List curated/validated observations | Yes |

- Supports bounding-box filtering via `InBBoxFilter` on the `location` field.
- `ObservationDetailView` restricts access to owners, staff, and users with the `researcher` role.

---

## Map

The `map` app provides a read-only geospatial endpoint optimized for map rendering. It blends external (OBIS/GBIF) and user-submitted observations with a configurable ratio (default 30% user, 70% external, up to 500 points total — tunable via env vars).

### Key Endpoints

| Endpoint | Method | Description | Requires Auth? |
|---|---|---|---|
| `/api/v1/map/observations/` | GET | Blended map observation data (GeoJSON) | No |

- `MAP_OBSERVATION_DEFAULT_LIMIT` — max total points returned (default: 500)
- `MAP_OBSERVATION_USER_RATIO` — fraction of results from user observations (default: 0.30)

---

## Troubleshooting

- **Spatial library errors (GDAL/GEOS/PROJ):**
  Make sure you're always running commands _inside the container_, not on your host.

- **Database errors:**
  Double-check that you're using Docker Compose and that all containers are running.

---

## Recap

- Always use Docker for backend commands: `docker-compose exec backend ...`
- No need to set up geospatial libs or Python venv on your host.
- If you see GDAL/GEOS errors on Mac, they're safe to ignore (just use Docker!).
- Database and backend are ready out of the box with Docker Compose.
