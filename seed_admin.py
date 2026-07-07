"""
Run this once after creating the database to add a default admin login.

    python seed_admin.py

Default credentials: username=admin / password=admin123
Change the password immediately after first login (or edit below before running).
"""
from werkzeug.security import generate_password_hash
from db import query

def seed():
    existing = query("SELECT id FROM admins WHERE username = %s", ("admin",), fetchone=True)
    if existing:
        print("Admin 'admin' already exists. Skipping.")
        return

    password_hash = generate_password_hash("admin123")
    query(
        "INSERT INTO admins (username, password_hash) VALUES (%s, %s)",
        ("admin", password_hash),
        commit=True,
    )
    print("Admin created -> username: admin | password: admin123")

if __name__ == "__main__":
    seed()
