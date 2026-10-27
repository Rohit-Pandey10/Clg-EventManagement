# 🎓 Python Lab Viva Voce Preparation Sheet
## College Event Management System (CEMS)

This guide contains frequently asked questions and high-scoring answers for your Python Laboratory practical exam and viva voce.

---

### Q1: What is Tkinter and how does GUI programming work in Python?
**Answer:**
- **Tkinter** (Tk interface) is Python's standard, built-in library for creating desktop Graphical User Interfaces (GUIs). It is a Python wrapper around the Tcl/Tk GUI toolkit.
- **`ttk` (Themed Tkinter)**: An extension module within Tkinter that provides modern, native-styled widgets (such as `ttk.Treeview`, `ttk.Combobox`, `ttk.Notebook`, and `ttk.Scrollbar`).
- **The Event Loop (`mainloop()`)**: Tkinter runs in an event-driven loop. Calling `root.mainloop()` starts an infinite loop that listens for user actions (mouse clicks, key presses, window resizing) and dispatches them to appropriate callback functions or event handlers.

---

### Q2: What is SQLite, and why did you choose it for this project?
**Answer:**
- **SQLite** is a lightweight, serverless, self-contained, and transactional relational database engine.
- Unlike client-server databases (like MySQL or PostgreSQL), SQLite reads and writes directly to an ordinary disk file (`college_events.db`).
- Python has native support through the built-in `sqlite3` module, meaning no external database servers or drivers need to be installed.

---

### Q3: What is CRUD, and how is it implemented in your project?
**Answer:**
**CRUD** stands for the four basic persistent storage operations:
1. **Create (Insert)**:
   - Example: Adding a new event (`INSERT INTO events (...) VALUES (...)`) or creating a new student account.
2. **Read (Select)**:
   - Example: Fetching upcoming events, viewing registered attendees, or filtering registrations using `SELECT ... JOIN ... WHERE`.
3. **Update (Modify)**:
   - Example: Editing event title, venue, or capacity (`UPDATE events SET ... WHERE event_id = ?`).
4. **Delete (Remove)**:
   - Example: Deleting an event (`DELETE FROM events WHERE event_id = ?`) after verifying that no active registrations exist.

---

### Q4: What is the difference between a Primary Key and a Foreign Key?
**Answer:**
- **Primary Key (PK)**:
  - A column (or set of columns) that uniquely identifies each record in a table. It cannot contain `NULL` values.
  - *Example in our project*: `user_id` in `users`, `event_id` in `events`, and `registration_id` in `registrations`.
- **Foreign Key (FK)**:
  - A column in one table that references the Primary Key of another table, creating an association and maintaining referential integrity.
  - *Example in our project*: `registrations.user_id` references `users.user_id`, and `registrations.event_id` references `events.event_id`.
- **Why is `PRAGMA foreign_keys = ON;` needed in SQLite?**
  - In SQLite, foreign key constraint enforcement is disabled by default for backwards compatibility. We must explicitly execute `PRAGMA foreign_keys = ON;` on every database connection.

---

### Q5: How is Database Normalization applied to this project?
**Answer:**
Database normalization organizes table columns to reduce data redundancy and improve data integrity:
- **1st Normal Form (1NF)**: Every table has a primary key, and each column contains atomic (indivisible) values (e.g., student names and departments are stored in individual scalar columns).
- **2nd Normal Form (2NF)**: The table is in 1NF, and all non-key attributes are fully functionally dependent on the primary key (no partial dependencies).
- **3rd Normal Form (3NF)**: The table is in 2NF, and there are no transitive dependencies (non-key columns do not depend on other non-key columns).
- **Many-to-Many Relationship**: Students and Events have a Many-to-Many relationship (a student registers for multiple events; an event holds multiple students). This is resolved into two One-to-Many relationships using the `registrations` associative table.

---

### Q6: How does password security and authentication work in your application?
**Answer:**
1. **Never store plain-text passwords**: Passwords are never stored in plain text or using outdated algorithms like MD5 or SHA-1 (which are vulnerable to collision attacks and rainbow tables).
2. **PBKDF2-HMAC-SHA256**:
   - We use Python’s built-in `hashlib.pbkdf2_hmac` with **100,000 iterations**.
   - **Salt**: A cryptographically secure random 16-byte hex salt is generated for each password using `secrets.token_hex(16)`.
   - The stored format is `salt$hash`.
3. **Verification**: When logging in, the stored salt is extracted, the entered password is hashed with the exact same salt and iteration count, and the hashes are compared using `secrets.compare_digest()` to prevent timing attacks.

---

### Q7: Explain the Event Registration process step-by-step.
**Answer:**
When a student clicks "Register for Event":
1. **Role Check**: Python verifies that the logged-in user is a student registering for themselves.
2. **Date Check**: Python checks if `event_date >= today`. Past events are rejected.
3. **Transaction Initiation (`with conn:`)**:
   - A database transaction starts to guarantee atomicity.
4. **Capacity Check**:
   - Queries `COUNT(*)` of active registrations (`status = 'registered'`).
   - If active count equals or exceeds `event.capacity`, the registration is aborted with a message that the event is full.
5. **Duplicate / Reactivation Handling**:
   - Checks if a registration record already exists for `(user_id, event_id)`:
     - If status is `registered`, returns duplicate error.
     - If status is `cancelled`, updates the status back to `registered` and timestamps the renewal.
     - If no prior record exists, inserts a new record with `status = 'registered'`.
6. **Commit**: The transaction automatically commits.

---

### Q8: What is SQL Injection, and how does this application prevent it?
**Answer:**
- **SQL Injection (SQLi)** occurs when untrusted user input is directly concatenated into a SQL statement, allowing an attacker to alter the query logic (e.g., `SELECT * FROM users WHERE username = '' OR '1'='1'`).
- **Prevention**: We use **parameterized queries** (prepared statements) with the `?` placeholder across the entire project (e.g., `cursor.execute("SELECT * FROM users WHERE username = ?", (clean_username,))`). The SQLite engine treats user input strictly as data, never as executable code.

---

### Q9: Why is Role-Based Access Control (RBAC) enforced in the Python service layer and not just the UI?
**Answer:**
- Hiding a button in the UI is only visual; if a client modifies the GUI state or calls a function directly, unauthorized operations could still occur.
- Enforcing permission checks in the Python service layer (e.g., `if admin_user.get("role") != "admin": return False, "Permission denied"`) ensures that business rules and database integrity are protected regardless of the UI layer.

---

### Q10: What is a SQLite Transaction and why is it important here?
**Answer:**
- A **transaction** is a sequence of database operations treated as a single unit of work satisfying ACID properties (Atomicity, Consistency, Isolation, Durability).
- In our registration service, capacity check and row insertion occur within the same transaction (`with conn:`). This ensures that two students cannot both register for the final remaining seat at the exact same fraction of a second (race condition).
