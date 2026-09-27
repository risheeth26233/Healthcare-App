# Healthcare-App

A Flask-based healthcare web application/prototype for patient health assessment, doctor appointments, and wellness tracking.

## Project Overview

HealthCare App is a web application designed to help users manage their health assessments, find doctors, book appointments, and access wellness resources. The application features user authentication with email verification, health screening calculations, and a range of healthcare-related functionality.

This is a student/prototype project intended for educational purposes and does not provide medical diagnosis or professional healthcare services.

## Key Features

- **User Authentication**: Secure signup/login with email verification
- **Health Assessment**: Interactive health questionnaire with BMI, vital signs evaluation, and health summaries
- **Doctor Directory**: Browse available doctors by specialization
- **Appointment Booking**: Book appointments with selected doctors
- **Email Verification**: Verify new accounts via 6-digit code sent to email
- **Password Reset**: Secure password reset with time-limited verification codes
- **Pregnancy & Maternity Wellness**: dedicated wellness resources
- **Dashboard & Profile**: User personal dashboard and profile management

## Technology Stack

- **Flask**: Web framework (Flask==3.0.0)
- **Flask-Mail**: Email sending functionality (Flask-Mail==0.10.0)
- **Python-Dotenv**: Environment variable loading (python-dotenv==1.0.0)
- **SQLite**: Local database for user data and appointments
- **Werkzeug**: Password hashing and security
- **Secrets**: Secure token generation for verification codes

## Project Architecture

The application follows the Flask Model-View-Controller pattern:

- **Routes** (`app.py`): URL routing and request handling
- **Templates** (`templates/`): HTML pages using Jinja2 templating
- **Database** (`database.py`): SQLite operations for users, appointments
- **Data** (`data/doctors.py`): Static doctor information
- **Health Calculations** (`health_calculations.py`: BMI, vital signs evaluation, health assessments
- **Configuration** (`.env`): Environment variables for SMTP and app settings

Application Flow:

1. Home page (`/`) → Entry point
2. Create Account (`/signup`) → User registration with email verification
3. Email Verification (`/verify-code`) → 6-digit code verification
4. Login (`/login`) → Authenticated access
5. Health Assessment (`/assessment`) → Health questionnaire
6. Results (`/results`) → Health screening results
7. Doctor Directory (`/doctors`) → Available doctors
8. Appointment Booking (`/appointment/<doctor_id>`) → Book appointment
9. Dashboard (`/dashboard`) → User personal dashboard
10. Profile (`/profile`) → User profile management
11. Pregnancy & Maternity (`/pregnancy`) → Wellness resources

## Application Flow

### Home → Create Account → Email Verification → Login → Health Assessment

1. **Home**: User lands on the home page and can navigate to create an account or log in
2. **Create Account**: User provides full name, email, and password. A 6-digit verification code is generated and sent to the email address. The user account is created in "unverified" state.
3. **Email Verification**: User receives email with 6-digit code. Code expires after 10 minutes. User enters code on verification page. Successful verification activates the account and logs the user in.
4. **Login**: Verified users can log in with their email and password.
5. **Health Assessment**: Completed authenticated users can fill out a health assessment form with personal data, vital signs, and symptoms.
6. **Results**: Assessment data is processed and displayed with BMI calculation, vital signs evaluation, and health summary. Results use screening language, not medical diagnosis.
7. **Doctor Directory**: Users can browse available doctors by specialization.
8. **Appointment Booking**: Users can book appointments with selected doctors for specific dates and times.
9. **Dashboard**: Users see their booked appointments, profile information, and quick access to features.
10. **Profile**: Users can view and manage their personal information.
11. **Pregnancy & Maternity**: Dedicated wellness page for pregnancy-related information.

## Health Assessment

The health assessment feature allows users to input their health data including:

- Personal information: age, gender, height, weight
- Vital signs: blood pressure, blood sugar, heart rate, temperature
- Symptoms: selected from a list

The system calculates:

- **BMI** (Body Mass Index) with weight classification
- **Blood Pressure** classification (Normal, Elevated, Stage 1 Hypertension, Stage 2 Hypertension)
- **Blood Glucose** classification (Normal, Prediabetes, Diabetes)
- **Heart Rate** classification (Bradycardia, Normal, Tachycardia)
- **Temperature** classification (Normal, Elevated, Fever)

**Important**: All guidance provided by the application is **screening information only**, not medical diagnosis. Users should consult healthcare professionals for medical advice.

## Authentication & Email Verification

- **Signup**: New users register with full name, email, and password. A 6-digit verification code is generated and stored in the database. The code is sent via email using Gmail SMTP with App Password. The account remains in unverified state until code is validated.
- **Verification Code**: 6-digit numeric code, expires after 10 minutes
- **Login**: Email and password authentication via werkzeug security
- **Password Reset**: Time-limited 6-digit codes sent via email (10-minute expiry)
- **Account Activation**: Successful verification sets `is_verified = 1` in database

**Required Environment Variables** (see `.env.example`):

- `MAIL_SERVER`: SMTP server (smtp.gmail.com for Gmail)
- `MAIL_PORT`: SMTP port (587 for TLS)
- `MAIL_USE_TLS`: TLS setting (True)
- `MAIL_USERNAME`: Gmail address
- `MAIL_PASSWORD`: 16-character Gmail App Password
- `MAIL_DEFAULT_SENDER`: Gmail address
- `SECRET_KEY`: Flask session secret key

**Gmail App Password Setup**: To use Gmail SMTP, enable 2-factor authentication on your Google account and generate an App Password at https://myaccount.google.com/apppasswords. Use the App Password as `MAIL_PASSWORD`, not your regular Google password.

## Doctor Directory

Users can browse available doctors with specializations including:

- Cardiology (Dr. Sarah Johnson)
- Endocrinology (Dr. Michael Chen)
- Family Medicine (Dr. Emily Rodriguez)
- Pulmonology (Dr. James Wilson)
- Dermatology (Dr. Lisa Thompson)
- Orthopedics (Dr. Robert Kim)

Each doctor has available days, description, and image reference.

## Appointment Booking

Users can book appointments with selected doctors by specifying:

- Appointment date (must be today or in the future)
- Appointment time
- Optional notes

Appointments are stored in both SQLite database and in-memory for backward compatibility.

## Pregnancy & Maternity

Dedicated wellness page providing general information and resources for pregnancy and maternity health. This is educational content, not medical advice.

## Dashboard & Profile

- **Dashboard**: Overview of user's appointments, quick access to assessment results
- **Profile**: User personal information management

## Security

- Passwords are hashed using Werkzeug's `generate_password_hash` and `check_password_hash`
- Session cookies have HTTP-only, Lax SameSite security flags
- Email verification prevents unverified account access
- Password reset tokens have 10-minute expiry
- Maximum 5 verification attempts before lockout
- Rate limiting on password reset requests (1 per minute)

## Local Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables in `.env`:
   - Copy `.env.example` to `.env`
   - Set Gmail SMTP credentials (App Password required)
   - Set `SECRET_KEY`
4. Initialize the database: The app auto-initializes on first run
5. Run the application: `python app.py`
6. Access at `http://localhost:5000`

## Environment Variables

Create a `.env` file based on `.env.example`:

```
# Flask Configuration
SECRET_KEY=your-secret-key-change-in-production

# Gmail SMTP Configuration (REQUIRED for email sending)
# Get App Password from: https://myaccount.google.com/apppasswords
# Enable 2FA on your Google account first, then generate an App Password
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-gmail-address@gmail.com
MAIL_PASSWORD=your-16-character-app-password
MAIL_DEFAULT_SENDER=your-gmail-address@gmail.com

# Database
DATABASE_URL=sqlite:///healthcare.db
```

**Never commit `.env` to version control.** It is excluded by `.gitignore`.

## Running the Application

```bash
python app.py
```

The application will be available at `http://0.0.0.0:5000` by default.

For production deployment, see the Deployment Readiness section below.

## Testing

All existing health calculation tests can be run:

```bash
python test_health_calculations.py
```

Or with pytest:

```bash
python -m pytest test_health_calculations.py -v
```

Tests cover BMI calculation, BMI categories, blood pressure classification, blood glucose classification, heart rate classification, temperature classification, overall assessment, guidance language, input validation, and appointment validation.

## Demo Walkthrough

### Home
Navigate to the application entry point. The home page introduces the HealthCare App and provides navigation to key features.

### Create Account
Users provide full name, email, and password. A 6-digit verification code is generated and sent to the provided email. The account is created in unverified state until the code is validated.

### Email Verification
User checks their email for the 6-digit code. Enter the code on the verification page. The code expires after 10 minutes. After successful verification, the account is activated and the user is logged in.

### Login
Verified users can log in with their email and password. The dashboard and other protected features become accessible.

### Health Assessment
Authenticated users complete a health questionnaire with personal data, vital signs, and symptoms. The system calculates BMI, evaluates vital signs, and generates a health summary using screening language.

### View Screening Results
Results display calculated values with categories and guidance using non-diagnostic language. Users see flag count indicating how many values are outside reference ranges.

### Find a Doctor
Browse the doctor directory by specialization to find available healthcare providers.

### Book Appointment
Select a doctor and book an appointment for a future date and time. Appointments are confirmed and stored.

### Dashboard/Profile
Access personal dashboard to view appointments, profile information, and quick navigation to key features.

### Pregnancy & Maternity

Access wellness resources for pregnancy and maternity health. Educational information only.

**Clear distinction is maintained throughout**: The application provides **health screening** and **wellness information**, not medical diagnosis or professional healthcare advice.

## Current Limitations

- Email delivery requires Gmail App Password configuration; without it, verification emails cannot be sent
- SQLite database is suitable for development and testing only; not recommended for production multi-user environments
- Static doctor list (not user-configurable)
- In-memory appointment storage (supplements database)
- No two-factor authentication beyond email verification
- No password reset via email without SMTP configuration
- Health assessments are screening tools, not medical diagnostics

## Future Enhancements

- SMTP provider flexibility (not just Gmail)
- User profile image upload
- Advanced search and filtering for doctors
- Patient history and medical records
- Integration with real healthcare APIs
- Mobile responsiveness improvements
- Additional health assessment categories
- Appointment reminder system
- Role-based access (patient vs admin)

## License

This project is for educational purposes as a student prototype.