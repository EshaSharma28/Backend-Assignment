# HireHub: Integrated CRM & HRMS Backend

HireHub is a production-hardened Flask backend that bridges Customer Relationship Management (CRM) and Human Resource Management (HRMS) into a unified, secure ecosystem.

---

## Quick Start

### Prerequisites
*   Docker & Docker Compose (Recommended)
*   Python 3.11+
*   PostgreSQL 15+

### Environment Variables
Configure your environment by creating a `.env` file in the root directory:
```bash
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secure-random-string
DATABASE_URL=postgresql://user:password@localhost:5432/hirehub_db
```

### Deployment via Docker
The system is pre-configured with a Gunicorn server and security-hardened container settings.
```bash
# Start the entire stack (PostgreSQL + App)
docker-compose up --build
```
The API will be available at `http://localhost:5000`.

### Manual Setup
1.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Initialize Database Schema**:
    ```bash
    flask db upgrade
    ```
3.  **Seed RBAC Roles & Permissions**:
    ```bash
    python3 seed.py
    ```
4.  **Run Development Server**:
    ```bash
    flask run
    ```

---

## Usage & Documentation

### API Base URL
*   Development: `http://localhost:5000/api`
*   **Auth Flow**: Most endpoints require a Bearer Token.
    1.  `POST /auth/register` (New users default to the 'Sales' role)
    2.  `POST /auth/login` (Returns a JWT token)
    3.  Add `Authorization: Bearer <token>` to your request headers.

### Postman Collection
A comprehensive collection is included: `HireHub_API_Collection.json`.
*   Import this into Postman to see all 26 endpoints.
*   Pre-configured variables handle the JWT token automatically after login.

### Testing
Verify security and integration logic by running:
```bash
pytest
```

---

## Technical Architecture

### 1. System Design
HireHub utilizes the Application Factory Pattern with modular Blueprints. This architecture ensures maintainability and allows for clean environment-specific configurations.

<img width="496" height="513" alt="image" src="https://github.com/user-attachments/assets/021c45da-2c39-437c-a3cf-c2a9ccd22a92" />

### 2. Data Modeling
The database links HR data (Employees) directly to Sales outcomes (Leads) with strict relational integrity.
*   **Data Scoping**: Sales agents are restricted to viewing only their assigned leads.
*   **Business Constraints**: Leads can only be assigned to employees where `is_sales_agent` is set to True.

<img width="799" height="635" alt="image" src="https://github.com/user-attachments/assets/3d9e7c61-c389-4357-a2c7-949eacbe39f2" />

---

## Security & Production Notes

*   **Production WSGI**: In Docker, the app runs via Gunicorn with multiple workers and threads for concurrent request handling.
*   **Non-Root Execution**: The Docker container runs as a dedicated `hirehub` user for enhanced security.
*   **RBAC**: A custom Scope + Permission matrix (e.g., `leave:can_write`) handles access control.
*   **Secrets**: Safe fallback mechanisms have been removed; the application will fail if `SECRET_KEY` is not provided.

---

## Troubleshooting
*   **DB Connection Error**: Ensure PostgreSQL is running and the DATABASE_URL in .env is correct.
*   **401 Unauthorized**: Ensure your Bearer token is fresh and included in the header.
*   **Docker Port Conflict**: If port 5000 is busy, change the mapping in docker-compose.yml.
