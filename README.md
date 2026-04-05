# Finance Dashboard System — Backend API

A robust, secure REST API backend for a finance dashboard built with **Python / Flask** and **MySQL**. Features **Role-Based Access Control (RBAC)**, JWT authentication, financial record CRUD, aggregated analytics, and Swagger UI documentation.

---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Project Structure](#project-structure)
3. [Prerequisites](#prerequisites)
4. [Environment Setup](#environment-setup)
5. [Running the Server](#running-the-server)
6. [Authentication & RBAC](#authentication--rbac)
7. [API Reference](#api-reference)
   - [Auth Endpoints](#auth-endpoints-apiauth)
   - [User Management Endpoints](#user-management-endpoints-apiusers)
   - [Financial Records Endpoints](#financial-records-endpoints-apirecords)
   - [Dashboard Endpoints](#dashboard-endpoints-apidashboard)
8. [Request & Response Examples](#request--response-examples)
9. [Validation Rules](#validation-rules)
10. [Error Handling](#error-handling)
11. [Swagger UI](#swagger-ui)
12. [Database Models](#database-models)

---

## Tech Stack

| Layer          | Technology                    |
|----------------|-------------------------------|
| Language       | Python 3.10+                  |
| Framework      | Flask 3.0                     |
| ORM            | Flask-SQLAlchemy + SQLAlchemy |
| DB Migrations  | Flask-Migrate (Alembic)       |
| Database       | MySQL (via PyMySQL driver)    |
| Auth           | Flask-JWT-Extended (JWT)      |
| Validation     | Marshmallow                   |
| API Docs       | Flasgger (Swagger UI)         |
| Config         | python-dotenv                 |

---

## Project Structure

```
Finance_dashboard_system/
├── run.py                      # Entry point — starts server & seeds DB
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not committed)
└── app/
    ├── __init__.py             # App factory (create_app)
    ├── config.py               # Config classes (Dev / Prod / Testing)
    ├── extensions.py           # Shared extension instances (db, jwt, etc.)
    ├── blueprints/
    │   ├── auth.py             # /api/auth  — Register, Login, Refresh
    │   ├── users.py            # /api/users — User management (Admin)
    │   ├── records.py          # /api/records — Financial CRUD
    │   └── dashboard.py        # /api/dashboard — Analytics & summaries
    ├── models/
    │   ├── user.py             # User model + RoleEnum
    │   └── financial_record.py # FinancialRecord model + RecordTypeEnum
    ├── middleware/
    │   └── auth_middleware.py  # JWT + RBAC decorators
    └── utils/
        └── validators.py       # Marshmallow schemas for all inputs
```

---

## Prerequisites

- Python 3.10 or higher
- MySQL 8.0 or higher (running locally or remotely)
- `pip` and optionally `virtualenv`

---

## Environment Setup

### 1. Clone and create virtual environment

```bash
git clone <your-repo-url>
cd Finance_dashboard_system

python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create the MySQL database

```sql
CREATE DATABASE finance_dashboard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
# Flask
SECRET_KEY=your-very-secret-key
FLASK_ENV=development

# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=finance_dashboard

# JWT
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600       # seconds (default: 1 hour)
JWT_REFRESH_TOKEN_EXPIRES=604800    # seconds (default: 7 days)
```

---

## Running the Server

### Initialize the database and seed the default admin user

```bash
python run.py init-db
```

This creates all tables and seeds a default **admin** user:

| Field    | Value             |
|----------|-------------------|
| Username | `admin`           |
| Password | `admin123`        |
| Role     | `admin`           |
| Email    | admin@example.com |

> **Note:** Change the default admin password immediately in production.

### Start the development server

```bash
python run.py
```

The API will be available at: **`http://localhost:5000`**

### Using Flask CLI (alternative)

```bash
flask --app run init-db   # Initialize DB
flask --app run run       # Start server
```

---

## Authentication & RBAC

### How Authentication Works

1. **Register** a user via `POST /api/auth/register`.
2. **Login** via `POST /api/auth/login` — you receive an `access_token` and a `refresh_token`.
3. **Include the token** in every protected request as an HTTP header:
   ```
   Authorization: Bearer <your_access_token>
   ```
4. When the access token expires, use `POST /api/auth/refresh` with the refresh token to get a new access token.

### Roles & Permissions

The system implements three roles with hierarchical permissions:

| Role       | Description                                                    |
|------------|----------------------------------------------------------------|
| `viewer`   | Read-only access to financial records and recent activity      |
| `analyst`  | Everything viewer can do + dashboard summary + monthly trends  |
| `admin`    | Full access — CRUD on records, user management, all analytics  |

### Permission Matrix

| Endpoint                              | Viewer | Analyst | Admin |
|---------------------------------------|:------:|:-------:|:-----:|
| `GET /api/records/`                   | Yes    | Yes     | Yes   |
| `GET /api/records/<id>`               | Yes    | Yes     | Yes   |
| `POST /api/records/`                  | No     | No      | Yes   |
| `PUT /api/records/<id>`               | No     | No      | Yes   |
| `DELETE /api/records/<id>`            | No     | No      | Yes   |
| `GET /api/dashboard/recent`           | Yes    | Yes     | Yes   |
| `GET /api/dashboard/summary`          | No     | Yes     | Yes   |
| `GET /api/dashboard/trends/monthly`   | No     | Yes     | Yes   |
| `GET /api/users/profile`              | Yes    | Yes     | Yes   |
| `GET /api/users/`                     | No     | No      | Yes   |
| `PUT /api/users/<id>`                 | No     | No      | Yes   |
| `PATCH /api/users/<id>/status`        | No     | No      | Yes   |
| `DELETE /api/users/<id>`              | No     | No      | Yes   |

---

## API Reference

> All request bodies must be `Content-Type: application/json`.  
> All protected routes require `Authorization: Bearer <token>` header.

---

### Auth Endpoints (`/api/auth`)

#### `POST /api/auth/register`

Register a new user account.

**Auth required:** No

**Request Body:**

| Field       | Type   | Required | Description                                        |
|-------------|--------|----------|----------------------------------------------------|
| `username`  | string | Yes      | 3-80 characters, must be unique                    |
| `email`     | string | Yes      | Valid email address, must be unique                |
| `password`  | string | Yes      | 6-128 characters                                   |
| `full_name` | string | No       | Up to 150 characters                               |
| `role`      | string | No       | `viewer` / `analyst` / `admin` (default: `viewer`) |

**Response `201 Created`:**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 2,
    "username": "johndoe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "viewer",
    "is_active": true,
    "created_at": "2024-04-01T10:00:00",
    "updated_at": "2024-04-01T10:00:00"
  }
}
```

---

#### `POST /api/auth/login`

Login and receive JWT tokens.

**Auth required:** No

**Request Body:**

| Field      | Type   | Required | Description         |
|------------|--------|----------|---------------------|
| `username` | string | Yes      | Registered username |
| `password` | string | Yes      | Account password    |

**Response `200 OK`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "System Administrator",
    "role": "admin",
    "is_active": true,
    "created_at": "2024-04-01T09:00:00",
    "updated_at": "2024-04-01T09:00:00"
  }
}
```

**Error `401 Unauthorized`:**
```json
{ "error": "Invalid username or password" }
```

---

#### `POST /api/auth/refresh`

Get a new access token using a refresh token.

**Auth required:** Yes (Refresh Token in `Authorization` header)

**Response `200 OK`:**
```json
{ "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." }
```

---

### User Management Endpoints (`/api/users`)

#### `GET /api/users/`

Get list of all active (non-deleted) users.

**Auth required:** Admin only

**Response `200 OK`:**
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "System Administrator",
    "role": "admin",
    "is_active": true,
    "created_at": "2024-04-01T09:00:00",
    "updated_at": "2024-04-01T09:00:00"
  }
]
```

---

#### `GET /api/users/profile`

Get the profile of the currently authenticated user.

**Auth required:** Any authenticated role

**Response `200 OK`:** Same as a single user object above.

---

#### `PUT /api/users/<id>`

Update a user's profile details.

**Auth required:** Admin only

**URL Parameter:** `id` (integer) — ID of the user to update

**Request Body (all fields optional):**

| Field       | Type    | Description                          |
|-------------|---------|--------------------------------------|
| `email`     | string  | New email address (must be unique)   |
| `full_name` | string  | Up to 150 characters                 |
| `role`      | string  | `viewer` / `analyst` / `admin`       |
| `is_active` | boolean | Activate or deactivate the account   |

**Response `200 OK`:**
```json
{
  "message": "User updated successfully",
  "user": { ... }
}
```

---

#### `PATCH /api/users/<id>/status`

Toggle a user's active/inactive status.

**Auth required:** Admin only

**URL Parameter:** `id` (integer)

**Request Body:**

| Field       | Type    | Required | Description                              |
|-------------|---------|----------|------------------------------------------|
| `is_active` | boolean | Yes      | `true` to activate, `false` to deactivate |

**Response `200 OK`:**
```json
{
  "message": "User activated successfully",
  "user": { ... }
}
```

---

#### `DELETE /api/users/<id>`

Soft-delete a user (sets `is_deleted = true`; data is retained in DB).

**Auth required:** Admin only

**URL Parameter:** `id` (integer)

> **Note:** An admin cannot delete their own account.

**Response `200 OK`:**
```json
{ "message": "User deleted successfully" }
```

---

### Financial Records Endpoints (`/api/records`)

#### `POST /api/records/`

Create a new financial record.

**Auth required:** Admin only

**Request Body:**

| Field         | Type   | Required | Description                                    |
|---------------|--------|----------|------------------------------------------------|
| `amount`      | number | Yes      | Positive decimal with up to 2 decimal places   |
| `record_type` | string | Yes      | `income` or `expense`                          |
| `category`    | string | Yes      | 1-100 characters (e.g. "Salary", "Rent")       |
| `record_date` | string | Yes      | Date in `YYYY-MM-DD` format (cannot be future) |
| `description` | string | No       | Optional notes, up to 1000 characters          |

**Response `201 Created`:**
```json
{
  "message": "Record created successfully",
  "record": {
    "id": 5,
    "amount": 1500.00,
    "record_type": "income",
    "category": "Salary",
    "record_date": "2024-04-01",
    "description": "Monthly paycheck",
    "created_by_id": 1,
    "created_at": "2024-04-01T10:30:00",
    "updated_at": "2024-04-01T10:30:00"
  }
}
```

---

#### `GET /api/records/`

Retrieve all financial records with optional filters and search.

**Auth required:** Any authenticated role

**Query Parameters (all optional):**

| Parameter     | Type   | Description                                                  |
|---------------|--------|--------------------------------------------------------------|
| `record_type` | string | Filter by `income` or `expense`                              |
| `category`    | string | Case-insensitive partial match                               |
| `start_date`  | string | `YYYY-MM-DD` — include records on or after this date         |
| `end_date`    | string | `YYYY-MM-DD` — include records on or before this date        |
| `search`      | string | Partial search across `category` and `description` fields    |

**Example Request:**
```
GET /api/records/?record_type=expense&start_date=2024-01-01&end_date=2024-03-31&search=rent
```

**Response `200 OK`:**
```json
{
  "total": 2,
  "records": [
    {
      "id": 3,
      "amount": 800.00,
      "record_type": "expense",
      "category": "Rent",
      "record_date": "2024-03-01",
      "description": "Monthly rent",
      "created_by_id": 1,
      "created_at": "2024-03-01T09:00:00",
      "updated_at": "2024-03-01T09:00:00"
    }
  ]
}
```

---

#### `GET /api/records/<id>`

Get a single financial record by its ID.

**Auth required:** Any authenticated role

**URL Parameter:** `id` (integer)

**Response `200 OK`:** Single record object (same shape as above).

**Response `404 Not Found`:**
```json
{ "error": "Record not found" }
```

---

#### `PUT /api/records/<id>`

Update an existing financial record.

**Auth required:** Admin only

**URL Parameter:** `id` (integer)

**Request Body (all fields optional):**

| Field         | Type   | Description                          |
|---------------|--------|--------------------------------------|
| `amount`      | number | Positive decimal                     |
| `record_type` | string | `income` or `expense`                |
| `category`    | string | 1-100 characters                     |
| `record_date` | string | `YYYY-MM-DD` (cannot be future date) |
| `description` | string | Up to 1000 characters                |

**Response `200 OK`:**
```json
{
  "message": "Record updated successfully",
  "record": { ... }
}
```

---

#### `DELETE /api/records/<id>`

Soft-delete a financial record (data is retained; `is_deleted` flag is set).

**Auth required:** Admin only

**URL Parameter:** `id` (integer)

**Response `200 OK`:**
```json
{ "message": "Record soft-deleted successfully" }
```

---

### Dashboard Endpoints (`/api/dashboard`)

#### `GET /api/dashboard/summary`

Aggregated financial summary: totals, net balance, category breakdown, and 5 most recent records.

**Auth required:** Analyst or Admin

**Response `200 OK`:**
```json
{
  "total_income": 15000.00,
  "total_expenses": 8500.00,
  "net_balance": 6500.00,
  "category_wise_totals": {
    "Salary": { "income": 12000.00, "expense": 0 },
    "Freelance": { "income": 3000.00, "expense": 0 },
    "Rent": { "income": 0, "expense": 5000.00 },
    "Utilities": { "income": 0, "expense": 3500.00 }
  },
  "recent_activity": [
    {
      "id": 10,
      "amount": 500.00,
      "record_type": "expense",
      "category": "Utilities",
      "record_date": "2024-04-01",
      "description": "Electric bill",
      "created_by_id": 1,
      "created_at": "2024-04-01T14:00:00",
      "updated_at": "2024-04-01T14:00:00"
    }
  ]
}
```

---

#### `GET /api/dashboard/trends/monthly`

Month-by-month income vs. expense breakdown for a given year.

**Auth required:** Analyst or Admin

**Query Parameters:**

| Parameter | Type    | Required | Default      | Description               |
|-----------|---------|----------|--------------|---------------------------|
| `year`    | integer | No       | Current year | Year to retrieve data for |

**Example:** `GET /api/dashboard/trends/monthly?year=2024`

**Response `200 OK`:**
```json
{
  "year": 2024,
  "trends": [
    { "month": 1, "income": 4000.00, "expense": 2500.00 },
    { "month": 2, "income": 5000.00, "expense": 3000.00 },
    { "month": 3, "income": 6000.00, "expense": 3000.00 }
  ]
}
```

> `month` is a number from 1 (January) to 12 (December). Only months with data are included.

---

#### `GET /api/dashboard/recent`

Get the most recently created financial records.

**Auth required:** Any authenticated role

**Query Parameters:**

| Parameter | Type    | Required | Default | Description                            |
|-----------|---------|----------|---------|----------------------------------------|
| `limit`   | integer | No       | 10      | Number of records to return (max: 100) |

**Example:** `GET /api/dashboard/recent?limit=5`

**Response `200 OK`:**
```json
{
  "records": [
    {
      "id": 10,
      "amount": 500.00,
      "record_type": "expense",
      "category": "Utilities",
      "record_date": "2024-04-01",
      "description": "Electric bill",
      "created_by_id": 1,
      "created_at": "2024-04-01T14:00:00",
      "updated_at": "2024-04-01T14:00:00"
    }
  ]
}
```

---

## Request & Response Examples

### Quick Start: Login and Create a Record

**Step 1 — Login**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

**Step 2 — Use the returned token to create a record**
```bash
curl -X POST http://localhost:5000/api/records/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_access_token>" \
  -d '{
    "amount": 1500.00,
    "record_type": "income",
    "category": "Salary",
    "record_date": "2024-04-01",
    "description": "Monthly paycheck"
  }'
```

**Step 3 — View dashboard summary (as analyst/admin)**
```bash
curl http://localhost:5000/api/dashboard/summary \
  -H "Authorization: Bearer <your_access_token>"
```

---

## Validation Rules

All inputs are validated with [Marshmallow](https://marshmallow.readthedocs.io/) before processing.

| Field         | Rules                                                      |
|---------------|------------------------------------------------------------|
| `username`    | Required, string, 3-80 chars                               |
| `email`       | Required, valid email format                               |
| `password`    | Required, 6-128 characters                                 |
| `role`        | One of: `viewer`, `analyst`, `admin`                       |
| `amount`      | Required, decimal >= 0.01, max 2 decimal places            |
| `record_type` | Required, one of: `income`, `expense`                      |
| `category`    | Required, 1-100 characters                                 |
| `record_date` | Required, `YYYY-MM-DD` format, cannot be a future date     |
| `description` | Optional, max 1000 characters                              |

Validation errors return a structured `400` response:
```json
{
  "error": "Validation failed",
  "details": {
    "amount": ["Amount must be greater than 0."],
    "record_date": ["record_date cannot be in the future."]
  }
}
```

---

## Error Handling

All error responses follow a consistent JSON structure.

| HTTP Code | Meaning                        | Example Body                                                   |
|-----------|--------------------------------|----------------------------------------------------------------|
| `400`     | Bad request / validation error | `{"error": "Validation failed", "details": {...}}`             |
| `401`     | Unauthorized / bad token       | `{"error": "Missing or invalid token", "detail": "..."}`       |
| `403`     | Forbidden / insufficient role  | `{"error": "Access denied", "detail": "Requires admin role"}`  |
| `404`     | Resource not found             | `{"error": "Record not found"}`                                |
| `405`     | Method not allowed             | `{"error": "Method not allowed"}`                              |
| `500`     | Internal server error          | `{"error": "Internal server error"}`                           |

---

## Swagger UI

Interactive API documentation is available via **Swagger UI** when the server is running:

```
http://localhost:5000/api/docs/
```

You can use the Swagger UI to:
- Browse all endpoints and their parameters
- Execute live API requests directly from the browser
- Authorize with a Bearer token using the lock button in the top right

---

## Database Models

### `users` table

| Column          | Type         | Notes                              |
|-----------------|--------------|------------------------------------|
| `id`            | INT (PK)     | Auto-increment                     |
| `username`      | VARCHAR(80)  | Unique, indexed                    |
| `email`         | VARCHAR(150) | Unique, indexed                    |
| `password_hash` | VARCHAR(256) | Werkzeug bcrypt hash               |
| `full_name`     | VARCHAR(150) | Nullable                           |
| `role`          | ENUM         | `viewer` / `analyst` / `admin`     |
| `is_active`     | BOOLEAN      | Default `true`                     |
| `is_deleted`    | BOOLEAN      | Soft-delete flag, default `false`  |
| `created_at`    | DATETIME     | UTC timestamp                      |
| `updated_at`    | DATETIME     | Auto-updated on change             |
| `deleted_at`    | DATETIME     | Nullable, set on soft delete       |

### `financial_records` table

| Column          | Type          | Notes                                      |
|-----------------|---------------|--------------------------------------------|
| `id`            | INT (PK)      | Auto-increment                             |
| `amount`        | DECIMAL(15,2) | Up to 2 decimal places                     |
| `record_type`   | ENUM          | `income` / `expense`                       |
| `category`      | VARCHAR(100)  | Indexed                                    |
| `record_date`   | DATE          | Indexed, cannot be future                  |
| `description`   | TEXT          | Nullable                                   |
| `created_by_id` | INT (FK)      | References `users.id`                      |
| `is_deleted`    | BOOLEAN       | Soft-delete flag, indexed, default `false` |
| `deleted_at`    | DATETIME      | Nullable, set on soft delete               |
| `created_at`    | DATETIME      | UTC timestamp                              |
| `updated_at`    | DATETIME      | Auto-updated on change                     |

---

Built with Flask, SQLAlchemy, MySQL, and JWT.
