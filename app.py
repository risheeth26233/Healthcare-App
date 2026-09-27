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

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'healthcare-app-secret-key-change-in-production')

# Session configuration for security
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

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
        
        # Create user in database with patient ID and secret code
        success, message, user_id, patient_id, secret_code = database.create_user(full_name, email, password)
        
        if not success:
            flash(message, 'error')
            return render_template('signup.html', form_data={
                'full_name': full_name,
                'email': email
            })
        
        # Store patient credentials in session for display
        session['new_patient_id'] = patient_id
        session['new_secret_code'] = secret_code
        session['new_user_name'] = full_name
        
        flash('Account created successfully!', 'success')
        return redirect(url_for('signup_confirmation'))
    
    return render_template('signup.html', form_data={})


@app.route('/signup-confirmation')
def signup_confirmation():
    """Display patient ID and secret code after successful registration."""
    patient_id = session.get('new_patient_id')
    secret_code = session.get('new_secret_code')
    user_name = session.get('new_user_name')
    
    if not patient_id or not secret_code:
        flash('No registration data found. Please sign up first.', 'error')
        return redirect(url_for('signup'))
    
    # Clear the session data after displaying
    session.pop('new_patient_id', None)
    session.pop('new_secret_code', None)
    session.pop('new_user_name', None)
    
    return render_template('signup_confirmation.html', 
                         patient_id=patient_id, 
                         secret_code=secret_code,
                         user_name=user_name)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page with Patient ID and Secret Code."""
    if request.method == 'POST':
        patient_id = request.form.get('patient_id', '').strip().upper()
        secret_code = request.form.get('secret_code', '').strip()
        
        if not patient_id or not secret_code:
            flash('Please enter both Patient ID and Secret Code.', 'error')
            return render_template('login.html', form_data={'patient_id': patient_id})
        
        # Verify secret code against hash
        success, user = database.verify_secret_code(patient_id, secret_code)
        
        if success:
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid Patient ID or Secret Code.', 'error')
            return render_template('login.html', form_data={'patient_id': patient_id})
    
    return render_template('login.html', form_data={})


@app.route('/logout')
def logout():
    """User logout."""
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


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