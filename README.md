# Django News API Backend

This is a Django REST API backend that fetches and serves news articles from NewsAPI.

## Prerequisites

- Python 3.11+
- PostgreSQL (for local development)
- Docker & Docker Compose (for containerized deployment)
- NewsAPI key from [newsapi.org](https://newsapi.org)

## Environment Variables

Create a `.env` file in the backend directory with:

```bash
# Database
DB_NAME=django_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Django
DJANGO_SETTINGS_MODULE=conf.settings.dev
SECRET_KEY=your-secret-key-here
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# NewsAPI
NEWSAPI_KEY=your-newsapi-key-here

# Email
DEFAULT_FROM_EMAIL=your-email@example.com

# Timezone
TZ=UTC

# Port
PORT=8000
```

## Running with pip (Local Development)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Database

Make sure PostgreSQL is running with the database configured in your `.env` file.

### 3. Run Migrations

```bash
python manage.py migrate
```

### 4. Populate Initial Data

```bash
python manage.py populate_countries
python manage.py populate_sources
```

### 5. Generate API Schema

```bash
python manage.py spectacular --color --file schema.yml
```

### 6. Start Background Tasks (Optional)

```bash
python manage.py start_background_tasks
```

### 7. Run Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

## Running with Docker

### 1. Build and Start Services

```bash
docker-compose up --build
```

This will:

- Build the Django application
- Start PostgreSQL database
- Wait for database to be ready
- Run migrations automatically
- Populate countries and sources
- Start background tasks
- Start the Django development server

### 2. Access the Application

- API: `http://localhost:8000`
- Admin: `http://localhost:8000/admin`
- API Documentation: `http://localhost:8000/api/schema/swagger-ui/`

### 3. Useful Docker Commands

```bash
# View logs
docker-compose logs -f django

# Stop services
docker-compose down

# Rebuild and restart
docker-compose down && docker-compose up --build

# Access Django shell
docker-compose exec django python manage.py shell

# Run management commands
docker-compose exec django python manage.py <command>
```

## API Endpoints

- `GET /api/countries/` - List all countries
- `GET /api/sources/` - List all news sources
- `GET /api/articles/` - List articles with filtering options
- `GET /api/schema/swagger-ui/` - API documentation

## Management Commands

- `populate_countries` - Populate countries from hardcoded list
- `populate_sources` - Fetch and populate news sources from NewsAPI
- `start_background_tasks` - Initialize background news fetching tasks

## Troubleshooting

### Database Connection Issues

- Ensure PostgreSQL is running
- Check database credentials in `.env`
- For Docker: Use `docker-compose logs db` to check database logs

### NewsAPI Issues

- Verify your `NEWSAPI_KEY` is valid
- Check API rate limits (1000 requests/day for free tier)
- Ensure you're not hitting the API too frequently

### Background Tasks Not Working

- Background tasks require the Django server to be running
- Check logs for any task-related errors
- Tasks run every 10 minutes by default
