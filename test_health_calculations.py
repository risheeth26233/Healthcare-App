"""
Automated tests for health_calculations.py
Run with: python -m pytest test_health_calculations.py -v
Or: python test_health_calculations.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import health_calculations


def test_bmi_calculation():
    """Test BMI calculation with known values."""
    # Standard test case: 70kg, 170cm = 24.2
    assert health_calculations.calculate_bmi(170, 70) == 24.2

    # Underweight: 50kg, 170cm = 17.3
    assert health_calculations.calculate_bmi(170, 50) == 17.3

    # Overweight: 85kg, 170cm = 29.4
    assert health_calculations.calculate_bmi(170, 85) == 29.4

    # Obese: 100kg, 170cm = 34.6
    assert health_calculations.calculate_bmi(170, 100) == 34.6

    # Edge case: exactly 25.0 boundary
    assert health_calculations.calculate_bmi(170, 72.25) == 25.0

    print("[PASS] BMI calculation tests passed")


def test_bmi_categories():
    """Test BMI category classification."""
    # Underweight
    cat, desc = health_calculations.get_bmi_category(17.0)
    assert cat == "Underweight"
    assert "screening flag" in desc.lower()
    assert "reference range" in desc.lower()

    # Normal weight
    cat, desc = health_calculations.get_bmi_category(22.0)
    assert cat == "Normal weight"
    assert "reference range" in desc.lower()

    # Normal weight at upper boundary
    cat, desc = health_calculations.get_bmi_category(24.9)
    assert cat == "Normal weight"

    # Overweight
    cat, desc = health_calculations.get_bmi_category(27.0)
    assert cat == "Overweight"
    assert "screening flag" in desc.lower()

    # Overweight at upper boundary
    cat, desc = health_calculations.get_bmi_category(29.9)
    assert cat == "Overweight"

    # Obese
    cat, desc = health_calculations.get_bmi_category(30.0)
    assert cat == "Obese"
    assert "screening flag" in desc.lower()

    cat, desc = health_calculations.get_bmi_category(35.0)
    assert cat == "Obese"

    print("[PASS] BMI category tests passed")


def test_blood_pressure_classification():
    """Test blood pressure classification with explicit boundary testing."""
    # Test low BP
    vitals = health_calculations.evaluate_vital_signs(30, 85, 55, 90, 72, 98.6)
    assert vitals['blood_pressure']['status'] == "Below Reference Range"

    # Test normal BP - exactly at boundary
    vitals = health_calculations.evaluate_vital_signs(30, 119, 79, 90, 72, 98.6)
    assert vitals['blood_pressure']['status'] == "Within Reference Range"

    # Test normal BP - well within range
    vitals = health_calculations.evaluate_vital_signs(30, 110, 70, 90, 72, 98.6)
    assert vitals['blood_pressure']['status'] == "Within Reference Range"

    # Test elevated BP - systolic 120-129, diastolic <80
    vitals = health_calculations.evaluate_vital_signs(30, 120, 79, 90, 72, 98.6)
    assert vitals['blood_pressure']['status'] == "Elevated"

    vitals = health_calculations.evaluate_vital_signs(30, 125, 75, 90, 72, 98.6)
    assert vitals['blood_pressure']['status'] == "Elevated"

    vitals = health_calculations.evaluate_vital_signs(30, 129, 79, 90, 72, 98.6)
    assert vitals['blood_pressure']['status'] == "Elevated"

    # Test Stage 1 hypertension - systolic 130-139 OR diastolic 80-89
    vitals = health_calculations.evaluate_vital_signs(30, 130, 79, 90, 72, 98.6)
    assert vitals['blood_pressure']['status'] == "Stage 1 Hypertension Range"

    vitals = health_calculations.evaluate_vital_signs(30, 135, 85, 90, 72, 98.6)
    assert vitals['blood_pressure']['status'] == "Stage 1 Hypertension Range"

    vitals = health_calculations.evaluate_vital_signs(30, 120, 80, 90, 72, 98.6)
    assert vitals['blood_pressure']['status'] == "Stage 1 Hypertension Range"

    vitals = health_calculations.evaluate_vital_signs(30, 120, 85, 90, 72, 98.6)
    assert vitals['blood_pressure']['status'] == "Stage 1 Hypertension Range"

    vitals = health_calculations.evaluate_vital_signs(30, 139, 89, 90, 72, 98.6)
    assert vitals['blood_pressure']['status'] == "Stage 1 Hypertension Range"

    # Test Stage 2 hypertension - systolic >=140 OR diastolic >=90
    vitals = health_calculations.evaluate_vital_signs(30, 140, 85, 90, 72, 98.6)
    assert vitals['blood_pressure']['status'] == "Stage 2 Hypertension Range"

    vitals = health_calculations.evaluate_vital_signs(30, 150, 95, 90, 72, 98.6)
    assert vitals['blood_pressure']['status'] == "Stage 2 Hypertension Range"

    vitals = health_calculations.evaluate_vital_signs(30, 130, 90, 90, 72, 98.6)
    assert vitals['blood_pressure']['status'] == "Stage 2 Hypertension Range"

    # The OLD BUG case - 125/75 should be Elevated (systolic 120-129 AND diastolic <80)
    vitals = health_calculations.evaluate_vital_signs(30, 125, 75, 90, 72, 98.6)
    assert vitals['blood_pressure']['status'] == "Elevated", f"Got: {vitals['blood_pressure']['status']}"

    # Another old bug case: 115/85 should be Stage 1 (diastolic 80-89)
    vitals = health_calculations.evaluate_vital_signs(30, 115, 85, 90, 72, 98.6)
    assert vitals['blood_pressure']['status'] == "Stage 1 Hypertension Range"

    print("[PASS] Blood pressure classification tests passed (including boundary cases)")


def test_blood_glucose_classification():
    """Test blood glucose classification with fasting context."""
    # Low
    vitals = health_calculations.evaluate_vital_signs(30, 120, 80, 65, 72, 98.6)
    assert vitals['blood_sugar']['status'] == "Below Reference Range (Fasting)"
    assert "fasting" in vitals['blood_sugar']['message'].lower()

    # Normal
    vitals = health_calculations.evaluate_vital_signs(30, 120, 80, 90, 72, 98.6)
    assert vitals['blood_sugar']['status'] == "Within Reference Range (Fasting)"
    assert "fasting" in vitals['blood_sugar']['message'].lower()

    vitals = health_calculations.evaluate_vital_signs(30, 120, 80, 99, 72, 98.6)
    assert vitals['blood_sugar']['status'] == "Within Reference Range (Fasting)"

    # Prediabetes range
    vitals = health_calculations.evaluate_vital_signs(30, 120, 80, 100, 72, 98.6)
    assert vitals['blood_sugar']['status'] == "Prediabetes Range (Fasting)"
    assert "fasting" in vitals['blood_sugar']['message'].lower()
    assert "prediabetes range" in vitals['blood_sugar']['message'].lower()

    vitals = health_calculations.evaluate_vital_signs(30, 120, 80, 125, 72, 98.6)
    assert vitals['blood_sugar']['status'] == "Prediabetes Range (Fasting)"

    # Diabetes range
    vitals = health_calculations.evaluate_vital_signs(30, 120, 80, 126, 72, 98.6)
    assert vitals['blood_sugar']['status'] == "Diabetes Range (Fasting)"
    assert "fasting" in vitals['blood_sugar']['message'].lower()
    assert "diabetes range" in vitals['blood_sugar']['message'].lower()

    vitals = health_calculations.evaluate_vital_signs(30, 120, 80, 200, 72, 98.6)
    assert vitals['blood_sugar']['status'] == "Diabetes Range (Fasting)"

    print("[PASS] Blood glucose classification tests passed")


def test_heart_rate_classification():
    """Test heart rate classification as screening flag for adults."""
    # Low (bradycardia range)
    vitals = health_calculations.evaluate_vital_signs(30, 120, 80, 90, 50, 98.6)
    assert vitals['heart_rate']['status'] == "Below Reference Range (Resting, Adults)"
    assert "resting" in vitals['heart_rate']['message'].lower()
    assert "adults" in vitals['heart_rate']['message'].lower()
    assert "screening flag" in vitals['heart_rate']['message'].lower()

    # Normal
    vitals = health_calculations.evaluate_vital_signs(30, 120, 80, 90, 72, 98.6)
    assert vitals['heart_rate']['status'] == "Within Reference Range (Resting, Adults)"

    vitals = health_calculations.evaluate_vital_signs(30, 120, 80, 90, 100, 98.6)
    assert vitals['heart_rate']['status'] == "Within Reference Range (Resting, Adults)"

    # High (tachycardia range)
    vitals = health_calculations.evaluate_vital_signs(30, 120, 80, 90, 101, 98.6)
    assert vitals['heart_rate']['status'] == "Above Reference Range (Resting, Adults)"
    assert "screening flag" in vitals['heart_rate']['message'].lower()

    print("[PASS] Heart rate classification tests passed")


def test_temperature_classification():
    """Test temperature classification with oral measurement assumption."""
    # Low
    vitals = health_calculations.evaluate_vital_signs(30, 120, 80, 90, 72, 96.0)
    assert vitals['temperature']['status'] == "Below Reference Range (Oral)"
    assert "oral" in vitals['temperature']['message'].lower()

    # Normal
    vitals = health_calculations.evaluate_vital_signs(30, 120, 80, 90, 72, 98.6)
    assert vitals['temperature']['status'] == "Within Reference Range (Oral)"

    vitals = health_calculations.evaluate_vital_signs(30, 120, 80, 90, 72, 99.0)
    assert vitals['temperature']['status'] == "Within Reference Range (Oral)"

    # Elevated
    vitals = health_calculations.evaluate_vital_signs(30, 120, 80, 90, 72, 99.5)
    assert vitals['temperature']['status'] == "Elevated (Oral)"
    assert "oral" in vitals['temperature']['message'].lower()

    vitals = health_calculations.evaluate_vital_signs(30, 120, 80, 90, 72, 100.4)
    assert vitals['temperature']['status'] == "Elevated (Oral)"

    # Fever
    vitals = health_calculations.evaluate_vital_signs(30, 120, 80, 90, 72, 100.5)
    assert vitals['temperature']['status'] == "Fever Range (Oral)"
    assert "oral" in vitals['temperature']['message'].lower()
    assert "fever range" in vitals['temperature']['message'].lower()

    print("[PASS] Temperature classification tests passed")


def test_overall_assessment():
    """Test overall health screening summary (neutral, non-diagnostic)."""
    # All normal
    vitals = {
        'blood_pressure': {'status': 'Within Reference Range', 'message': 'Normal BP'},
        'blood_sugar': {'status': 'Within Reference Range (Fasting)', 'message': 'Normal sugar'},
        'heart_rate': {'status': 'Within Reference Range (Resting, Adults)', 'message': 'Normal HR'},
        'temperature': {'status': 'Within Reference Range (Oral)', 'message': 'Normal temp'}
    }
    bmi_cat = ("Normal weight", "desc")
    assessment = health_calculations.generate_health_assessment(22.0, bmi_cat, vitals, [])
    assert assessment['overall'] == "All Values Within Reference Ranges"
    assert "within typical reference ranges" in assessment['summary'].lower()

    # One flag
    vitals['blood_pressure']['status'] = "Elevated"
    vitals['blood_pressure']['message'] = 'Elevated BP'
    assessment = health_calculations.generate_health_assessment(22.0, bmi_cat, vitals, [])
    assert assessment['overall'] == "One or More Values Outside Reference Ranges"
    assert "screening flags" in assessment['summary'].lower()

    # Multiple flags
    vitals['blood_sugar']['status'] = "Prediabetes Range (Fasting)"
    vitals['blood_sugar']['message'] = 'High sugar'
    assessment = health_calculations.generate_health_assessment(22.0, bmi_cat, vitals, [])
    assert assessment['overall'] == "Multiple Values Outside Reference Ranges"
    assert "further evaluation" in assessment['summary'].lower()

    # Obese with normal vitals
    bmi_cat_obese = ("Obese", "desc")
    vitals = {
        'blood_pressure': {'status': 'Within Reference Range', 'message': 'Normal BP'},
        'blood_sugar': {'status': 'Within Reference Range (Fasting)', 'message': 'Normal sugar'},
        'heart_rate': {'status': 'Within Reference Range (Resting, Adults)', 'message': 'Normal HR'},
        'temperature': {'status': 'Within Reference Range (Oral)', 'message': 'Normal temp'}
    }
    assessment = health_calculations.generate_health_assessment(32.0, bmi_cat_obese, vitals, [])
    assert assessment['overall'] == "Multiple Values Outside Reference Ranges"

    print("[PASS] Overall assessment tests passed")


def test_guidance_language():
    """Test that guidance uses non-diagnostic language."""
    vitals = {
        'blood_pressure': {'status': 'Stage 1 Hypertension Range', 'message': 'This screening flag may warrant further evaluation with a healthcare professional.'},
        'blood_sugar': {'status': 'Within Reference Range (Fasting)', 'message': 'Normal'},
        'heart_rate': {'status': 'Within Reference Range (Resting, Adults)', 'message': 'Normal'},
        'temperature': {'status': 'Within Reference Range (Oral)', 'message': 'Normal'}
    }
    # Use actual BMI category function to get proper description with screening language
    bmi_cat = health_calculations.get_bmi_category(22.0)
    assessment = health_calculations.generate_health_assessment(22.0, bmi_cat, vitals, [])

    # Check that guidance doesn't use diagnostic language
    for item in assessment['guidance']:
        item_lower = item.lower()
        # Should not contain diagnostic phrases
        assert "you have" not in item_lower
        assert "diagnos" not in item_lower
        # Should contain screening/educational language
        has_screening_lang = any(phrase in item_lower for phrase in [
            "screening flag", "reference range", "warrant further evaluation",
            "consult a healthcare professional", "may warrant", "general wellness information"
        ])
        assert has_screening_lang, f"Guidance item lacks screening language: {item}"

    print("[PASS] Guidance language tests passed")


def test_input_validation():
    """Test input validation with edge cases."""
    # Valid data
    valid_data = {
        'age': '30', 'height': '170', 'weight': '70',
        'systolic_bp': '120', 'diastolic_bp': '80',
        'blood_sugar': '90', 'heart_rate': '72', 'temperature': '98.6'
    }
    is_valid, errors = health_calculations.validate_assessment_inputs(valid_data)
    assert is_valid == True
    assert errors == []

    # Invalid age
    invalid = valid_data.copy()
    invalid['age'] = '-5'
    is_valid, errors = health_calculations.validate_assessment_inputs(invalid)
    assert is_valid == False
    assert any("age" in e.lower() for e in errors)

    # Invalid height (too high)
    invalid = valid_data.copy()
    invalid['height'] = '300'
    is_valid, errors = health_calculations.validate_assessment_inputs(invalid)
    assert is_valid == False

    # Invalid weight (too high)
    invalid = valid_data.copy()
    invalid['weight'] = '400'
    is_valid, errors = health_calculations.validate_assessment_inputs(invalid)
    assert is_valid == False

    # Systolic <= diastolic
    invalid = valid_data.copy()
    invalid['systolic_bp'] = '80'
    invalid['diastolic_bp'] = '120'
    is_valid, errors = health_calculations.validate_assessment_inputs(invalid)
    assert is_valid == False
    assert any("systolic" in e.lower() for e in errors)

    print("[PASS] Input validation tests passed")


def test_appointment_validation():
    """Test appointment input validation."""
    from datetime import date, timedelta

    # Valid
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    valid = {
        'doctor_id': '1',
        'appointment_date': tomorrow,
        'appointment_time': '10:00',
        'notes': 'Test'
    }
    is_valid, errors = health_calculations.validate_appointment_inputs(valid)
    assert is_valid == True

    # Past date
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    invalid = valid.copy()
    invalid['appointment_date'] = yesterday
    is_valid, errors = health_calculations.validate_appointment_inputs(invalid)
    assert is_valid == False
    assert any("past" in e.lower() for e in errors)

    # Missing time
    invalid = valid.copy()
    invalid['appointment_time'] = ''
    is_valid, errors = health_calculations.validate_appointment_inputs(invalid)
    assert is_valid == False
    assert any("time" in e.lower() for e in errors)

    print("[PASS] Appointment validation tests passed")


def run_all_tests():
    """Run all tests and report results."""
    print("Running health calculation tests...\n")

    test_bmi_calculation()
    test_bmi_categories()
    test_blood_pressure_classification()
    test_blood_glucose_classification()
    test_heart_rate_classification()
    test_temperature_classification()
    test_overall_assessment()
    test_guidance_language()
    test_input_validation()
    test_appointment_validation()

    print("\n" + "=" * 50)
    print("ALL TESTS PASSED")
    print("=" * 50)


if __name__ == "__main__":
    run_all_tests()