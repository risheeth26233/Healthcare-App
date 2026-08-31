"""
Health calculation functions for the Patient Health Assessment application.
Contains pure Python functions for BMI calculation, vital signs evaluation,
and health assessment generation.

IMPORTANT: This application is for educational purposes only and does not provide
medical diagnosis, treatment, or professional medical advice.
"""

# Standard BMI category thresholds (WHO)
BMI_UNDERWEIGHT_THRESHOLD = 18.5
BMI_NORMAL_UPPER_THRESHOLD = 25.0
BMI_OVERWEIGHT_UPPER_THRESHOLD = 30.0

# Blood pressure classification thresholds (ACC/AHA 2017 guidelines for adults)
BP_LOW_SYSTOLIC = 90
BP_LOW_DIASTOLIC = 60
BP_NORMAL_SYSTOLIC = 120
BP_NORMAL_DIASTOLIC = 80
BP_ELEVATED_SYSTOLIC = 130
BP_STAGE2_SYSTOLIC = 140
BP_STAGE2_DIASTOLIC = 90

# Blood glucose thresholds (fasting values, ADA guidelines)
GLUCOSE_LOW_THRESHOLD = 70
GLUCOSE_NORMAL_UPPER = 100
GLUCOSE_PREDIABETES_UPPER = 126

# Heart rate thresholds (resting, adults)
HR_LOW_THRESHOLD = 60
HR_HIGH_THRESHOLD = 100

# Temperature thresholds (oral measurement, Fahrenheit)
TEMP_LOW_THRESHOLD = 97.0
TEMP_NORMAL_UPPER = 99.0
TEMP_ELEVATED_UPPER = 100.4


def calculate_bmi(height_cm, weight_kg):
    """
    Calculate BMI from height (cm) and weight (kg).

    Args:
        height_cm: Height in centimeters
        weight_kg: Weight in kilograms

    Returns:
        float: BMI value rounded to 1 decimal place
    """
    height_m = height_cm / 100
    bmi = weight_kg / (height_m * height_m)
    return round(bmi, 1)


def get_bmi_category(bmi):
    """
    Classify BMI into standard WHO categories.

    Args:
        bmi: BMI value

    Returns:
        tuple: (category_name, category_description)
    """
    if bmi < BMI_UNDERWEIGHT_THRESHOLD:
        return ("Underweight", "BMI below 18.5 - This screening flag suggests the value is below the reference range. Consider consulting a healthcare professional about healthy weight gain.")
    elif bmi < BMI_NORMAL_UPPER_THRESHOLD:
        return ("Normal weight", "BMI 18.5-24.9 - This value is within the reference range for healthy weight.")
    elif bmi < BMI_OVERWEIGHT_UPPER_THRESHOLD:
        return ("Overweight", "BMI 25-29.9 - This screening flag suggests the value is above the reference range. Lifestyle modifications including diet and exercise may warrant further evaluation with a healthcare professional.")
    else:
        return ("Obese", "BMI 30 or above - This screening flag suggests the value is significantly above the reference range. Consulting a healthcare professional for personalized guidance is recommended.")


def evaluate_vital_signs(age, systolic_bp, diastolic_bp, blood_sugar, heart_rate, temperature):
    """
    Evaluate basic vital signs and return screening assessments.

    Args:
        age: Patient age in years
        systolic_bp: Systolic blood pressure (mmHg)
        diastolic_bp: Diastolic blood pressure (mmHg)
        blood_sugar: Blood glucose level (mg/dL)
        heart_rate: Heart rate (beats per minute)
        temperature: Body temperature (Fahrenheit)

    Returns:
        dict: Dictionary with vital sign screening assessments
    """
    results = {}

    # Blood Pressure Evaluation - Using explicit ordered ranges per ACC/AHA 2017 guidelines
    # Classification is based on the higher of systolic or diastolic category
    # Order matters: check most severe first, then less severe
    if systolic_bp < BP_LOW_SYSTOLIC or diastolic_bp < BP_LOW_DIASTOLIC:
        bp_status = "Below Reference Range"
        bp_message = "This blood pressure reading is below the typical reference range for adults. This screening flag may warrant further evaluation with a healthcare professional."
    elif systolic_bp < BP_NORMAL_SYSTOLIC and diastolic_bp < BP_NORMAL_DIASTOLIC:
        bp_status = "Within Reference Range"
        bp_message = "This blood pressure reading is within the typical reference range for adults."
    elif systolic_bp < BP_ELEVATED_SYSTOLIC and diastolic_bp < BP_NORMAL_DIASTOLIC:
        bp_status = "Elevated"
        bp_message = "This systolic reading is in the elevated range while diastolic is within reference range. This screening flag may warrant monitoring and lifestyle evaluation with a healthcare professional."
    # Stage 2 hypertension: systolic >= 140 OR diastolic >= 90
    elif systolic_bp >= BP_STAGE2_SYSTOLIC or diastolic_bp >= BP_STAGE2_DIASTOLIC:
        bp_status = "Stage 2 Hypertension Range"
        bp_message = "This reading falls within the Stage 2 hypertension range per adult guidelines. This screening flag warrants further evaluation with a healthcare professional."
    # Stage 1 hypertension: systolic 130-139 OR diastolic 80-89 (but not Stage 2)
    else:
        bp_status = "Stage 1 Hypertension Range"
        bp_message = "This reading falls within the Stage 1 hypertension range per adult guidelines. This screening flag may warrant further evaluation with a healthcare professional."

    results['blood_pressure'] = {
        'value': f"{systolic_bp}/{diastolic_bp} mmHg",
        'status': bp_status,
        'message': bp_message
    }

    # Blood Sugar Evaluation - Explicitly for fasting values only
    if blood_sugar < GLUCOSE_LOW_THRESHOLD:
        bs_status = "Below Reference Range (Fasting)"
        bs_message = "This fasting blood glucose value is below the typical reference range. This screening flag may warrant further evaluation with a healthcare professional."
    elif blood_sugar < GLUCOSE_NORMAL_UPPER:
        bs_status = "Within Reference Range (Fasting)"
        bs_message = "This fasting blood glucose value is within the typical reference range."
    elif blood_sugar < GLUCOSE_PREDIABETES_UPPER:
        bs_status = "Prediabetes Range (Fasting)"
        bs_message = "This fasting blood glucose value falls within the prediabetes range per adult guidelines. This screening flag may warrant lifestyle evaluation and follow-up testing with a healthcare professional."
    else:
        bs_status = "Diabetes Range (Fasting)"
        bs_message = "This fasting blood glucose value falls within the diabetes range per adult guidelines. This screening flag warrants further evaluation with a healthcare professional."

    results['blood_sugar'] = {
        'value': f"{blood_sugar} mg/dL",
        'status': bs_status,
        'message': bs_message
    }

    # Heart Rate Evaluation - Screening flag for resting heart rate (adults)
    if heart_rate < HR_LOW_THRESHOLD:
        hr_status = "Below Reference Range (Resting, Adults)"
        hr_message = "This resting heart rate is below the typical reference range for adults. This screening flag may warrant further evaluation with a healthcare professional, especially if symptomatic."
    elif heart_rate <= HR_HIGH_THRESHOLD:
        hr_status = "Within Reference Range (Resting, Adults)"
        hr_message = "This resting heart rate is within the typical reference range for adults."
    else:
        hr_status = "Above Reference Range (Resting, Adults)"
        hr_message = "This resting heart rate is above the typical reference range for adults. This screening flag may warrant further evaluation with a healthcare professional if persistent."

    results['heart_rate'] = {
        'value': f"{heart_rate} bpm",
        'status': hr_status,
        'message': hr_message
    }

    # Temperature Evaluation - Assumes oral measurement in Fahrenheit
    if temperature < TEMP_LOW_THRESHOLD:
        temp_status = "Below Reference Range (Oral)"
        temp_message = "This oral temperature is below the typical reference range. This screening flag may warrant further evaluation with a healthcare professional if experiencing symptoms."
    elif temperature <= TEMP_NORMAL_UPPER:
        temp_status = "Within Reference Range (Oral)"
        temp_message = "This oral temperature is within the typical reference range."
    elif temperature <= TEMP_ELEVATED_UPPER:
        temp_status = "Elevated (Oral)"
        temp_message = "This oral temperature is slightly elevated. Monitor for other symptoms and consider further evaluation with a healthcare professional if persistent."
    else:
        temp_status = "Fever Range (Oral)"
        temp_message = "This oral temperature is in the fever range. This screening flag warrants rest, hydration, and further evaluation with a healthcare professional if persistent."

    results['temperature'] = {
        'value': f"{temperature} °F",
        'status': temp_status,
        'message': temp_message
    }

    return results


def generate_health_assessment(bmi, bmi_category, vital_signs, symptoms):
    """
    Generate overall health screening summary and guidance based on all inputs.

    Args:
        bmi: BMI value
        bmi_category: BMI category tuple (name, description)
        vital_signs: Dictionary of vital sign evaluations
        symptoms: List of reported symptoms

    Returns:
        dict: Overall screening summary and guidance
    """
    # Count screening flags outside reference range
    flag_count = 0
    for vital in vital_signs.values():
        if vital['status'] != 'Within Reference Range' and 'Within Reference Range' not in vital['status']:
            flag_count += 1

    # Determine overall screening summary (neutral, non-diagnostic)
    if flag_count == 0 and bmi_category[0] == "Normal weight" and not symptoms:
        overall = "All Values Within Reference Ranges"
        summary = "All vital signs and BMI are within typical reference ranges for adults, and no symptoms were reported."
    elif flag_count <= 1 and bmi_category[0] in ["Normal weight", "Overweight"] and len(symptoms) <= 1:
        overall = "One or More Values Outside Reference Ranges"
        summary = "Most values are within typical reference ranges, with one or more screening flags that may warrant monitoring or further evaluation."
    else:
        overall = "Multiple Values Outside Reference Ranges"
        summary = "Several vital signs, BMI, or reported symptoms are outside typical reference ranges. Further evaluation with a healthcare professional is recommended."

    # Generate guidance - all framed as educational information, not prescriptions
    guidance = []

    # BMI guidance
    guidance.append(bmi_category[1])

    # Vital signs guidance - only for values outside reference range
    for vital in vital_signs.values():
        if vital['status'] != 'Within Reference Range' and 'Within Reference Range' not in vital['status']:
            guidance.append(vital['message'])

    # Symptom guidance
    if symptoms:
        symptom_names = [s.replace('_', ' ').title() for s in symptoms]
        guidance.append(f"You reported {len(symptoms)} symptom(s): {', '.join(symptom_names)}. Consider discussing these with a healthcare professional.")

    # General lifestyle guidance (educational, not prescriptive)
    guidance.append("General wellness information: A balanced diet with fruits, vegetables, lean proteins, and whole grains supports overall health.")
    guidance.append("General wellness information: Regular physical activity (such as 150 minutes of moderate exercise per week) is associated with health benefits.")
    guidance.append("General wellness information: Adequate sleep (typically 7-9 hours for adults) supports overall well-being.")
    guidance.append("General wellness information: Staying hydrated and limiting alcohol and tobacco use are generally recommended.")
    guidance.append("General wellness information: Regular check-ups with a healthcare professional support preventive care.")

    return {
        'overall': overall,
        'summary': summary,
        'guidance': guidance
    }


def validate_assessment_inputs(data):
    """
    Validate health assessment form inputs.

    Args:
        data: Dictionary of form data

    Returns:
        tuple: (is_valid, error_messages)
    """
    errors = []

    # Age validation
    try:
        age = int(data.get('age', 0))
        if age <= 0 or age > 120:
            errors.append("Age must be between 1 and 120.")
    except (ValueError, TypeError):
        errors.append("Age must be a valid number.")

    # Height validation
    try:
        height = float(data.get('height', 0))
        if height <= 0 or height > 250:
            errors.append("Height must be between 1 and 250 cm.")
    except (ValueError, TypeError):
        errors.append("Height must be a valid number.")

    # Weight validation
    try:
        weight = float(data.get('weight', 0))
        if weight <= 0 or weight > 300:
            errors.append("Weight must be between 1 and 300 kg.")
    except (ValueError, TypeError):
        errors.append("Weight must be a valid number.")

    # Blood pressure validation
    try:
        systolic = int(data.get('systolic_bp', 0))
        diastolic = int(data.get('diastolic_bp', 0))
        if systolic <= 0 or systolic > 300:
            errors.append("Systolic blood pressure must be between 1 and 300 mmHg.")
        if diastolic <= 0 or diastolic > 200:
            errors.append("Diastolic blood pressure must be between 1 and 200 mmHg.")
        if systolic <= diastolic:
            errors.append("Systolic pressure must be higher than diastolic pressure.")
    except (ValueError, TypeError):
        errors.append("Blood pressure values must be valid numbers.")

    # Blood sugar validation
    try:
        blood_sugar = int(data.get('blood_sugar', 0))
        if blood_sugar <= 0 or blood_sugar > 500:
            errors.append("Blood sugar must be between 1 and 500 mg/dL.")
    except (ValueError, TypeError):
        errors.append("Blood sugar must be a valid number.")

    # Heart rate validation
    try:
        heart_rate = int(data.get('heart_rate', 0))
        if heart_rate <= 0 or heart_rate > 300:
            errors.append("Heart rate must be between 1 and 300 bpm.")
    except (ValueError, TypeError):
        errors.append("Heart rate must be a valid number.")

    # Temperature validation
    try:
        temperature = float(data.get('temperature', 0))
        if temperature < 90 or temperature > 110:
            errors.append("Temperature must be between 90 and 110 °F.")
    except (ValueError, TypeError):
        errors.append("Temperature must be a valid number.")

    return len(errors) == 0, errors


def validate_appointment_inputs(data):
    """
    Validate appointment booking form inputs.

    Args:
        data: Dictionary of form data

    Returns:
        tuple: (is_valid, error_messages)
    """
    errors = []
    from datetime import datetime

    # Doctor validation
    if not data.get('doctor_id'):
        errors.append("Please select a doctor.")

    # Date validation
    appointment_date = data.get('appointment_date', '')
    if not appointment_date:
        errors.append("Please select an appointment date.")
    else:
        try:
            appt_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            if appt_date < datetime.now().date():
                errors.append("Appointment date cannot be in the past.")
        except ValueError:
            errors.append("Invalid date format.")

    # Time validation
    if not data.get('appointment_time'):
        errors.append("Please select an appointment time.")

    return len(errors) == 0, errors