# Smart Attendance System (Face Recognition)

Flask + MySQL + OpenCV/`face_recognition` based attendance system.

## Features
- Admin login & dashboard (stats, recent attendance)
- Add students (roll no, name, email, class, password)
- Face registration via webcam (multiple samples per student)
- Face recognition to auto-mark attendance (once per day, "Late" after 9:30 AM)
- Attendance reports with date-range filtering
- Export attendance to Excel (.xlsx)
- Student login & personal attendance dashboard with attendance %

## Project Structure
```
smart_attendance/
├── app.py                 # Flask routes
├── config.py               # App + MySQL + camera config
├── db.py                    # MySQL connection pool + query helper
├── schema.sql               # Database schema
├── seed_admin.py            # Creates default admin (admin/admin123)
├── requirements.txt
├── utils/
│   ├── face_utils.py       # Face registration + recognition logic
│   └── excel_utils.py      # Excel export logic
├── templates/               # Jinja2 HTML templates
├── static/style.css
├── encodings/                # Stores encodings.pickle (auto-created)
└── exports/                  # Generated Excel reports (auto-created)
```

## Setup

### 1. Install system dependencies
`dlib` (a dependency of `face_recognition`) needs CMake and a C++ compiler.

**Windows:** install [CMake](https://cmake.org/download/) and Visual Studio Build Tools first.
**macOS:** `brew install cmake`
**Linux:** `sudo apt install cmake build-essential`

### 2. Create a virtual environment & install Python packages
```bash
python -m venv venv
source venv/bin/activate      # venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 3. Set up MySQL
```bash
mysql -u root -p < schema.sql
```
Edit `config.py` (or set environment variables) with your MySQL credentials:
```python
MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "your_mysql_password"
MYSQL_DB = "smart_attendance"
```

### 4. Create the default admin account
```bash
python seed_admin.py
```
Default login: `admin` / `admin123` — change this after first login by updating
the `password_hash` in the `admins` table (or add an "edit password" feature).

### 5. Run the app
```bash
python app.py
```
Visit `http://localhost:5000`

## Usage Flow
1. Log in as admin → **Add Student** → fill in details → you're redirected to
   **Register Face**, which opens a webcam window. Press `c` to capture a
   sample (do this ~5 times from slightly different angles), `q` to finish.
2. On any class day, admin clicks **Start Recognition** on the dashboard —
   this opens a live webcam feed that recognizes registered faces and marks
   attendance automatically. Press `q` to stop the session.
3. Admin can view **Reports** (filter by date range) and **Export to Excel**.
4. Students log in with their email/password to see their own attendance
   history and attendance percentage.

## Important Notes / Limitations
- **Camera access**: `cv2.VideoCapture` opens a window on the *server's*
  physical machine. This works well for a local/college-lab demo where the
  server runs on the same PC as the webcam. It will **not** work if you
  deploy this to a remote cloud server — for that you'd need to capture
  frames in the browser (`getUserMedia`) and POST them to the backend
  instead. Happy to help build that version if you need it for deployment.
- **Accuracy**: recognition quality depends heavily on lighting and having
  multiple face samples per student. `Config.FACE_TOLERANCE` (default 0.5)
  controls strictness — lower it if you're getting false positives, raise
  it if real matches are being missed.
- **One scan per day**: attendance is capped at one row per student per day
  (enforced by a DB unique constraint) — running recognition again the same
  day won't create duplicates.
- **Security**: this is built for a college project/demo, not production
  hardening. Before treating it as production-grade you'd want CSRF
  protection, rate limiting on login, HTTPS, and stronger session config.

