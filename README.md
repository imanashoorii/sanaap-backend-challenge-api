# Document Management System (DMS) API

A secure document management REST API built with Django REST Framework.
Users upload, update, retrieve and delete documents stored in MinIO, with
role-based access control (RBAC), short-lived secure URLs, filtering and
pagination.

## Features

- JWT authentication (login with username **or** email)
- RBAC with three roles: `admin`, `editor`, `viewer`
- Document upload, update, retrieve and soft delete
- Private object storage on MinIO (S3 compatible)
- Presigned, expiring document URLs
- Upload validation (size, content type) and a SHA-256 checksum per document
- Filtering, search, ordering and pagination
- Interactive API docs (Swagger UI, ReDoc)
- Health endpoints for liveness and readiness
- Unit and API tests (41 tests)

## Tech stack

Python 3.12, Django 4.2, Django REST Framework, SimpleJWT, django-filter,
drf-spectacular, PostgreSQL, Redis (cache and throttling), MinIO
(django-storages + boto3), Gunicorn, Nginx, Docker.

## Roles and permissions

| Action                      | admin | editor | viewer |
|-----------------------------|:-----:|:------:|:------:|
| List / retrieve documents   |  yes  |  yes   |  yes   |
| Upload document             |  yes  |  yes   |   no   |
| Update document             |  yes  |  yes   |   no   |
| Delete document             |  yes  |   no   |   no   |
| Create users, change roles  |  yes  |   no   |   no   |

There is no public registration: only an admin creates users and assigns
roles. An admin cannot change their own role or status (prevents lock-out).
`createsuperuser` creates a user with the `admin` role.

## Project structure

```
apps/
  base/            base models, mixins, exception handler, storage, health check
  authentication/  user model with role, login, user management, RBAC permissions
  document/        document model, upload validation, filters, API
core/              settings, urls, wsgi/asgi
general/           enums (error codes and messages), constants, utils
nginx/             Nginx image and config
```

Business logic lives in services (`UserServices`, `DocumentServices`);
viewsets choose serializers, permissions and throttles per action through
`BaseMixin`.

## Configuration

Copy `env.sample` to `.env` and fill it in. Never commit `.env`.

| Variable                      | Description                                   |
|-------------------------------|-----------------------------------------------|
| `DEBUG`                       | `True` / `False` (default `False`)            |
| `SECRET_KEY`                  | Django secret key                             |
| `ALLOWED_HOSTS`               | Comma separated hosts (default `*`)           |
| `POSTGRES_HOST` `POSTGRES_PORT` `POSTGRES_DB` `POSTGRES_USER` `POSTGRES_PASSWORD` | PostgreSQL connection |
| `REDIS_HOST` `REDIS_PORT`     | Redis connection                              |
| `AWS_S3_ENDPOINT_URL`         | MinIO endpoint, e.g. `http://minio:9000`      |
| `AWS_ACCESS_KEY_ID` `AWS_SECRET_ACCESS_KEY` | MinIO credentials               |
| `AWS_STORAGE_BUCKET_NAME`     | Bucket for documents (must exist)             |
| `DOCUMENT_URL_EXPIRE_SECONDS` | Lifetime of document URLs (default `300`)     |

Document URLs are signed for the host in `AWS_S3_ENDPOINT_URL`. That host
must be reachable by the API clients, not only inside the Docker network.

## Run for development

Start PostgreSQL, Redis and MinIO:

```bash
docker compose -f docker-compose.dev.yml up -d
```

Create the bucket once: open the MinIO console at http://localhost:9001, log
in with the credentials from the compose file and create a bucket named like
`AWS_STORAGE_BUCKET_NAME`.

Run the API:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp env.sample .env      # POSTGRES_HOST=localhost, REDIS_HOST=localhost,
                        # AWS_S3_ENDPOINT_URL=http://localhost:9000
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Run with Docker (Gunicorn + Nginx)

```bash
cp env.sample .env      # POSTGRES_HOST=postgres, REDIS_HOST=redis
docker compose -f docker-compose.prod.yml up --build -d
docker compose -f docker-compose.prod.yml exec api python manage.py createsuperuser
```

This starts `api` (Gunicorn, port 8000 inside the network), `nginx` (port 80),
`postgres` and `redis`. The container entrypoint waits for PostgreSQL, applies
migrations and collects static files before starting the server. MinIO is not
part of this compose file: point `AWS_S3_ENDPOINT_URL` to a running MinIO with
the bucket created.

## API overview

Interactive docs: `/swagger/`, `/redoc/`; raw schema: `/schema/`.
Health: `/health/live/`, `/health/ready/` (checks database and Redis).

| Method | Path                      | Access          | Description                   |
|--------|---------------------------|-----------------|-------------------------------|
| POST   | `/v1/auth/pass/login/`    | public          | Login, returns access/refresh |
| POST   | `/v1/auth/refresh/`       | public          | Refresh access token          |
| GET    | `/v1/auth/pass/me/`       | authenticated   | Current user                  |
| GET    | `/v1/auth/users/`         | admin           | List users                    |
| POST   | `/v1/auth/users/`         | admin           | Create user with role         |
| GET    | `/v1/auth/users/{id}/`    | admin           | Retrieve user                 |
| PATCH  | `/v1/auth/users/{id}/`    | admin           | Change role / active status   |
| GET    | `/v1/dms/docs/`           | any role        | List (filter, search, order)  |
| POST   | `/v1/dms/docs/`           | admin, editor   | Upload (multipart)            |
| GET    | `/v1/dms/docs/{id}/`      | any role        | Retrieve with secure `url`    |
| PATCH  | `/v1/dms/docs/{id}/`      | admin, editor   | Update title/description/file |
| DELETE | `/v1/dms/docs/{id}/`      | admin           | Soft delete                   |

Role values: `1` admin, `2` editor, `3` viewer.

### Examples

```bash
# login
curl -X POST http://localhost:8000/v1/auth/pass/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"..."}'

# create an editor (admin only)
curl -X POST http://localhost:8000/v1/auth/users/ \
  -H "Authorization: Bearer <access>" -H "Content-Type: application/json" \
  -d '{"username":"ed","email":"ed@example.com","password":"Str0ng-pass!","role":2}'

# upload
curl -X POST http://localhost:8000/v1/dms/docs/ \
  -H "Authorization: Bearer <access>" \
  -F "title=Contract" -F "description=Signed copy" -F "file=@contract.pdf"

# list with filters
curl "http://localhost:8000/v1/dms/docs/?search=contract&content_type=application/pdf&ordering=-size&page_size=10" \
  -H "Authorization: Bearer <access>"
```

List filters: `title`, `file_name`, `owner` (username), `content_type`,
`min_size`, `max_size`, `created_from`, `created_to` (ISO datetime), `search`
(title, description, file name), `ordering` (`created_at`, `size`, `title`),
`page`, `page_size` (default 20, max 100).

Errors use a common format: `{"success": false, "code": "...", "detail": ...}`.

## Security notes

- Files are stored in a private bucket. The API returns a presigned URL that
  expires after `DOCUMENT_URL_EXPIRE_SECONDS`, and only to users allowed to
  retrieve the document.
- Stored object names are generated (`documents/<owner_id>/<uuid>.<ext>`);
  the original file name is kept only as metadata.
- Uploads are limited to 10 MB and to PDF, JPEG, PNG, plain text and Word
  (`.doc`) files. The content type comes from the upload request; add content
  sniffing (e.g. `python-magic`) for stricter validation.
- Login is rate limited to 10 requests per minute per IP; unknown users and
  wrong passwords return the same error. Other endpoints: 20/min anonymous,
  120/min authenticated.
- Access and refresh tokens are valid for 1 day (`SIMPLE_JWT` in settings).
- Role checks are enforced per action; actions that are not declared on a
  viewset do not exist.
- Passwords are hashed with Argon2 and validated with Django's validators.

## Tests

```bash
python manage.py test
# or inside the container
docker compose -f docker-compose.prod.yml exec api python manage.py test
```

Tests use in-memory file storage and a local-memory cache, so MinIO and Redis
are not needed. A PostgreSQL database is required, and its user must be able
to create the test database.

## Design decisions

- Role is a field on the user model (three fixed roles).
- All roles can see all documents; roles control actions, not ownership.
- Deleting a document is a soft delete and the stored file is kept. Replacing
  a document's file removes the old object.
- `PUT` is disabled; documents are changed with `PATCH`.
- Timezone is `Asia/Tehran` with `USE_TZ = False`.

## Not implemented

Audit logging, background task processing (a Celery app is configured but has
no tasks) and WebSocket notifications with Django Channels are not part of
this version.