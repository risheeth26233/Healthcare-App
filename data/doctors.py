"""
Static list of doctors for the appointment system.
In a future version, this could be moved to a database.
"""

DOCTORS = [
    {
        'id': 1,
        'name': 'Dr. Sarah Johnson',
        'specialization': 'Cardiology',
        'description': 'Specializes in heart conditions, hypertension, and cardiovascular health.',
        'available_days': ['Monday', 'Wednesday', 'Friday'],
        'image': 'doctor1.jpg'
    },
    {
        'id': 2,
        'name': 'Dr. Michael Chen',
        'specialization': 'Endocrinology',
        'description': 'Expert in diabetes, thyroid disorders, and hormonal imbalances.',
        'available_days': ['Tuesday', 'Thursday', 'Saturday'],
        'image': 'doctor2.jpg'
    },
    {
        'id': 3,
        'name': 'Dr. Emily Rodriguez',
        'specialization': 'Family Medicine',
        'description': 'Primary care physician for general health, preventive care, and chronic disease management.',
        'available_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
        'image': 'doctor3.jpg'
    },
    {
        'id': 4,
        'name': 'Dr. James Wilson',
        'specialization': 'Pulmonology',
        'description': 'Specializes in respiratory conditions including asthma, COPD, and sleep apnea.',
        'available_days': ['Wednesday', 'Friday', 'Saturday'],
        'image': 'doctor4.jpg'
    },
    {
        'id': 5,
        'name': 'Dr. Lisa Thompson',
        'specialization': 'Dermatology',
        'description': 'Expert in skin conditions, skin cancer screening, and cosmetic dermatology.',
        'available_days': ['Monday', 'Thursday', 'Friday'],
        'image': 'doctor5.jpg'
    },
    {
        'id': 6,
        'name': 'Dr. Robert Kim',
        'specialization': 'Orthopedics',
        'description': 'Specializes in bone, joint, and muscle conditions including sports injuries.',
        'available_days': ['Tuesday', 'Wednesday', 'Saturday'],
        'image': 'doctor6.jpg'
    }
]


def get_all_doctors():
    """Return list of all doctors."""
    return DOCTORS


def get_doctor_by_id(doctor_id):
    """Find and return a doctor by ID."""
    for doctor in DOCTORS:
        if doctor['id'] == doctor_id:
            return doctor
    return None