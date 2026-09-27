"""
Main Flask application for the Patient Health Assessment and Doctor Appointment system.
"""
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime, timedelta
from functools import wraps
import os
from dotenv import load_dotenv
import health_calculations
from data.doctors import get_all_doctors, get_doctor_by_id
import database
from flask_mail import Mail, Message

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'healthcare-app-secret-key-change-in-production')

# Session configuration for security
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# Mail configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

mail = Mail(app)

# In-memory storage for appointments (Version 1 - no database)
# Keeping for backward compatibility during transition
appointments = []


def login_required(f):
    """Decorator to require login for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    """Home page - entry point to the application."""
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration page."""
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Server-side validation
        errors = []
        
        if not full_name:
            errors.append('Full name is required.')
        elif len(full_name) < 2:
            errors.append('Full name must be at least 2 characters.')
        
        if not email:
            errors.append('Email address is required.')
        elif '@' not in email or '.' not in email:
            errors.append('Please enter a valid email address.')
        
        if not password:
            errors.append('Password is required.')
        else:
            if len(password) < 8:
                errors.append('Password must be at least 8 characters.')
            if not any(c.isupper() for c in password):
                errors.append('Password must contain at least one uppercase letter.')
            if not any(c.islower() for c in password):
                errors.append('Password must contain at least one lowercase letter.')
            if not any(c.isdigit() for c in password):
                errors.append('Password must contain at least one number.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('signup.html', form_data={
                'full_name': full_name,
                'email': email
            })
        
        # Create user in database (unverified)
        success, message, user_id = database.create_user(full_name, email, password)
        
        if not success:
            flash(message, 'error')
            return render_template('signup.html', form_data={
                'full_name': full_name,
                'email': email
            })
        
        # Generate verification code
        verification_code = database.generate_reset_token()
        expiry = datetime.now() + timedelta(minutes=10)
        
        # Store verification code in database
        with database.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET email_verification_code = ?, email_verification_expiry = ?
                WHERE id = ?
            ''', (verification_code, expiry, user_id))
            conn.commit()
        
        # Log email details for development
        app.logger.info(f'Verification code generated for {email}')
        app.logger.info(f'Recipient email: {email}')
        app.logger.info(f'Verification code: {verification_code}')
        app.logger.info(f'Email send attempt started to {email}')
        
        # Send verification email
        send_success, send_message = send_signup_verification_email(email, verification_code)
        
        # Log SMTP result
        app.logger.info(f'Email send result to {email}: {send_success} - {send_message}')
        
        if send_success:
            flash('A verification code has been sent to your email. Please check your inbox.', 'success')
        else:
            flash(f'Verification code could not be sent: {send_message}', 'error')
        
        # Redirect to verification page
        return redirect(url_for('verify_code', email=email))
    
    return render_template('signup.html', form_data={})


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('login.html', form_data={'email': email})
        
        success, user = database.verify_password(email, password)
        
        if success:
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
            return render_template('login.html', form_data={'email': email})
    
    return render_template('login.html', form_data={})


@app.route('/logout')
def logout():
    """User logout."""
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


def send_reset_email(email, token):
    """Send password reset verification code via email."""
    # Check if SMTP is configured
    username = app.config.get('MAIL_USERNAME')
    password = app.config.get('MAIL_PASSWORD')
    sender = app.config.get('MAIL_DEFAULT_SENDER')
    
    if not username or not password or not sender:
        # SMTP not configured - return clear error, never log the token
        app.logger.error('SMTP not configured: MAIL_USERNAME, MAIL_PASSWORD, and MAIL_DEFAULT_SENDER must be set in .env')
        return False, 'Email service not configured. Please contact administrator.'
    
    try:
        msg = Message(
            'HealthCare App - Password Reset Verification Code',
            recipients=[email],
            sender=sender
        )
        msg.body = f'''Your password reset verification code is: {token}

This code will expire in 10 minutes.

If you did not request a password reset, please ignore this email.

---
HealthCare App'''
        msg.html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1f2d24; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .card {{ background: #ffffff; border-radius: 12px; padding: 32px; box-shadow: 0 4px 8px rgba(90, 138, 110, 0.08); border: 1px solid #d4e0d7; }}
        .logo {{ color: #5a8a6e; font-size: 24px; font-weight: 700; margin-bottom: 24px; }}
        .code {{ background: #eef3ef; border-radius: 8px; padding: 16px; text-align: center; font-size: 32px; font-weight: 700; color: #5a8a6e; letter-spacing: 8px; margin: 24px 0; }}
        .footer {{ margin-top: 24px; padding-top: 16px; border-top: 1px solid #d4e0d7; font-size: 14px; color: #6b8a72; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="logo">⚕ HealthCare</div>
            <h2 style="color: #1f2d24; margin-bottom: 16px;">Password Reset Request</h2>
            <p>You requested a password reset for your HealthCare account. Use the verification code below:</p>
            <div class="code">{token}</div>
            <p>This code will expire in <strong>10 minutes</strong>.</p>
            <p>If you did not request a password reset, please ignore this email.</p>
            <div class="footer">
                <p>— The HealthCare Team</p>
                <p>This is an automated message, please do not reply.</p>
            </div>
        </div>
    </div>
</body>
</html>'''
        mail.send(msg)
        return True, 'Verification code sent to your email'
    except Exception as e:
        # Log error without exposing credentials or token
        app.logger.error(f'Failed to send reset email to {email}: {type(e).__name__}')
        return False, 'Failed to send verification email. Please try later.'


def send_signup_verification_email(email, verification_code):
    """Send signup verification code via email."""
    # Check if SMTP is configured
    username = app.config.get('MAIL_USERNAME')
    password = app.config.get('MAIL_PASSWORD')
    sender = app.config.get('MAIL_DEFAULT_SENDER')
    
    if not username or not password or not sender:
        # SMTP not configured - return clear error, never log the token
        app.logger.error('SMTP not configured: MAIL_USERNAME, MAIL_PASSWORD, and MAIL_DEFAULT_SENDER must be set in .env')
        return False, 'Email service not configured. Please contact administrator.'
    
    try:
        msg = Message(
            'HealthCare App - Email Verification Code',
            recipients=[email],
            sender=sender
        )
        msg.body = f'''Your HealthCare account verification code is: {verification_code}

This code will expire in 10 minutes.

If you did not sign up for HealthCare, please ignore this email.

---
HealthCare App'''
        msg.html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1f2d24; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .card {{ background: #ffffff; border-radius: 12px; padding: 32px; box-shadow: 0 4px 8px rgba(90, 138, 110, 0.08); border: 1px solid #d4e0d7; }}
        .logo {{ color: #5a8a6e; font-size: 24px; font-weight: 700; margin-bottom: 24px; }}
        .code {{ background: #eef3ef; border-radius: 8px; padding: 16px; text-align: center; font-size: 32px; font-weight: 700; color: #5a8a6e; letter-spacing: 8px; margin: 24px 0; }}
        .footer {{ margin-top: 24px; padding-top: 16px; border-top: 1px solid #d4e0d7; font-size: 14px; color: #6b8a72; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="logo">⚕ HealthCare</div>
            <h2 style="color: #1f2d24; margin-bottom: 16px;">Email Verification</h2>
            <p>Use the verification code below to complete your account setup:</p>
            <div class="code">{verification_code}</div>
            <p>This code will expire in <strong>10 minutes</strong>.</p>
            <p>If you did not sign up for HealthCare, please ignore this email.</p>
            <div class="footer">
                <p>— The HealthCare Team</p>
                <p>This is an automated message, please do not reply.</p>
            </div>
        </div>
    </div>
</body>
</html>'''
        mail.send(msg)
        return True, 'Verification code sent to your email'
    except Exception as e:
        # Log error without exposing credentials or token
        app.logger.error(f'Failed to send signup verification email to {email}: {type(e).__name__}')
        return False, 'Failed to send verification email. Please try again later.'


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page - request verification code."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('forgot_password.html', form_data={'email': email})
        
        # Check rate limit
        allowed, message = database.check_reset_rate_limit(email)
        if not allowed:
            flash(message, 'error')
            return render_template('forgot_password.html', form_data={'email': email})
        
        # Generate and store reset token (always returns generic message for security)
        success, token = database.set_reset_token(email)
        
        if success:
            # Send email
            send_success, send_message = send_reset_email(email, token)
            if send_success:
                flash('If an account exists with this email, a verification code has been sent.', 'success')
            else:
                flash(send_message, 'error')
        else:
            # Generic message to prevent email enumeration
            flash('If an account exists with this email, a verification code has been sent.', 'success')
        
        return redirect(url_for('verify_code', email=email))
    
    return render_template('forgot_password.html', form_data={})


@app.route('/verify-code', methods=['GET', 'POST'])
def verify_code():
    """Verify the 6-digit code sent via email."""
    email = request.args.get('email', '').strip().lower()
    
    if not email:
        flash('Invalid request. Please start over.', 'error')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        
        if not token or len(token) != 6 or not token.isdigit():
            flash('Please enter a valid 6-digit code.', 'error')
            return render_template('verify_code.html', email=email)
        
        # Check if this is a signup verification code or password reset token
        with database.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, full_name, email, is_verified, reset_token, reset_token_expiry,
                       email_verification_code, email_verification_expiry
                FROM users WHERE email = ?
            ''', (email,))
            user = cursor.fetchone()
        
        if not user:
            flash('Invalid verification code', 'error')
            return render_template('verify_code.html', email=email)
        
        # Check if this is a signup verification (email_verification_code is set)
        if user['email_verification_code'] and user['email_verification_expiry']:
            # Signup verification flow
            expiry = datetime.fromisoformat(user['email_verification_expiry'])
            if datetime.now() > expiry:
                # Expired signup code - generate a new one
                new_code = database.generate_reset_token()
                new_expiry = datetime.now() + timedelta(minutes=10)
                with database.get_db_connection() as conn2:
                    cursor2 = conn2.cursor()
                    cursor2.execute('''
                        UPDATE users 
                        SET email_verification_code = ?, email_verification_expiry = ?
                        WHERE email = ?
                    ''', (new_code, new_expiry, email))
                    conn2.commit()
                flash('Verification code has expired. A new code has been sent to your email.', 'error')
                return render_template('verify_code.html', email=email)
            
            if user['email_verification_code'] != token:
                # Increment failed attempts
                with database.get_db_connection() as conn3:
                    cursor3 = conn3.cursor()
                    cursor3.execute('''
                        UPDATE users SET reset_attempts = reset_attempts + 1 WHERE email = ?
                    ''', (email,))
                    conn3.commit()
                flash('Invalid verification code', 'error')
                return render_template('verify_code.html', email=email)
            
            # Code is valid - activate the user account
            with database.get_db_connection() as conn4:
                cursor4 = conn4.cursor()
                cursor4.execute('UPDATE users SET is_verified = 1, email_verification_code = NULL, email_verification_expiry = NULL, reset_attempts = 0 WHERE email = ?', (email,))
                conn4.commit()
            
            # Log in the user
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            flash('Email verified! Your account is now activated.', 'success')
            return redirect(url_for('dashboard'))
        
        # Password reset flow (check reset_token)
        if user['reset_token']:
            # Password reset flow
            success, message, user_data = database.verify_reset_token(email, token)
            
            if success:
                # Store verified email in session for reset password step
                session['reset_email'] = email
                return redirect(url_for('reset_password'))
            else:
                flash(message, 'error')
                return render_template('verify_code.html', email=email)
        
        # Unknown state - invalid code
        flash('Invalid verification code', 'error')
        return render_template('verify_code.html', email=email)
    
    return render_template('verify_code.html', email=email)


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Reset password page - enter new password after code verification."""
    # Check if user has verified the code
    email = session.get('reset_email')
    if not email:
        flash('Please verify your code first.', 'error')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        errors = []
        
        if not password:
            errors.append('Password is required.')
        else:
            if len(password) < 8:
                errors.append('Password must be at least 8 characters.')
            if not any(c.isupper() for c in password):
                errors.append('Password must contain at least one uppercase letter.')
            if not any(c.islower() for c in password):
                errors.append('Password must contain at least one lowercase letter.')
            if not any(c.isdigit() for c in password):
                errors.append('Password must contain at least one number.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('reset_password.html', email=email)
        
        # Update password
        success, message = database.update_password(email, password)
        
        if success:
            # Clear session
            session.pop('reset_email', None)
            flash('Your password has been reset successfully. Please sign in with your new password.', 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'error')
            return render_template('reset_password.html', email=email)
    
    return render_template('reset_password.html', email=email)


@app.route('/dashboard')
@login_required
def dashboard():
    """Authenticated user dashboard."""
    user_name = session.get('user_name', 'User')
    user_id = session.get('user_id')
    
    # Get upcoming appointments
    user_appointments = database.get_user_appointments(user_id)
    upcoming = None
    if user_appointments:
        # Get the next upcoming appointment
        for appt in user_appointments:
            appt_date = datetime.strptime(appt['appointment_date'], '%Y-%m-%d').date()
            if appt_date >= datetime.now().date():
                upcoming = appt
                break
    
    return render_template('dashboard.html', 
                         user_name=user_name, 
                         upcoming=upcoming,
                         appointments=user_appointments)


@app.route('/profile')
@login_required
def profile():
    """User profile page."""
    user_id = session.get('user_id')
    user = database.get_user_by_id(user_id)
    return render_template('profile.html', user=user)


@app.route('/assessment', methods=['GET', 'POST'])
@login_required
def assessment():
    """Health assessment form page."""
    if request.method == 'POST':
        # Collect form data
        form_data = {
            'name': request.form.get('name', '').strip(),
            'age': request.form.get('age', ''),
            'gender': request.form.get('gender', ''),
            'height': request.form.get('height', ''),
            'weight': request.form.get('weight', ''),
            'systolic_bp': request.form.get('systolic_bp', ''),
            'diastolic_bp': request.form.get('diastolic_bp', ''),
            'blood_sugar': request.form.get('blood_sugar', ''),
            'heart_rate': request.form.get('heart_rate', ''),
            'temperature': request.form.get('temperature', ''),
            'symptoms': request.form.getlist('symptoms')
        }
        
        # Validate inputs
        is_valid, errors = health_calculations.validate_assessment_inputs(form_data)
        
        if not is_valid:
            for error in errors:
                flash(error, 'error')
            return render_template('assessment.html', form_data=form_data)
        
        # Store validated data in session for results page
        session['assessment_data'] = form_data
        return redirect(url_for('results'))
    
    return render_template('assessment.html', form_data={})


@app.route('/results')
@login_required
def results():
    """Display health assessment results."""
    # Get assessment data from session
    data = session.get('assessment_data')
    
    if not data:
        flash('No assessment data found. Please complete the health assessment first.', 'error')
        return redirect(url_for('assessment'))
    
    # Perform calculations
    height = float(data['height'])
    weight = float(data['weight'])
    age = int(data['age'])
    systolic = int(data['systolic_bp'])
    diastolic = int(data['diastolic_bp'])
    blood_sugar = int(data['blood_sugar'])
    heart_rate = int(data['heart_rate'])
    temperature = float(data['temperature'])
    symptoms = data.get('symptoms', [])
    
    # Calculate BMI
    bmi = health_calculations.calculate_bmi(height, weight)
    bmi_category = health_calculations.get_bmi_category(bmi)
    
    # Evaluate vital signs
    vital_signs = health_calculations.evaluate_vital_signs(
        age, systolic, diastolic, blood_sugar, heart_rate, temperature
    )
    
    # Generate overall assessment
    assessment = health_calculations.generate_health_assessment(
        bmi, bmi_category, vital_signs, symptoms
    )
    
    # Calculate screening flag count for UI
    flag_count = 0
    for vital in vital_signs.values():
        if 'Within Reference Range' not in vital['status']:
            flag_count += 1
    if bmi_category[0] != 'Normal weight':
        flag_count += 1
    if symptoms:
        flag_count += 1
    
    # Prepare results for template
    results_data = {
        'patient_name': data['name'],
        'age': age,
        'gender': data['gender'],
        'height': height,
        'weight': weight,
        'bmi': bmi,
        'bmi_category': bmi_category[0],
        'bmi_description': bmi_category[1],
        'vital_signs': vital_signs,
        'symptoms': symptoms,
        'assessment': assessment,
        'flag_count': flag_count
    }
    
    return render_template('results.html', results=results_data)


@app.route('/doctors')
def doctors():
    """Display list of available doctors."""
    doctors_list = get_all_doctors()
    return render_template('doctors.html', doctors=doctors_list)


@app.route('/appointment/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
def appointment(doctor_id):
    """Appointment booking page for a specific doctor."""
    doctor = get_doctor_by_id(doctor_id)
    
    if not doctor:
        flash('Doctor not found.', 'error')
        return redirect(url_for('doctors'))
    
    if request.method == 'POST':
        form_data = {
            'doctor_id': doctor_id,
            'appointment_date': request.form.get('appointment_date', ''),
            'appointment_time': request.form.get('appointment_time', ''),
            'notes': request.form.get('notes', '').strip()
        }
        
        # Validate appointment inputs
        is_valid, errors = health_calculations.validate_appointment_inputs(form_data)
        
        if not is_valid:
            for error in errors:
                flash(error, 'error')
            return render_template('appointment.html', doctor=doctor, form_data=form_data)
        
        # Create appointment record in database
        user_id = session.get('user_id')
        success, message, appointment_id = database.create_appointment(
            user_id, doctor_id, form_data['appointment_date'],
            form_data['appointment_time'], form_data['notes']
        )
        
        if success:
            # Also keep in-memory for backward compatibility
            appointment_record = {
                'id': appointment_id,
                'doctor': doctor,
                'date': form_data['appointment_date'],
                'time': form_data['appointment_time'],
                'notes': form_data['notes'],
                'booked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            appointments.append(appointment_record)
            session['last_appointment'] = appointment_record
            
            flash('Appointment booked successfully!', 'success')
            return redirect(url_for('confirmation'))
        else:
            flash(message, 'error')
            return render_template('appointment.html', doctor=doctor, form_data=form_data)
    
    # For GET request, show the form with today's date as minimum
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('appointment.html', doctor=doctor, today=today, form_data={})


@app.route('/confirmation')
@login_required
def confirmation():
    """Appointment confirmation page."""
    appointment_data = session.get('last_appointment')
    
    if not appointment_data:
        flash('No appointment found.', 'error')
        return redirect(url_for('doctors'))
    
    return render_template('confirmation.html', appointment=appointment_data)


@app.route('/pregnancy')
def pregnancy():
    """Pregnancy & Maternity wellness page."""
    user_name = session.get('user_name')
    return render_template('pregnancy.html', user_name=user_name)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)