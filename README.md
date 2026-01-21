# Gym Flow Backend API

A comprehensive gym management system backend built with Flask. Track members, manage attendance, organize workouts, and generate detailed business analytics—all through a robust REST API with JWT authentication.

**Live API Documentation:** Visit `/api-docs` after running the server to explore endpoints interactively.

---

## Table of Contents

[Features](#features)
[Tech Stack](#tech-stack)
[Setup & Installation](#setup--installation)
[Running the Application](#running-the-application)
[API Endpoints](#api-endpoints)
[Architecture](#architecture)
[Contributing](#contributing)

---

## Features

### Authentication & Authorization
*Secure user management with role-based access control*

User registration and login with email/password
JWT token-based authentication on all protected endpoints
Password reset with secure token validation
Admin and user role system with permission enforcement
Automatic token expiration and validation
All sensitive endpoints require valid Bearer token

**Key Endpoints:**
`POST /api/auth/register` - Create new user account
`POST /api/auth/login` - Login and receive JWT token
`GET /api/auth/me` - Get authenticated user profile
`POST /api/auth/reset-password` - Request password reset
`POST /api/auth/reset-password/confirm` - Confirm with reset token

---

### Member Management
*Comprehensive member profile and membership tracking system*

Create, update, and manage gym member profiles with flexible membership options. Track membership status (active/inactive/expired/suspended) across three tiers: Basic, Premium, and VIP.

**Features:**
- Full member CRUD operations with validation
- Search members by name or email
- Filter by membership status and type
- Track membership dates and renewal status
- Emergency contact information storage
- Personal notes for each member
- Pagination support for large member lists
- Admin-only access to member management

**Key Endpoints:**
`GET /api/members` - List all members with filters (admin only)
`GET /api/members/<id>` - Get member details and history
`POST /api/members` - Create new member
`PUT /api/members/<id>` - Update member profile
`DELETE /api/members/<id>` - Remove member

**Example Member Response:**
```json
{
  "id": "uuid",
  "name": "John Doe",
  "email": "john@example.com",
  "membershipType": "premium",
  "membershipStatus": "active",
  "membershipStartDate": "2025-01-01T00:00:00",
  "membershipEndDate": "2025-12-31T00:00:00"
}
```

---

### Attendance Tracking
*Real-time check-in system for gym visits*

Record and track member gym visits with timestamps. Prevent duplicate same-day check-ins and maintain detailed attendance history for each member. Automatically generate daily attendance reports.

**Features:**
One-click member check-in with automatic timestamp
Duplicate check-in prevention (one check-in per member per day)
Retrieve member attendance history with customizable limit
Get all check-ins for the current day
View check-in patterns and trends
Staff member tracking (who processed the check-in)
ISO 8601 formatted timestamps for consistency

**Key Endpoints:**
- `POST /api/attendance/checkin` - Check in a member
- `GET /api/attendance/member/<member_id>` - Get member's check-in history
- `GET /api/attendance/today` - View today's check-ins (admin)
- `GET /api/attendance/history` - Paginated attendance history (admin)

**Example Check-in Response:**
```json
{
  "id": "uuid",
  "memberId": "member-uuid",
  "memberName": "John Doe",
  "checkInTime": "2025-01-21T14:30:00+00:00",
  "createdAt": "2025-01-21T14:30:00+00:00"
}
```

---

### Workout Management
*Track and organize member fitness activities and coaching sessions*

Coaches create and assign workouts to members. Organize by workout type, track duration and intensity, record exercises with detailed metrics (sets, reps, weight).

**Features:**
Multiple workout types: Strength Training, Cardio, HIIT, Yoga, Pilates, Swimming, CrossFit, Other
Record workout details: type, duration, calories, intensity level
Exercise tracking with sets, reps, and weight
Assign workouts to members with validation
Filter workouts by type, date range, and member
User-based access (coaches see their own workouts, admins see all)
Pagination for large workout lists
Flexible notes and metadata

**Key Endpoints:**
`GET /api/workouts/types` - Get available workout types
`GET /api/workouts` - List user's workouts with filters
`POST /api/workouts` - Create new workout
`PUT /api/workouts/<id>` - Update workout details
`DELETE /api/workouts/<id>` - Remove workout
`GET /api/workouts/<id>/members` - List members in workout
`POST /api/workouts/<id>/members` - Assign member to workout

**Example Workout:**
```json
{
  "id": "uuid",
  "userId": "coach-uuid",
  "memberId": "member-uuid",
  "type": "Strength Training",
  "duration": 60,
  "intensity": "high",
  "calories": 450,
  "exercises": [
    {
      "name": "Bench Press",
      "sets": 4,
      "reps": 8,
      "weight": 185
    }
  ],
  "date": "2025-01-21T14:00:00"
}
```

---

### Reports & Analytics
*Business intelligence and member activity insights*

Generate comprehensive reports on member engagement, revenue projections, attendance patterns, and fitness trends. Export data in multiple formats for further analysis.

**Features:**
Summary reports with key metrics (active members, revenue, check-ins)
Attendance frequency analysis with top members ranking
Workout activity breakdown by type
Member activity classification (active vs. inactive)
Revenue projections based on membership type
Monthly and yearly trend analysis
CSV export functionality for all reports
Date range filtering for custom reports
Pagination support for large datasets

**Key Endpoints:**
`GET /api/reports/summary` - Overview of gym operations
`GET /api/reports/members-activity` - Active vs. inactive member count
`GET /api/reports/attendance-trends` - Attendance patterns over time
`GET /api/reports/revenue` - Revenue projections and summaries
`GET /api/reports/workout-analysis` - Workout type breakdowns
`GET /api/reports/export` - Export reports as CSV

**Example Summary Report:**
```json
{
  "totalMembers": 150,
  "activeMembers": 120,
  "inactiveMembers": 30,
  "totalCheckinsThisMonth": 1250,
  "averageCheckinPerMember": 10.4,
  "projectedMonthlyRevenue": 4500,
  "membershipTypeBreakdown": {
    "basic": 50,
    "premium": 70,
    "vip": 30
  }
}
```

---

### 🔍 Admin Reports & Insights
*Advanced analytics for gym administrators with role-based access*

Exclusive admin-only reporting suite for in-depth business analysis. Track top-performing members, monitor attendance patterns, and analyze workout trends.

**Features:**
Attendance frequency ranking (top members by check-ins)
Attendance aggregation by days/time period
Workout summary with type distribution
Member activity scoring (active/inactive classification)
Duration averages and totals
CSV export for attendance and workout reports
Flexible date range queries
ZTop N results pagination

**Key Endpoints:**
`GET /api/admin/reports/attendance-frequency` - Top members by check-ins
`GET /api/admin/reports/workouts-summary` - Workout statistics
`GET /api/admin/reports/members-activity` - Member engagement levels

**Admin Report Example:**
```json
{
  "totalCheckins": 2500,
  "avgCheckinsPerMember": 16.7,
  "totalMembersWithActivity": 150,
  "topMembers": [
    {
      "memberId": "uuid",
      "memberName": "John Doe",
      "checkins": 45
    }
  ]
}
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Framework** | Flask (Python) |
| **Database** | SQLAlchemy ORM |
| **Authentication** | Flask-JWT-Extended |
| **API Documentation** | Flasgger (Swagger/OpenAPI) |
| **CORS** | Flask-CORS |
| **Password Hashing** | bcrypt |
| **Testing** | pytest |

---

## Setup & Installation

### Prerequisites
- Python 3.8+
- pip or pipenv
- Git

### Clone the Repository
```bash
git clone <repository-url>
cd gym-flow-back
```

### Install Dependencies

Using pip:
```bash
pip install -r requirements.txt
```

Or using pipenv:
```bash
pipenv install
pipenv shell
```

### Environment Variables

Create a `.env` file in the root directory:
```bash
FLASK_ENV=development
FLASK_APP=run.py
DATABASE_URL=sqlite:///gym_flow.db
JWT_SECRET_KEY=your-secret-key-here
```

### Database Setup

```bash
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

---

## Running the Application

### Development Server

```bash
flask run
```

The API will be available at `http://localhost:5000`

### Access API Documentation

Open your browser and navigate to:
```
http://localhost:5000/api-docs
```

### Run Tests

```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app tests/
```

---

## API Endpoints

### Authentication
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register` | ❌ | Register new user |
| POST | `/api/auth/login` | ❌ | Login user |
| GET | `/api/auth/me` | ✅ JWT | Get current user |
| POST | `/api/auth/reset-password` | ❌ | Request password reset |
| POST | `/api/auth/reset-password/confirm` | ❌ | Confirm password reset |

### Members
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/members` | ✅ Admin | List all members |
| GET | `/api/members/<id>` | ✅ JWT | Get member details |
| POST | `/api/members` | ✅ Admin | Create member |
| PUT | `/api/members/<id>` | ✅ Admin | Update member |
| DELETE | `/api/members/<id>` | ✅ Admin | Delete member |

### Attendance
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/attendance/checkin` | ✅ JWT | Check in member |
| GET | `/api/attendance/member/<id>` | ✅ JWT | Member history |
| GET | `/api/attendance/today` | ✅ Admin | Today's check-ins |
| GET | `/api/attendance/history` | ✅ Admin | All attendance |

### Workouts
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/workouts/types` | ✅ JWT | Available types |
| GET | `/api/workouts` | ✅ JWT | List workouts |
| POST | `/api/workouts` | ✅ JWT | Create workout |
| PUT | `/api/workouts/<id>` | ✅ JWT | Update workout |
| DELETE | `/api/workouts/<id>` | ✅ JWT | Delete workout |

### Reports
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/reports/summary` | ✅ Admin | Summary report |
| GET | `/api/reports/members-activity` | ✅ Admin | Member activity |
| GET | `/api/admin/reports/attendance-frequency` | ✅ Admin | Top members |
| GET | `/api/admin/reports/workouts-summary` | ✅ Admin | Workout stats |
| GET | `/api/admin/reports/members-activity` | ✅ Admin | Member engagement |

---

## Architecture

### Project Structure

```
gym-flow-back/
├── app/
│   ├── __init__.py              # App factory & configuration
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py          # Environment configuration
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth.py              # JWT validation & admin checks
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py              # User model (auth)
│   │   ├── member.py            # Member model
│   │   ├── attendance.py         # Attendance/check-in model
│   │   └── workout.py           # Workout model
│   └── routes/
│       ├── __init__.py
│       ├── auth.py              # Authentication endpoints
│       ├── members.py           # Member management endpoints
│       ├── attendance.py         # Check-in endpoints
│       ├── workouts.py          # Workout endpoints
│       ├── reports.py           # General reports
│       └── admin_reports.py     # Admin analytics
├── tests/
│   ├── conftest.py              # Test configuration & fixtures
│   ├── test_admin_reports.py    # Admin report tests
│   └── test_workouts.py         # Workout tests
├── requirements.txt             # Python dependencies
├── Pipfile                      # Pipenv configuration
└── run.py                       # Application entry point
```

### Data Flow

```
User Registration/Login
  ↓
JWT Token Generated
  ↓
Protected Endpoints (All require JWT)
  ├→ Member Management (CRUD)
  ├→ Attendance Check-ins
  ├→ Workout Creation & Assignment
  └→ Reports & Analytics
```

### Models & Relationships

```
User (Coaches/Staff)
  ├→ Workouts (created by user)
  └→ Can view Attendances (if admin)

Member
  ├→ Attendances (check-in records)
  └→ Workouts (assigned workouts)

Attendance
  ├→ Member (who checked in)
  └→ User (who processed check-in, optional)

Workout
  ├→ User (coach who created)
  └→ Member (participant)
```

---

## Contributing

When adding new features, please:

1. **Create a feature branch:** `git checkout -b feature/your-feature-name`
2. **Write tests** for your endpoints
3. **Update this README** with new endpoints and features
4. **Add inline comments** explaining your logic
5. **Submit a pull request** with a clear description

### Feature Guidelines

- All protected endpoints must use `@jwt_required()`
- Admin-only endpoints should use `@admin_required`
- Include Swagger documentation in route docstrings
- Write tests in `tests/` directory
- Follow existing code style and patterns

---

## License

This project is part of the SE Prep Phase 4 curriculum.

---

**Questions or Issues?** Open an issue on the repository or check the API documentation at `/api-docs`.

## Acknowledgements
- The emojis in this text were obtained from unicode emojis: (https://symbl.cc/en/search/?q=check)

This project was a collaboration.

## Contributors
- Kennedy Ng'ang'a
- Derrick Koome
- Linda Jerop
- Allan Ratemo
- Branice Nashilu