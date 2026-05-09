# HireHub: Integrated CRM & HRMS Backend

HireHub is a production-hardened Flask backend that bridges Customer Relationship Management (CRM) and Human Resource Management (HRMS) into a unified, secure ecosystem.

---

## 🚀 Quick Start

### **Prerequisites**
*   **Docker & Docker Compose** (Recommended)
*   **Python 3.11+** (For manual setup)
*   **PostgreSQL 15+** (For manual setup)

### **Environment Variables**
Create a `.env` file in the root directory:
```bash
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secure-random-string
DATABASE_URL=postgresql://user:password@localhost:5432/hirehub_db
```

### **Deployment via Docker (Recommended)**
The system is pre-configured with a production-grade Gunicorn server.
```bash
# Start the entire stack (PostgreSQL + App)
docker-compose up --build
```
*The API will be available at `http://localhost:5000`.*

### **Manual Setup**
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

## 🛠 Usage & Documentation

### **API Base URL**
*   **Development**: `http://localhost:5000/api`
*   **Auth Flow**: Most endpoints require a **Bearer Token**.
    1.  `POST /auth/register` (New users are 'Sales' by default)
    2.  `POST /auth/login` (Returns a JWT token)
    3.  Add `Authorization: Bearer <token>` to your request headers.

### **Postman Collection**
A comprehensive collection is included: `HireHub_API_Collection.json`.
*   Import it into Postman to see all 26 endpoints.
*   Pre-configured variables will automatically handle the JWT token once you log in.

### **Testing**
Run the automated test suite to verify security and integration logic:
```bash
pytest
```

---

## 🏗 Technical Architecture

### **1. System Design**
HireHub uses the **Application Factory Pattern** with **Modular Blueprints**. This ensures the codebase remains maintainable and allows for environment-specific configurations.

<img width="496" height="513" alt="image" src="https://github.com/user-attachments/assets/021c45da-2c39-437c-a3cf-c2a9ccd22a92" />

### **2. Data Modeling**
The database is designed with strict relational integrity, linking HR data (Employees) directly to Sales outcomes (Leads).
*   **Data Scoping**: Sales agents are restricted to viewing only their assigned leads.
*   **Business Constraints**: Leads can only be assigned to employees where `is_sales_agent=True`.

<img width="799" height="635" alt="image" src="https://github.com/user-attachments/assets/3d9e7c61-c389-4357-a2c7-949eacbe39f2" />

---

## 🛡 Security & Production Notes

*   **Production WSGI**: In Docker, the app runs via **Gunicorn** with 4 workers and 2 threads per worker for concurrent request handling.
*   **Non-Root Execution**: The Docker container runs as a dedicated `hirehub` user, adhering to the principle of least privilege.
*   **RBAC**: A custom Scope + Permission matrix (e.g., `leave:can_write`) handles access control.
*   **Secrets**: Safe fallback mechanisms have been removed; the app will fail-fast if `SECRET_KEY` is missing in production.

---

## ❓ Troubleshooting
*   **DB Connection Error**: Ensure PostgreSQL is running and the `DATABASE_URL` in `.env` is correct.
*   **401 Unauthorized**: Ensure your Bearer token is fresh and included in the `Authorization` header.
*   **Docker Port Conflict**: If port 5000 is busy, change the mapping in `docker-compose.yml` (e.g., `"5001:5000"`).
