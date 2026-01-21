# Gym Flow Backend

This is the backend API for the Gym Flow application, built with Flask and SQLAlchemy. It provides endpoints for user authentication, workout logging, attendance tracking, and admin reporting features.

## Features
- User authentication with JWT
- Member and workout management
- Attendance tracking
- Admin-only reports and dashboard endpoints (aggregations, CSV export, pagination)
- Automated tests with pytest
- CI workflow for backend tests

## Setup
1. **Clone the repository**
2. **Create a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install psycopg2-binary pytest
   ```
4. **Set environment variables:**
   - `SQLALCHEMY_DATABASE_URI` (default: local Postgres, override for tests)
   - `JWT_SECRET_KEY`
5. **Run the app:**
   ```bash
   flask run
   ```
6. **Run tests:**
   ```bash
   PYTHONPATH=. SQLALCHEMY_DATABASE_URI=sqlite:///:memory: .venv/bin/pytest -q
   ```

## API Documentation
- Swagger UI available at `/api/docs` when running the app.

## Contributors
- Allan Ratemo
- Branice Nashilu
- Derrick Koome
- Kennedy Ng'ang'a
- Linda Chepchieng

---
MIT License
