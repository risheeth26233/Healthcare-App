"""
Database module for the Healthcare Flask application.
Handles SQLite database operations for users and appointments.
"""
import sqlite3
import os
import secrets
from datetime import datetime, timedelta, timezone
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reset_token TEXT,
                reset_token_expiry TIMESTAMP,
                reset_attempts INTEGER DEFAULT 0,
                last_reset_request TIMESTAMP,
                is_verified INTEGER DEFAULT 0,
                email_verification_code TEXT,
                email_verification_expiry TIMESTAMP,
                patient_id TEXT UNIQUE,
                secret_code_hash TEXT
            )
        ''')
        
        # Add password reset columns if they don't exist (migration for existing databases)
        _add_reset_columns_if_missing(cursor)
        
        # Add email verification columns if they don't exist (migration for existing databases)
        _add_email_verification_columns_if_missing(cursor)
        
        # Add patient ID and secret code hash columns if they don't exist (migration for existing databases)
        _add_patient_auth_columns_if_missing(cursor)
        
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


def _add_reset_columns_if_missing(cursor):
    """Add password reset columns to users table if they don't exist."""
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'reset_token' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN reset_token TEXT')
    if 'reset_token_expiry' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN reset_token_expiry TIMESTAMP')
    if 'reset_attempts' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN reset_attempts INTEGER DEFAULT 0')
    if 'last_reset_request' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN last_reset_request TIMESTAMP')


def _add_email_verification_columns_if_missing(cursor):
    """Add email verification columns to users table if they don't exist."""
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'is_verified' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 0')
    if 'email_verification_code' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN email_verification_code TEXT')
    if 'email_verification_expiry' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN email_verification_expiry TIMESTAMP')


def _add_patient_auth_columns_if_missing(cursor):
    """Add patient ID and secret code hash columns to users table if they don't exist."""
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'patient_id' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN patient_id TEXT')
        # Create unique index for patient_id (can't add UNIQUE column directly in SQLite ALTER)
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_users_patient_id ON users(patient_id)')
    if 'secret_code_hash' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN secret_code_hash TEXT')

def generate_patient_id():
    """Generate a unique patient ID in format HC-YYYY-NNNNN."""
    from datetime import datetime
    year = datetime.now().year
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Get max sequence number for this year to generate next sequential number
        # Format: HC-YYYY-NNNNN, sequence starts at position 9 (1-indexed)
        cursor.execute('''
            SELECT MAX(CAST(SUBSTR(patient_id, 9) AS INTEGER)) as max_seq 
            FROM users 
            WHERE patient_id LIKE ?
        ''', (f'HC-{year}-%',))
        row = cursor.fetchone()
        max_seq = row['max_seq'] if row['max_seq'] is not None else 0
        # Next sequence number
        sequence = max_seq + 1
        return f'HC-{year}-{sequence:05d}'


def generate_secret_code():
    """Generate a strong random secret code for patient authentication."""
    # Use secrets module for cryptographically secure random generation
    # Format: 4 groups of 4 alphanumeric characters = 16 chars total
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    groups = []
    for _ in range(4):
        group = ''.join(secrets.choice(alphabet) for _ in range(4))
        groups.append(group)
    return '-'.join(groups)


def create_user(full_name, email, password, patient_id=None, secret_code_hash=None):
    """
    Create a new user with hashed password and optional patient authentication.
    
    If patient_id and secret_code_hash are not provided, they will be generated.
    
    Returns:
        tuple: (success, message, user_id or None, patient_id, secret_code)
    """
    password_hash = generate_password_hash(password)
    
    # Generate patient authentication if not provided
    if patient_id is None:
        patient_id = generate_patient_id()
    if secret_code_hash is None:
        secret_code = generate_secret_code()
        secret_code_hash = generate_password_hash(secret_code)
    else:
        secret_code = None  # We don't have the plaintext if hash was provided
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO users (full_name, email, password_hash, patient_id, secret_code_hash) VALUES (?, ?, ?, ?, ?)',
                (full_name, email, password_hash, patient_id, secret_code_hash)
            )
            conn.commit()
            user_id = cursor.lastrowid
            return True, 'Account created successfully', user_id, patient_id, secret_code
        except sqlite3.IntegrityError as e:
            if 'patient_id' in str(e):
                # Retry with new patient ID (very unlikely collision)
                return create_user(full_name, email, password, None, secret_code_hash)
            return False, 'An account with this email already exists', None, None, None
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


# Password Reset Functions

def generate_reset_token():
    """Generate a secure 6-digit verification code."""
    return ''.join(secrets.choice('0123456789') for _ in range(6))


def set_reset_token(email):
    """
    Generate and store a reset token for the given email.
    
    Returns:
        tuple: (success, token or error_message)
    """
    token = generate_reset_token()
    expiry = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=10)
    reset_request_time = datetime.now(timezone.utc).replace(tzinfo=None)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET reset_token = ?, reset_token_expiry = ?, reset_attempts = 0, last_reset_request = ?
            WHERE email = ?
        ''', (token, expiry, reset_request_time, email))
        conn.commit()
        
        if cursor.rowcount > 0:
            return True, token
        return False, 'User not found'


def verify_reset_token(email, token):
    """
    Verify the reset token for the given email.
    
    Returns:
        tuple: (success, message, user_data or None)
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, full_name, email, reset_token, reset_token_expiry, reset_attempts
            FROM users WHERE email = ?
        ''', (email,))
        user = cursor.fetchone()
        
        if not user:
            return False, 'Invalid verification code', None
        
        # Check attempts limit (max 5 attempts)
        if user['reset_attempts'] >= 5:
            return False, 'Too many failed attempts. Please request a new code.', None
        
        # Check if token matches
        if user['reset_token'] != token:
            # Increment attempts
            cursor.execute('UPDATE users SET reset_attempts = reset_attempts + 1 WHERE email = ?', (email,))
            conn.commit()
            return False, 'Invalid verification code', None
        
        # Check expiry
        if user['reset_token_expiry']:
            expiry = datetime.fromisoformat(user['reset_token_expiry'])
            # Compare in UTC
            now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
            if now_utc > expiry:
                return False, 'Verification code has expired. Please request a new code.', None
        
        return True, 'Token verified', user


def clear_reset_token(email):
    """Clear the reset token after successful password reset."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET reset_token = NULL, reset_token_expiry = NULL, reset_attempts = 0
            WHERE email = ?
        ''', (email,))
        conn.commit()


def get_user_by_patient_id(patient_id):
    """Get user by patient ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE patient_id = ?', (patient_id,))
        return cursor.fetchone()


def verify_secret_code(patient_id, secret_code):
    """
    Verify a patient's secret code against its stored hash.
    
    Returns:
        tuple: (success, user_data or None)
    """
    user = get_user_by_patient_id(patient_id)
    if not user or not user['secret_code_hash']:
        return False, None
    
    if check_password_hash(user['secret_code_hash'], secret_code):
        return True, user
    return False, None


def update_password(email, new_password):
    """
    Update user's password and clear reset token.
    
    Returns:
        tuple: (success, message)
    """
    password_hash = generate_password_hash(new_password)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET password_hash = ?, reset_token = NULL, reset_token_expiry = NULL, reset_attempts = 0
            WHERE email = ?
        ''', (password_hash, email))
        conn.commit()
        
        if cursor.rowcount > 0:
            return True, 'Password updated successfully'
        return False, 'User not found'


def check_reset_rate_limit(email):
    """
    Check if the user has requested a reset too recently.
    
    Returns:
        tuple: (allowed, message)
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT last_reset_request FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if not user or not user['last_reset_request']:
            return True, None
        
        last_request = datetime.fromisoformat(user['last_reset_request'])
        # Compare in UTC: both timestamps are naive UTC
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        if now_utc - last_request < timedelta(minutes=1):
            return False, 'Please wait before requesting another code.'
        
        return True, None


# Initialize database on import
init_db()