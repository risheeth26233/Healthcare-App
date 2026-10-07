"""
Authentication and database compatibility tests for the Patient ID + Secret Code flow.

Covers:
- Signup/login UI and routes (Full Name -> Patient ID + Secret Code, no email/password)
- Removal of email OTP / password reset / SMTP authentication logic
- PostgreSQL (Render) cursor compatibility - RealDictCursor rows are dicts
- Friendly, raw-exception-free database error messages
- SQLite (local) and PostgreSQL (production) SQL compatibility helpers

Run with: python -m pytest test_authentication.py -v
"""
import atexit
import contextlib
import datetime
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Use an isolated SQLite database so tests never touch development or
# production data. Must be set before app/database are imported.
TEST_DB_NAME = 'test_healthcare_auth.db'
TEST_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), TEST_DB_NAME)
os.environ['DATABASE_URL'] = f'sqlite:///{TEST_DB_NAME}'


def _remove_test_db():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


_remove_test_db()
atexit.register(_remove_test_db)

import app as app_module  # noqa: E402
import database  # noqa: E402

app_module.app.config['TESTING'] = True

PATIENT_ID_RE = re.compile(r'^HC-\d{4}-\d{5}$')
SECRET_CODE_RE = re.compile(r'^[A-Z0-9]{4}(?:-[A-Z0-9]{4}){3}$')

BANNED_ROUTE_FRAGMENTS = ('reset', 'forgot', 'verify', 'verification', 'otp', 'password', 'email', 'smtp')

REMOVED_DATABASE_FUNCTIONS = (
    'generate_reset_token',
    'set_reset_token',
    'verify_reset_token',
    'clear_reset_token',
    'check_reset_rate_limit',
    'update_password',
    'verify_password',
    'get_user_by_email',
)


class FakePgCursor:
    """Mimics psycopg2 RealDictCursor: every row is a dict keyed by column name.

    An unrecognized query returns {} so that positional indexing such as
    ``fetchone()[0]`` raises KeyError(0) - the exact production bug that used to
    surface as "An error occurred: 0".
    """

    def __init__(self, fail_on=None, existing_columns=()):
        self.log = []
        self.fail_on = fail_on
        self.existing_columns = existing_columns
        self._row = None
        self._rows = []
        self.lastrowid = None
        self.rowcount = 1

    def execute(self, sql, params=None):
        self.log.append(sql)
        text = ' '.join(sql.lower().split())

        if self.fail_on and self.fail_on in text:
            raise RuntimeError('simulated database failure with raw details')

        if 'information_schema.columns' in text:
            self._rows = [{'column_name': col} for col in self.existing_columns]
            self._row = None
        elif 'select max' in text:
            self._row = {'max_seq': 0}
        elif 'insert into users' in text:
            self._row = {'id': 42}
        elif 'insert into appointments' in text:
            self._row = {'id': 7}
        else:
            self._row = None
            self._rows = []

    def fetchone(self):
        # RealDictCursor never returns tuples: a dict (empty if no row) comes back.
        if self._row is None:
            return {}
        return self._row

    def fetchall(self):
        return self._rows


class FakePgConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor

    def commit(self):
        pass

    def close(self):
        pass


@contextlib.contextmanager
def fake_pg_connection(cursor):
    conn = FakePgConnection(cursor)
    try:
        yield conn
    finally:
        conn.close()


def _patch_postgres(monkeypatch, cursor):
    """Run database.py code against a fake PostgreSQL/RealDictCursor backend."""
    monkeypatch.setattr(database, 'DB_CONFIG', dict(database.DB_CONFIG, driver='postgresql'))
    monkeypatch.setattr(database, 'get_db_connection', lambda: fake_pg_connection(cursor))


def _client():
    return app_module.app.test_client()


# ---------------------------------------------------------------------------
# Signup UI and routes
# ---------------------------------------------------------------------------

def test_signup_form_uses_only_full_name():
    """Signup must ask for Full Name only - no email, no password."""
    html = _client().get('/signup').get_data(as_text=True)

    assert 'name="full_name"' in html
    assert 'name="email"' not in html
    assert 'name="password"' not in html
    assert 'name="confirm_password"' not in html
    for label in ('Email Address', 'Confirm Password', 'Create a strong password'):
        assert label not in html


def test_login_form_uses_only_patient_id_and_secret_code():
    """Login must ask for Patient ID and Secret Code only."""
    html = _client().get('/login').get_data(as_text=True)

    assert 'name="patient_id"' in html
    assert 'name="secret_code"' in html
    assert 'name="email"' not in html
    assert 'name="password"' not in html


def test_signup_requires_full_name():
    client = _client()
    response = client.post('/signup', data={'full_name': ''})

    assert response.status_code == 200
    assert 'Full name is required.' in response.get_data(as_text=True)


def test_signup_ignores_legacy_email_and_password_fields():
    """Old clients that still post email/password must not break signup."""
    client = _client()
    response = client.post('/signup', data={
        'full_name': 'Legacy Client',
        'email': 'legacy@example.com',
        'password': 'Password1',
        'confirm_password': 'Password1',
    })

    assert response.status_code == 302
    assert 'signup-confirmation' in response.headers['Location']


def test_signup_login_roundtrip():
    client = _client()

    response = client.post('/signup', data={'full_name': 'Ada Lovelace'})
    assert response.status_code == 302
    assert 'signup-confirmation' in response.headers['Location']

    confirmation = client.get('/signup-confirmation').get_data(as_text=True)
    patient_id = re.search(r'id="patient-id">\s*([^<\s]+)', confirmation).group(1)
    secret_code = re.search(r'id="secret-code">\s*([^<\s]+)', confirmation).group(1)

    assert PATIENT_ID_RE.match(patient_id), patient_id
    assert SECRET_CODE_RE.match(secret_code), secret_code

    # Credentials are displayed only once.
    assert client.get('/signup-confirmation').status_code == 302

    # Stored securely: secret code is hashed, no real email was collected.
    user = database.get_user_by_patient_id(patient_id)
    assert user is not None
    assert user['full_name'] == 'Ada Lovelace'
    assert secret_code not in user['secret_code_hash']
    assert user['email'].endswith('@noemail.invalid')

    # Login with Patient ID + Secret Code.
    response = client.post('/login', data={
        'patient_id': patient_id,
        'secret_code': secret_code,
    })
    assert response.status_code == 302
    assert 'dashboard' in response.headers['Location']

    dashboard = client.get('/dashboard')
    assert dashboard.status_code == 200
    assert 'Ada Lovelace' in dashboard.get_data(as_text=True)

    profile = client.get('/profile')
    assert profile.status_code == 200
    profile_html = profile.get_data(as_text=True)
    assert patient_id in profile_html
    assert 'noemail.invalid' not in profile_html
    assert 'Email Address' not in profile_html
    assert 'Change Password' not in profile_html


def test_patient_ids_are_sequential():
    client = _client()

    client.post('/signup', data={'full_name': 'First Patient'})
    first = re.search(
        r'id="patient-id">\s*([^<\s]+)',
        _client_confirmation(client),
    ).group(1)

    client.post('/signup', data={'full_name': 'Second Patient'})
    second = re.search(
        r'id="patient-id">\s*([^<\s]+)',
        _client_confirmation(client),
    ).group(1)

    assert int(second.rsplit('-', 1)[1]) == int(first.rsplit('-', 1)[1]) + 1


def _client_confirmation(client):
    return client.get('/signup-confirmation').get_data(as_text=True)


def test_login_rejects_wrong_secret_code():
    client = _client()
    client.post('/signup', data={'full_name': 'Wrong Code Patient'})
    confirmation = _client_confirmation(client)
    patient_id = re.search(r'id="patient-id">\s*([^<\s]+)', confirmation).group(1)

    response = client.post('/login', data={
        'patient_id': patient_id,
        'secret_code': 'AAAA-BBBB-CCCC-DDDD',
    })

    assert response.status_code == 200
    assert 'Invalid Patient ID or Secret Code.' in response.get_data(as_text=True)


def test_login_requires_both_fields():
    response = _client().post('/login', data={'patient_id': '', 'secret_code': ''})

    assert response.status_code == 200
    assert 'Please enter both Patient ID and Secret Code.' in response.get_data(as_text=True)


# ---------------------------------------------------------------------------
# Route safety: no authenticated route may return 500 to an external browser
# ---------------------------------------------------------------------------

PROTECTED_ROUTES = (
    '/dashboard',
    '/profile',
    '/assessment',
    '/results',
    '/appointment/1',
    '/confirmation',
)


def _signed_in_client(full_name='Route Safety User'):
    client = _client()
    success, message, user_id, patient_id, secret_code = database.create_user(full_name)
    assert success, message
    response = client.post('/login', data={
        'patient_id': patient_id,
        'secret_code': secret_code,
    })
    assert response.status_code == 302
    return client, user_id, patient_id, secret_code


@pytest.mark.parametrize('path', PROTECTED_ROUTES)
def test_unauthenticated_redirects_to_login_not_500(path):
    """A brand-new browser hitting a protected route must be redirected, never 500."""
    response = _client().get(path, follow_redirects=False)

    assert response.status_code == 302, f'{path} returned {response.status_code}'
    assert response.headers['Location'].startswith('/login')
    assert '/login' in response.headers['Location']


@pytest.mark.parametrize('path', PROTECTED_ROUTES)
def test_unauthenticated_with_invalid_session_cookie_redirects_not_500(path):
    """Garbage/expired session cookies must not crash the login check."""
    response = _client().get(
        path,
        headers={'Cookie': 'session=garbage.value.here'},
        follow_redirects=False,
    )

    assert response.status_code == 302, f'{path} returned {response.status_code}'
    assert response.headers['Location'].startswith('/login')


@pytest.mark.parametrize('path', PROTECTED_ROUTES)
def test_authenticated_protected_routes_never_return_500(path):
    client, _user_id, _patient_id, _secret_code = _signed_in_client()

    response = client.get(path, follow_redirects=False)

    assert response.status_code != 500, f'{path} returned 500'
    assert response.status_code in (200, 302)


def test_dashboard_renders_for_user_with_appointments():
    """Regression: dashboard.html used `now|date(...)`, which does not exist in
    Jinja2, so /dashboard returned HTTP 500 for any user with an appointment."""
    client, user_id, _patient_id, _secret_code = _signed_in_client('Appointment Owner')

    today = datetime.date.today()
    upcoming_date = (today + datetime.timedelta(days=7)).isoformat()
    past_date = (today - datetime.timedelta(days=3)).isoformat()

    success, message, _appt_id = database.create_appointment(
        user_id, 1, upcoming_date, '10:30', 'upcoming visit'
    )
    assert success, message
    success, message, _appt_id = database.create_appointment(
        user_id, 2, past_date, '09:00', 'past visit'
    )
    assert success, message

    response = client.get('/dashboard', follow_redirects=False)
    html = response.get_data(as_text=True)

    assert response.status_code == 200, f'/dashboard returned {response.status_code}'
    assert upcoming_date in html
    assert past_date in html
    assert 'status-badge upcoming' in html
    assert 'status-badge past' in html


def test_new_browser_full_demo_flow():
    """A completely new browser must be able to browse, sign up, log in and use
    the app without ever seeing a 500."""
    client = _client()

    for path in ('/', '/signup', '/login', '/doctors', '/pregnancy'):
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 200, f'GET {path} returned {response.status_code}'

    for path in PROTECTED_ROUTES:
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 302, f'GET {path} before login returned {response.status_code}'
        assert response.headers['Location'].startswith('/login')

    response = client.post('/signup', data={'full_name': 'New Browser Demo'}, follow_redirects=False)
    assert response.status_code == 302
    assert 'signup-confirmation' in response.headers['Location']

    confirmation = client.get('/signup-confirmation').get_data(as_text=True)
    patient_id = re.search(r'id="patient-id">\s*([^<\s]+)', confirmation).group(1)
    secret_code = re.search(r'id="secret-code">\s*([^<\s]+)', confirmation).group(1)
    assert PATIENT_ID_RE.match(patient_id)
    assert SECRET_CODE_RE.match(secret_code)

    response = client.post('/login', data={
        'patient_id': patient_id,
        'secret_code': secret_code,
    }, follow_redirects=False)
    assert response.status_code == 302
    assert 'dashboard' in response.headers['Location']

    for path in ('/dashboard', '/profile', '/assessment', '/doctors',
                 '/appointment/1', '/'):
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 200, f'GET {path} after login returned {response.status_code}'


# ---------------------------------------------------------------------------
# Email / OTP / password reset / SMTP removal
# ---------------------------------------------------------------------------

def test_no_email_otp_or_reset_routes():
    paths = {str(rule) for rule in app_module.app.url_map.iter_rules()}
    endpoints = {rule.endpoint for rule in app_module.app.url_map.iter_rules()}

    for path in paths:
        for fragment in BANNED_ROUTE_FRAGMENTS:
            assert fragment not in path.lower(), f'Unexpected route: {path}'
    for endpoint in endpoints:
        for fragment in BANNED_ROUTE_FRAGMENTS:
            assert fragment not in endpoint.lower(), f'Unexpected endpoint: {endpoint}'


def test_email_and_reset_functions_removed_from_database_module():
    for name in REMOVED_DATABASE_FUNCTIONS:
        assert not hasattr(database, name), f'{name} must be removed'


def test_no_smtp_or_email_auth_code():
    for filename in ('app.py', 'database.py'):
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)) as handle:
            source = handle.read().lower()
        for token in ('smtp', 'flask_mail', 'flask-mail', 'gmail', 'send_mail', 'sendgrid', 'otp'):
            assert token not in source, f'{token} found in {filename}'


def test_no_reset_or_verification_columns_created():
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('PRAGMA table_info(users)')
        columns = [row[1] for row in cursor.fetchall()]

    for column in ('reset_token', 'reset_token_expiry', 'reset_attempts',
                   'last_reset_request', 'is_verified', 'email_verification_code',
                   'email_verification_expiry'):
        assert column not in columns, f'{column} must not be created'

    assert 'patient_id' in columns
    assert 'secret_code_hash' in columns


# ---------------------------------------------------------------------------
# PostgreSQL (Render) cursor compatibility - regression tests for
# "An error occurred: 0" (KeyError: 0 from fetchone()[0] on a RealDictRow)
# ---------------------------------------------------------------------------

def test_create_user_with_real_dict_cursor(monkeypatch):
    cursor = FakePgCursor()
    _patch_postgres(monkeypatch, cursor)

    success, message, user_id, patient_id, secret_code = database.create_user('Postgres Patient')

    assert success is True, message
    assert user_id == 42
    assert PATIENT_ID_RE.match(patient_id)
    assert SECRET_CODE_RE.match(secret_code)
    assert 'An error occurred' not in message
    assert not message.endswith(': 0')

    inserts = [sql for sql in cursor.log if 'insert into users' in sql.lower()]
    assert inserts, 'No INSERT was executed'
    for sql in inserts:
        assert 'returning id' in sql.lower(), 'PostgreSQL INSERT must use RETURNING id'
        assert '?' not in sql, 'PostgreSQL statements must use %s placeholders'


def test_create_appointment_with_real_dict_cursor(monkeypatch):
    cursor = FakePgCursor()
    _patch_postgres(monkeypatch, cursor)

    success, message, appointment_id = database.create_appointment(
        1, 1, '2027-01-01', '10:00', 'Routine check-up'
    )

    assert success is True, message
    assert appointment_id == 7
    assert 'An error occurred' not in message

    inserts = [sql for sql in cursor.log if 'insert into appointments' in sql.lower()]
    for sql in inserts:
        assert 'returning id' in sql.lower()
        assert '?' not in sql


def test_database_errors_are_never_returned_raw(monkeypatch):
    cursor = FakePgCursor(fail_on='insert into users')
    _patch_postgres(monkeypatch, cursor)

    success, message, user_id, patient_id, secret_code = database.create_user('Broken Patient')

    assert success is False
    assert user_id is None and patient_id is None and secret_code is None
    assert message == database.ACCOUNT_CREATE_FAILED
    assert 'simulated database failure' not in message
    assert 'An error occurred' not in message
    assert message.endswith(': 0') is False


def test_appointment_errors_are_never_returned_raw(monkeypatch):
    cursor = FakePgCursor(fail_on='insert into appointments')
    _patch_postgres(monkeypatch, cursor)

    success, message, appointment_id = database.create_appointment(
        1, 1, '2027-01-01', '10:00', 'Routine check-up'
    )

    assert success is False
    assert appointment_id is None
    assert message == database.APPOINTMENT_CREATE_FAILED
    assert 'simulated database failure' not in message


def test_signup_route_hides_unexpected_database_errors(monkeypatch):
    def boom():
        raise RuntimeError('raw database exploded: 0')

    monkeypatch.setattr(database, 'create_user', boom)

    response = _client().post('/signup', data={'full_name': 'Error Patient'})
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert database.ACCOUNT_CREATE_FAILED in html
    assert 'raw database exploded' not in html
    assert 'An error occurred' not in html


# ---------------------------------------------------------------------------
# SQLite (local) / PostgreSQL (production) compatibility checks
# ---------------------------------------------------------------------------

def test_sqlite_sql_helpers(monkeypatch):
    monkeypatch.setattr(database, 'DB_CONFIG', dict(database.DB_CONFIG, driver='sqlite'))

    assert database._get_placeholder() == '?'
    assert database._get_autoincrement() == 'AUTOINCREMENT'
    assert database._get_timestamp_default() == 'DEFAULT CURRENT_TIMESTAMP'


def test_postgres_sql_helpers(monkeypatch):
    monkeypatch.setattr(database, 'DB_CONFIG', dict(database.DB_CONFIG, driver='postgresql'))

    assert database._get_placeholder() == '%s'
    assert database._get_autoincrement() == 'GENERATED BY DEFAULT AS IDENTITY'
    assert database._get_timestamp_default() == 'DEFAULT NOW()'


def test_postgres_schema_initialization_sql(monkeypatch):
    existing = ('id', 'full_name', 'email', 'password_hash', 'created_at',
                'patient_id', 'secret_code_hash')
    cursor = FakePgCursor(existing_columns=existing)
    _patch_postgres(monkeypatch, cursor)

    database.init_db()

    create_statements = [sql for sql in cursor.log if 'create table' in sql.lower()]
    assert len(create_statements) == 2

    for sql in create_statements:
        assert 'autoincrement' not in sql.lower()
    users_sql = next(sql for sql in create_statements if 'users' in sql.lower())
    assert 'GENERATED BY DEFAULT AS IDENTITY' in users_sql
    assert 'DEFAULT NOW()' in users_sql
    # All columns already exist: no destructive statements should run.
    assert not [sql for sql in cursor.log if sql.lower().strip().startswith('alter table')]


def test_sqlite_schema_is_initialized_locally():
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

    assert {'users', 'appointments'}.issubset(tables)


def test_profile_template_handles_sqlite_and_postgres_timestamps():
    """SQLite returns TIMESTAMP columns as strings, PostgreSQL as datetime objects."""
    from datetime import datetime
    from flask import render_template

    base_user = {'id': 1, 'full_name': 'Timestamp Patient', 'patient_id': 'HC-2026-00001'}

    with app_module.app.test_request_context():
        html = render_template('profile.html', user=dict(base_user, created_at=datetime(2026, 1, 2, 3, 4, 5)))
    assert '2026-01-02' in html

    with app_module.app.test_request_context():
        html = render_template('profile.html', user=dict(base_user, created_at='2026-01-02 03:04:05'))
    assert '2026-01-02' in html


if __name__ == '__main__':
    import pytest
    sys.exit(pytest.main([__file__, '-v']))
