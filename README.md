# Healthcare-App

A Flask-based healthcare web application/prototype for patient health assessment, doctor appointments, and wellness tracking.

## Project Overview

HealthCare App is a web application designed to help users manage their health assessments, find doctors, book appointments, and access wellness resources. The application features user authentication with Patient ID + Secret Code, health screening calculations, and a range of healthcare-related functionality.

This is a student/prototype project intended for educational purposes and does not provide medical diagnosis or professional healthcare services.

## Key Features

- **User Authentication**: Secure signup/login with Patient ID + Secret Code (no email verification required)
- **Health Assessment**: Interactive health questionnaire with BMI, vital signs evaluation, and health summaries
- **Doctor Directory**: Browse available doctors by specialization
- **Appointment Booking**: Book appointments with selected doctors
- **Pregnancy & Maternity Wellness**: Dedicated wellness resources
- **Dashboard & Profile**: User personal dashboard and profile management

## Technology Stack

- **Flask**: Web framework (Flask==3.0.0)
- **Python-Dotenv**: Environment variable loading (python-dotenv==1.0.0)
- **SQLite**: Local database for user data and appointments
- **Werkzeug**: Password hashing and security
- **Secrets**: Secure token generation for Patient IDs and Secret Codes

## Project Architecture

The application follows the Flask Model-View-Controller pattern:

- **Routes** (`app.py`): URL routing and request handling
- **Templates** (`templates/`): HTML pages using Jinja2 templating
- **Database** (`database.py`): SQLite operations for users, appointments
- **Data** (`data/doctors.py`): Static doctor information
- **Health Calculations** (`health_calculations.py`): BMI, vital signs evaluation, health assessments
- **Configuration** (`.env`): Environment variables for app settings

### Application Flow

1. Home page (`/`) → Entry point
2. Create Account (`/signup`) → User registration with Patient ID + Secret Code generation
3. Signup Confirmation (`/signup-confirmation`) → Display Patient ID + Secret Code
4. Login (`/login`) → Authenticated access with Patient ID + Secret Code
5. Health Assessment (`/assessment`) → Health questionnaire
6. Results (`/results`) → Health screening results
7. Doctor Directory (`/doctors`) → Available doctors
8. Appointment Booking (`/appointment/<doctor_id>`) → Book appointment
9. Dashboard (`/dashboard`) → User personal dashboard
10. Profile (`/profile`) → User profile management
11. Pregnancy & Maternity (`/pregnancy`) → Wellness resources

## Application Flow

### Home → Create Account → Signup Confirmation → Login → Health Assessment

1. **Home**: User lands on the home page and can navigate to create an account or log in
2. **Create Account**: User provides full name, email, and password. A unique Patient ID (format: HC-YYYY-NNNNN) and Secret Code (format: XXXX-XXXX-XXXX-XXXX) are generated and stored securely. The Secret Code is shown only once on the confirmation page.
3. **Signup Confirmation**: User sees their Patient ID and Secret Code with a warning to save the Secret Code securely. The Secret Code cannot be recovered or reset.
4. **Login**: Users authenticate with their Patient ID and Secret Code. The Secret Code is verified against its bcrypt hash.
5. **Health Assessment**: Authenticated users fill out a health assessment form with personal data, vital signs, and symptoms.
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

## Authentication

- **Signup**: New users register with full name, email, and password. A unique Patient ID (format: HC-YYYY-NNNNN) and Secret Code (format: XXXX-XXXX-XXXX-XXXX) are generated. The Secret Code is shown only once on the confirmation page.
- **Secret Code**: 16-character alphanumeric code (4 groups of 4 characters), stored as bcrypt hash
- **Login**: Patient ID + Secret Code authentication; Secret Code verified against bcrypt hash
- **Secret Code Recovery**: Not available — Secret Codes cannot be recovered or reset. Users must save their Secret Code securely during signup.
- **Account Status**: Successful login creates a session with user ID and name

### Required Environment Variables (see `.env.example`):

- `SECRET_KEY`: Flask session secret key

**No SMTP/Gmail configuration required** — the application does not send authentication emails.

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
- Secret Codes are hashed using the same secure mechanism (bcrypt via Werkzeug)
- Session cookies have HTTP-only, Lax SameSite security flags
- Patient ID uniqueness enforced by database UNIQUE constraint
- Generic authentication error messages prevent enumeration attacks
- Secret Codes never logged, never exposed in URLs, never printed to terminal

## Local Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables in `.env`:
   - Copy `.env.example` to `.env`
   - Set `SECRET_KEY`
4. Initialize the database: The app auto-initializes on first run
5. Run the application: `python app.py`
6. Access at `http://localhost:5000`

## Environment Variables

Create a `.env` file based on `.env.example`:

```
# Flask Configuration
SECRET_KEY=your-secret-key-change-in-production

# Database
DATABASE_URL=sqlite:///healthcare.db
```

**Never commit `.env` to version control.** It is excluded by `.gitignore`.

## Running the Application

```bash
python app.py
```

The application will be available at `http://0.0.0.0:5000` by default.

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
Users provide full name, email, and password. A unique Patient ID and Secret Code are generated. The Secret Code is shown only once on the confirmation page.

### Signup Confirmation
User sees their Patient ID and Secret Code. The Secret Code cannot be recovered or reset. User must save it securely (password manager, physical safe, etc.).

### Login
Users enter their Patient ID and Secret Code. The Secret Code is verified against its bcrypt hash. Successful login redirects to the dashboard.

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

- No email-based password reset or account recovery (Secret Code cannot be recovered)
- SQLite database is suitable for development and testing only; not recommended for production multi-user environments
- Static doctor list (not user-configurable)
- In-memory appointment storage (supplements database)
- Health assessments are screening tools, not medical diagnostics
- No two-factor authentication

## Deployment Setup

This section describes how to deploy the Healthcare-App to a production environment using Render with PostgreSQL.

### Prerequisites

- GitHub account with access to this repository
- Render account (free tier available)
- Basic familiarity with environment variables and web deployment

### Production Architecture

- **Web Service**: Gunicorn WSGI server running the Flask application
- **Database**: PostgreSQL (managed by Render)
- **HTTPS**: Automatic SSL/TLS via Render
- **Environment Variables**: Configured in Render dashboard

### Deployment Steps

#### 1. Push to GitHub

Ensure your code is pushed to the GitHub repository:

```bash
git add .
git commit -m "Prepare for deployment"
git push origin main
```

#### 2. Create Render Account

Sign up at [render.com](https://render.com) if you haven't already.

#### 3. Create PostgreSQL Database

1. In Render dashboard, click **New** → **PostgreSQL**
2. Configure:
   - Name: `healthcare-db` (or your preferred name)
   - Database: `healthcare_app`
   - User: `healthcare_user`
   - Plan: Free (for testing) or Starter/Pro for production
3. Click **Create Database**
4. Note the **Internal Database URL** - this will be your `DATABASE_URL`

#### 4. Create Web Service

1. In Render dashboard, click **New** → **Web Service**
2. Connect your GitHub repository: `risheeth26233/Healthcare-App`
3. Configure:
   - Name: `healthcare-app`
   - Runtime: `Python`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Plan: Free (for testing) or Starter/Pro for production

#### 5. Configure Environment Variables

In the web service settings, add these environment variables:

| Key | Value | Notes |
|-----|-------|-------|
| `FLASK_ENV` | `production` | Required |
| `FLASK_DEBUG` | `false` | Required for production |
| `SECRET_KEY` | *generate a strong random value* | **Required** - generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | *paste Internal Database URL from step 3* | **Required** - automatically available if you link the database |

**Optional variables:**
| Key | Value | Notes |
|-----|-------|-------|
| `FLASK_HOST` | `0.0.0.0` | Default |
| `PORT` | (auto) | Render sets this automatically |
| `FLASK_DEBUG` | `false` | Explicitly disable debug |

#### 6. Deploy

Click **Create Web Service** and wait for deployment to complete. Render will:
1. Install dependencies from `requirements.txt`
2. Run the build command
3. Start the application with gunicorn
4. Provide a public HTTPS URL (e.g., `https://healthcare-app.onrender.com`)

### Local Development

Local development continues to work with SQLite:

```bash
# Clone and setup
git clone https://github.com/risheeth26233/Healthcare-App.git
cd Healthcare-App
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your local settings (optional)
python app.py
```

The app will be available at `http://localhost:5000` with SQLite database.

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes (prod) | - | Flask secret key for sessions |
| `FLASK_ENV` | No | `development` | `development` or `production` |
| `FLASK_DEBUG` | No | `true` | `true` or `false` |
| `FLASK_HOST` | No | `0.0.0.0` | Bind address |
| `PORT` | No | `5000` | Port number (Render sets automatically) |
| `DATABASE_URL` | Yes (prod) | `sqlite:///healthcare.db` | Database connection string |
| `DATABASE_URL` | No (dev) | `sqlite:///healthcare.db` | Local SQLite path |

### Database Migration Notes

- The application automatically initializes tables on first run
- Schema migrations for existing columns are handled in `database.py`
- For PostgreSQL, the `SERIAL` type is used instead of `AUTOINCREMENT`
- All queries use parameterized placeholders compatible with both SQLite and PostgreSQL

### Security Considerations for Production

1. **Always use a strong SECRET_KEY** - Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`
2. **Never commit `.env` or `.env.local`** - These are in `.gitignore`
3. **Use HTTPS only** - Render provides automatic HTTPS
4. **Set `FLASK_ENV=production` and `FLASK_DEBUG=false`** - Disables debug mode
5. **Use PostgreSQL in production** - SQLite is not suitable for multi-user production

### Troubleshooting

- **Build fails**: Check `requirements.txt` for correct package versions
- **Database connection fails**: Verify `DATABASE_URL` is correct and database is in same region
- **App crashes on startup**: Check Render logs for Python errors
- **Static files not loading**: Ensure `static/` folder is in repository

## Future Enhancements

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