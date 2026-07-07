"""
Face registration and recognition helpers.

Encodings are stored in a single pickle file as:
    {
        "encodings": [128-d vector, 128-d vector, ...],
        "student_ids": [1, 1, 3, ...]   # parallel list, allows multiple
                                         # samples per student for accuracy
    }
"""
import os
import pickle
import datetime
import cv2
import face_recognition

from config import Config
from db import query


def _load_encodings():
    if not os.path.exists(Config.ENCODINGS_FILE):
        return {"encodings": [], "student_ids": []}
    with open(Config.ENCODINGS_FILE, "rb") as f:
        return pickle.load(f)


def _save_encodings(data):
    os.makedirs(os.path.dirname(Config.ENCODINGS_FILE), exist_ok=True)
    with open(Config.ENCODINGS_FILE, "wb") as f:
        pickle.dump(data, f)


def register_face_from_webcam(student_id, num_samples=5):
    """
    Opens the webcam, captures `num_samples` good face frames, and stores
    their encodings against student_id. Meant to be run on the machine
    that has a physical camera attached (e.g. an admin/registration kiosk).

    Returns (success: bool, message: str)
    """
    cam = cv2.VideoCapture(Config.CAMERA_INDEX)
    if not cam.isOpened():
        return False, "Could not access webcam."

    data = _load_encodings()
    collected = 0

    print("Look at the camera. Press 'c' to capture a sample, 'q' to quit.")
    while collected < num_samples:
        ret, frame = cam.read()
        if not ret:
            continue

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb_frame)

        # Draw boxes for live feedback
        display = frame.copy()
        for (top, right, bottom, left) in locations:
            cv2.rectangle(display, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(display, f"Samples: {collected}/{num_samples}  [c]=capture [q]=quit",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.imshow("Face Registration", display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        if key == ord('c'):
            if len(locations) != 1:
                print("Need exactly one face in frame. Try again.")
                continue
            encodings = face_recognition.face_encodings(rgb_frame, locations)
            if not encodings:
                continue
            data["encodings"].append(encodings[0])
            data["student_ids"].append(student_id)
            collected += 1
            print(f"Captured sample {collected}/{num_samples}")

    cam.release()
    cv2.destroyAllWindows()

    if collected == 0:
        return False, "No face samples captured."

    _save_encodings(data)
    query(
        "UPDATE students SET face_registered = TRUE WHERE id = %s",
        (student_id,),
        commit=True,
    )
    return True, f"Registered {collected} face sample(s) successfully."


def run_recognition_and_mark_attendance():
    """
    Opens the webcam, continuously recognizes faces, and marks attendance
    for each recognized student (once per day). Press 'q' to stop.

    Returns list of dicts: [{"student_id": .., "name": .., "status": "marked"/"already_marked"}]
    """
    data = _load_encodings()
    if not data["encodings"]:
        return {"error": "No registered faces found. Register students first."}

    known_encodings = data["encodings"]
    known_ids = data["student_ids"]

    # Preload student names for display
    students = query("SELECT id, name, roll_no FROM students", fetch=True)
    id_to_name = {s["id"]: f'{s["name"]} ({s["roll_no"]})' for s in students}

    marked_today = set()
    results = []

    cam = cv2.VideoCapture(Config.CAMERA_INDEX)
    if not cam.isOpened():
        return {"error": "Could not access webcam."}

    print("Recognizing faces... Press 'q' to stop.")
    while True:
        ret, frame = cam.read()
        if not ret:
            continue

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        locations = face_recognition.face_locations(rgb_small)
        encodings = face_recognition.face_encodings(rgb_small, locations)

        for (top, right, bottom, left), face_encoding in zip(locations, encodings):
            matches = face_recognition.compare_faces(
                known_encodings, face_encoding, tolerance=Config.FACE_TOLERANCE
            )
            distances = face_recognition.face_distance(known_encodings, face_encoding)
            name = "Unknown"
            student_id = None

            if len(distances) > 0:
                best_idx = distances.argmin()
                if matches[best_idx]:
                    student_id = known_ids[best_idx]
                    name = id_to_name.get(student_id, "Unknown")

            # Scale back up (we shrank the frame by 4x)
            top, right, bottom, left = top * 4, right * 4, bottom * 4, left * 4
            color = (0, 200, 0) if student_id else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, name, (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            if student_id and student_id not in marked_today:
                marked = mark_attendance(student_id)
                marked_today.add(student_id)
                results.append({
                    "student_id": student_id,
                    "name": name,
                    "status": "marked" if marked else "already_marked",
                })

        cv2.imshow("Attendance - Face Recognition", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()
    return {"results": results}


def mark_attendance(student_id):
    """
    Inserts an attendance row for today if one doesn't already exist.
    Returns True if a new row was inserted, False if already marked.
    """
    today = datetime.date.today()
    now_time = datetime.datetime.now().time().strftime("%H:%M:%S")

    existing = query(
        "SELECT id FROM attendance WHERE student_id = %s AND date = %s",
        (student_id, today),
        fetchone=True,
    )
    if existing:
        return False

    # Mark "Late" if after 9:30 AM -- adjust cutoff as needed
    cutoff = datetime.time(9, 30, 0)
    status = "Late" if datetime.datetime.now().time() > cutoff else "Present"

    query(
        "INSERT INTO attendance (student_id, date, time_in, status) VALUES (%s, %s, %s, %s)",
        (student_id, today, now_time, status),
        commit=True,
    )
    return True
