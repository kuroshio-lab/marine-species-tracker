# 🐋 Marine Species Tracker — Backend (Django + GeoDjango + PostGIS)

This backend uses **Django** with **GeoDjango** and **PostGIS** for geospatial functionalities.
**All development and commands are intended to be run inside Docker containers** (not your host system).

---

## 🛠️ Dependency Management

This backend **now uses [Poetry](https://python-poetry.org/)** instead of `requirements.txt` for all Python package management.

### 🐍 How to install dependencies

- Dependencies are listed in `pyproject.toml` and `poetry.lock`.

- **Install everything (inside the backend container):**
  ```sh
  docker-compose run --rm backend poetry install
  ```

  - This will:
    - Create a virtual environment (if running locally—not inside Docker).
    - Install all main, development, and system-packaged dependencies.

- **Add a new runtime dependency:**
  ```sh
  docker-compose run --rm backend poetry add <package-name>
  ```

- **Add a new development dependency:**
  ```sh
  docker-compose run --rm backend poetry add --dev <package-name>

## 🚀 Quick Start

1. **Start all services ([backend, frontend, PostGIS DB]):**
    ```sh
    docker-compose up --build
    ```
    - The backend will be available at [http://localhost:8000](http://localhost:8000).
    - The PostGIS database will be available to containers as `db:5432`.

---

## 🛠️ Running Django Commands (always inside Docker)

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

    docker-compose exec backend python manage.py shelln:**
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
## 📊 ETL & External Data Sync (OBIS / WoRMS)

This backend includes an Extract, Transform, Load (ETL) pipeline to fetch and curate marine species occurrence data from the **OBIS API** and enrich it with common names from the **WoRMS API**. The curated data is stored in the `CuratedObservation` model in the `species` app.

The ETL is designed for periodic execution with two primary modes:

-   **Incremental Refresh:** Efficiently fetches only records updated or created within a specified date range (defaulting to the last month). This mode is ideal for regular updates.
-   **Full Refresh:** Dynamically fetches all available data from OBIS, ensuring comprehensive data integrity. This mode is suitable for less frequent, deep synchronizations.

**Geographical Scope (`--geometry` parameter):**
All OBIS queries require a geographical filter. The ETL command provides a `--geometry` argument where you can specify a WKT (Well-Known Text) string to define your area of interest (e.g., `POLYGON((-80 30, -80 50, -30 50, -30 30, -80 30))`).

**Crucially, if you omit the `--geometry` argument, it defaults to a global polygon (`POLYGON((-180 -90, 180 -90, 180 90, -180 90, -180 -90))`), allowing you to fetch all available OBIS data worldwide.**

### **Manual Execution for Testing / On-Demand Sync (via Docker)**

You can run the ETL process manually from your terminal. The command executes in a background thread within the `backend` container, and logs are printed directly to your terminal. A `time.sleep(1)` delay is introduced between page fetches to be respectful to the OBIS API.

-   **Run Incremental Refresh (last month's data):**
    Fetches a default number of pages (configurable in settings as `OBIS_DEFAULT_FETCH_PAGES`) for the last month.


        docker-compose exec backend python manage.py refresh_obis_data --mode incremental
      *   To specify a custom date range (YYYY-MM-DD) and/or a maximum number of pages:

        docker-compose exec backend python manage.py refresh_obis_data --mode incremental --start-date 2024-01-01 --end-date 2024-01-31 --max-pages 5
-   **Run Full Refresh (all data, dynamically paginated):**
    This mode will automatically determine the total number of pages from the OBIS API and fetch them sequentially.

      *   To limit the number of pages fetched for a full refresh (e.g., for testing or partial syncs):
        docker-compose exec backend python manage.py refresh_obis_data --mode full

        docker-compose exec backend python manage.py refresh_obis_data --mode full --max-pages 1000
      *   To specify a custom geometry for either mode (e.g., for a specific region):

        docker-compose exec backend python manage.py refresh_obis_data --mode full --geometry "POLYGON((-70 40, -70 50, -60 50, -60 40, -70 40))"
-   **Check the number of records in the database:**

        docker-compose exec db psql -U postgres -d marine_tracker -c "SELECT COUNT(*) AS total_observations, COUNT(DISTINCT species_name) AS distinct_species_names FROM species_curatedobservation;"

### **EC2 Configuration: Automated Monthly & Bi-Annual Cron Jobs**

For production deployment on an EC2 instance, you will configure system-level cron jobs to execute these commands automatically.

1.  **Ensure Docker Compose is set up and running your services on the EC2 instance.**
2.  **Edit your crontab:**

  Open the crontab editor:
  crontab -e

3.  **Add the following cron entries:**

  Monthly Incremental Refresh (1st day of month, 03:00 UTC)
  Fetches data with eventDate in the last month (date range handled by script default).
  ```sh
  0 3 1 * * cd /path/to/your/marine-species-tracker && docker-compose exec backend python manage.py refresh_obis_data --mode incremental >> /var/log/obis_refresh_monthly.log 2>&1
  ```

  Bi-Annual Full Refresh (1st day of January and July, 04:00 UTC)
  Fetches ALL data (global geometry, dynamically paginated).
  ```sh
  0 4 1 1,7 * cd /path/to/your/marine-species-tracker && docker-compose exec backend python manage.py refresh_obis_data --mode full >> /var/log/obis_refresh_biannual.log 2>&1
  ```
  *   **`/path/to/your/marine-species-tracker`**: Replace this with the actual absolute path to your project's root directory on the EC2 instance (where `docker-compose.yml` is located).
  *   **Log Files**: `>> /var/log/obis_refresh_monthly.log 2>&1` redirects all output to a log file, which is crucial for monitoring and troubleshooting cron jobs.

---

## 🧭 Spatial Library Setup (Important!)

- **All required system libraries** (`gdal`, `geos`, `proj`) are preinstalled _inside the backend Docker container_.
- **Ignore all spatial library errors** if running Django commands outside Docker—they do _not_ apply to this workflow.
- **Do not use your host Python/venv for backend tasks!**

---

## 🐘 Database (PostGIS)

- The PostGIS database is set up by Docker as the `db` service.
- Default connection settings inside Docker:
    HOST: db
    PORT: 5432
    DATABASE: marine_tracker
    USER: postgres
    PASSWORD: postgres

## 👤 User Authentication & Custom User System

This backend implements a **custom user model** (see `users/` app) with role support and JWT (cookie-based) authentication via Django REST Framework + SimpleJWT.

### Highlights
- **Custom User Model**: Uses email as the primary identifier, with unique username and role fields. Extend or adjust in `users/models.py`.
- **Registration, Login, Logout, and Profile**: Complete user management endpoints.
- **JWT Auth via HttpOnly Cookies**, not localStorage/sessionStorage.
- **Security**: Production-grade, with SameSite, Secure, and HttpOnly cookie flags set appropriately (see `users/views.py`).

### Key Endpoints

| Endpoint          | Method | Description                    | Requires Auth? |
|-------------------|--------|--------------------------------|---------------|
| `/api/v1/auth/register/`      | POST   | User registration              | No  |
| `/api/v1/auth/login/`         | POST   | User login, sets JWT cookie    | No  |
| `/api/v1/auth/logout/`        | POST   | Removes JWT cookie (logout)    | Yes |
| `/api/v1/auth/profiles/me/`   | GET    | Current user's profile         | Yes |
| `/api/v1/auth/verify-email/`  | POST   | Verify user email with token   | No  |
| `/api/v1/auth/password-reset/` | POST  | Request password reset email   | No  |
| `/api/v1/auth/password-reset/confirm/` | POST | Confirm password reset with new password | No  |

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

- Uses RESSEND for production email sending (configured in `core/settings.py`)
- Includes both HTML and plain text email templates
- Environment-specific domain configuration (localhost for development, production domain for live)
- Email templates are located in `users/templates/users/`

#### Security Features

- Tokens are cryptographically secure and time-limited (Django's `default_token_generator`)
- User IDs are base64 encoded for URL safety
- Passwords must be at least 8 characters long
- New password confirmation required
- Invalid tokens return generic error messages (prevents email enumeration)
- All reset endpoints are public (no authentication required)

#### Testing

Comprehensive tests are available in `users/test_users.py` covering:
- Successful password reset requests and confirmations

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
- Invalid email handling
- Invalid token/UID validation
- Password mismatch detection
- Password length validation

Run password reset tests with:
```bash
docker-compose exec backend pytest backend/users/test_users.py -k "password_reset"
```

### Roles & Permissions
- Custom roles can be added/managed in `users/models.py` for future admin/moderator logic.
- [Django admin interface](http://localhost:8000/admin) gives you superuser/role management.

### Adding More User Endpoints
- See `users/views.py` for class-based views. Add new endpoints in `users/urls.py` as needed.

---

For more, see the in-code docstrings in `users/serializers.py`, `users/views.py`, and the OpenAPI docs at `/api/v1/docs/` (Swagger UI).


## 🦺 Troubleshooting

- **Spatial library errors (GDAL/GEOS/PROJ):**
  Make sure you’re always running commands _inside the container_, not on your host.

- **Database errors:**
  Double-check that you’re using Docker Compose and that all containers are running.

---

## ✅ Recap

- ✔️ **Always** use Docker for backend commands: `docker-compose exec backend ...`
- ✔️ No need to set up geospatial libs or Python venv on your host.
- ✔️ If you see GDAL/GEOS errors on Mac, they're safe to ignore (just use Docker!).
- ✔️ Database and backend are ready out of the box with Docker Compose.
