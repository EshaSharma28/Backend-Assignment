# HireHub: Integrated CRM & HRMS Backend

This is a professional-grade Flask backend that bridges Customer Relationship Management (CRM) and Human Resource Management (HRMS) into a unified ecosystem.

## **HireHub: Technical Architecture & Design Report**

### **1. System Design and Architecture Decisions**
*   **Application Factory Pattern**: We used the `create_app()` factory pattern. This ensures the app is highly scalable and allows for easy switching between environments (Development, Testing, Production) without changing the core code.
*   **Modular Blueprints**: Instead of a monolithic `routes.py`, we separated the logic into Blueprints (`auth`, `hrms`, `crm`, `performance`). This makes the codebase maintainable and allows different teams to work on different modules simultaneously.
*   **Separation of Concerns**: We strictly separated Models (Database structure), Schemas (Validation/Serialization), and Routes (Business Logic).


<img width="496" height="513" alt="image" src="https://github.com/user-attachments/assets/021c45da-2c39-437c-a3cf-c2a9ccd22a92" />

### **2. Data Modeling and Relationships**
*   **PostgreSQL Normalization**: We used a relational structure to ensure data integrity.
*   **Key Relationships**:
    *   **User ↔ Employee**: A 1:1 relationship where every authenticated user has a professional profile.
    *   **Employee ↔ Lead**: A 1:N relationship (one sales agent manages many leads).
    *   **Lead ↔ Interaction**: A 1:N relationship tracking every touchpoint (calls/meetings) for a specific lead.
*   **Integrity**: We used UUIDs for users to prevent ID enumeration attacks and PgEnum for restricted fields like Lead Status and Leave Types.

<img width="799" height="635" alt="image" src="https://github.com/user-attachments/assets/3d9e7c61-c389-4357-a2c7-949eacbe39f2" />

### **3. API Structure and Standards**
*   **RESTful Principles**: We used standard HTTP methods (GET for reading, POST for creating, PATCH for partial updates) and proper status codes (201 Created, 403 Forbidden, 400 Bad Request).
*   **Marshmallow Serialization**: We used Marshmallow schemas to ensure that all data entering or leaving the API is strictly validated and formatted consistently.
*   **Unified Error Handling**: Every request returns a consistent JSON error object (e.g., `{"message": "..."}`).

### **4. Code Quality and Modularity**
*   **DRY (Don't Repeat Yourself)**: Common logic, such as RBAC checks, was extracted into reusable decorators.
*   **Scalability**: The architecture is designed so that adding a new module (e.g., a "Payroll" module) would only require creating one new Blueprint and adding it to the factory.
*   **Type Hinting**: Python type hints were used where appropriate to improve code readability and IDE support.

### **5. Security Practices**
*   **JWT Authentication**: Stateless authentication ensures the backend doesn't need to store session data, improving performance and security.
*   **Granular RBAC**: We didn't just check if a user is "Admin." We implemented a Scope + Permission system (e.g., `leave:can_read`, `attendance:can_write`).
*   **Password Hashing**: We used Bcrypt for hashing passwords, ensuring that even if the database is leaked, user passwords remain secure.
*   **Secret Management**: Sensitive keys are kept in a `.env` file and excluded from Git via `.gitignore`.

### **6. Performance Scoring (The "Bridge")**
This is the heart of the integration. We calculate a composite score for employees by weighting data from both modules:
*   **Conversion Rate (40%)**: CRM data (Leads → Customers).
*   **Interaction Volume (20%)**: CRM data (How active is the agent?).
*   **Attendance Score (10%)**: HRMS data (Is the employee consistent?).
*   **Deal Value (30%)**: CRM data (The actual revenue impact).

**Why this method?**: A pure sales target ignores reliability, and a pure attendance target ignores revenue. Our weighted formula provides a 360-degree view of employee value.

### **7. Key Decisions & Trade-offs**
*   **Async Processing (Threads vs. Celery)**: I chose Python's `threading` library for background tasks (like notifications) instead of a full Celery/Redis stack. 
    *   *Trade-off*: While Celery is more robust for huge scales, threading keeps the project lightweight and "plug-and-play" for the reviewer without requiring extra infrastructure.
*   **Performance Caching**: Performance scores are calculated and stored in a "materialized" `performance_records` table.
    *   *Trade-off*: This adds a small amount of extra code during updates, but it ensures that "Read" operations (dashboards) are nearly instant, which is critical for a management system.

### **8. Testing Approach**
*   **Pytest Infrastructure**: We built a complete test suite with custom fixtures.
*   **Integration Testing**: Our tests don't just check isolated functions; they verify the Integration—proving that a sales agent's clock-in and lead conversion correctly impact their performance score.
*   **Database Isolation**: We use a dedicated `hirehub_pytest_db` for testing to ensure your development data remains untouched.

---

### **Quick Setup**

#### **Option A: Docker (Recommended)**
```bash
docker-compose up --build
```

#### **Option B: Manual**
1. `pip install -r requirements.txt`
2. `python3 seed.py` (Creates DB and seeds permissions)
3. `flask run`

---

### **API Documentation**
*   **Postman**: Import `HireHub_API_Collection.json` for all pre-configured endpoints and example bodies.
