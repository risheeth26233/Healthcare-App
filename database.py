"""
Database module for the Healthcare Flask application.
Handles SQLite database operations for users and appointments.
"""
import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager
from werkzeug.security import generate_password_hash, check_password_hash

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), 'healthcare.db')

@contextmanager
def get_db_connection():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize the database with required tables."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Appointments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                doctor_id INTEGER NOT NULL,
                appointment_date TEXT NOT NULL,
                appointment_time TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()

def create_user(full_name, email, password):
    """
    Create a new user with hashed password.
    
    Returns:
        tuple: (success, message, user_id or None)
    """
    password_hash = generate_password_hash(password)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)',
                (full_name, email, password_hash)
            )
            conn.commit()
            return True, 'Account created successfully', cursor.lastrowid
        except sqlite3.IntegrityError:
            return False, 'An account with this email already exists', None
        except Exception as e:
            return False, f'An error occurred: {str(e)}', None

def get_user_by_email(email):
    """Get user by email address."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        return cursor.fetchone()

def get_user_by_id(user_id):
    """Get user by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, full_name, email, created_at FROM users WHERE id = ?', (user_id,))
        return cursor.fetchone()

def verify_password(email, password):
    """
    Verify user password.
    
    Returns:
        tuple: (success, user_data or None)
    """
    user = get_user_by_email(email)
    if user and check_password_hash(user['password_hash'], password):
        return True, user
    return False, None

def create_appointment(user_id, doctor_id, appointment_date, appointment_time, notes):
    """
    Create a new appointment for a user.
    
    Returns:
        tuple: (success, message, appointment_id or None)
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                '''INSERT INTO appointments 
                   (user_id, doctor_id, appointment_date, appointment_time, notes)
                   VALUES (?, ?, ?, ?, ?)''',
                (user_id, doctor_id, appointment_date, appointment_time, notes)
            )
            conn.commit()
            return True, 'Appointment booked successfully', cursor.lastrowid
        except Exception as e:
            return False, f'An error occurred: {str(e)}', None

def get_user_appointments(user_id):
    """Get all appointments for a user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.*, d.name as doctor_name, d.specialization
            FROM appointments a
            LEFT JOIN (
                SELECT 1 as id, 'Dr. Sarah Johnson' as name, 'Cardiology' as specialization UNION
                SELECT 2, 'Dr. Michael Chen', 'Endocrinology' UNION
                SELECT 3, 'Dr. Emily Rodriguez', 'Family Medicine' UNION
                SELECT 4, 'Dr. James Wilson', 'Pulmonology' UNION
                SELECT 5, 'Dr. Lisa Thompson', 'Dermatology' UNION
                SELECT 6, 'Dr. Robert Kim', 'Orthopedics'
            ) d ON a.doctor_id = d.id
            WHERE a.user_id = ?
            ORDER BY a.appointment_date, a.appointment_time
        ''', (user_id,))
        return cursor.fetchall()

def get_appointment_by_id(appointment_id, user_id):
    """Get a specific appointment for a user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.*, d.name as doctor_name, d.specialization
            FROM appointments a
            LEFT JOIN (
                SELECT 1 as id, 'Dr. Sarah Johnson' as name, 'Cardiology' as specialization UNION
                SELECT 2, 'Dr. Michael Chen', 'Endocrinology' UNION
                SELECT 3, 'Dr. Emily Rodriguez', 'Family Medicine' UNION
                SELECT 4, 'Dr. James Wilson', 'Pulmonology' UNION
                SELECT 5, 'Dr. Lisa Thompson', 'Dermatology' UNION
                SELECT 6, 'Dr. Robert Kim', 'Orthopedics'
            ) d ON a.doctor_id = d.id
            WHERE a.id = ? AND a.user_id = ?
        ''', (appointment_id, user_id))
        return cursor.fetchone()

# Initialize database on import
init_db()