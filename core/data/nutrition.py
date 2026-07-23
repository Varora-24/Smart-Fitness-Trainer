# ================================================================
#  nutrition.py  –  Macro / nutrition calculator (pure functions)
# ================================================================
#  Independently testable — no UI, no database, no side effects.
#  Uses the Mifflin-St Jeor equation (current evidence-based default).
# ================================================================


def calculate_bmr(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
    """
    Calculate Basal Metabolic Rate using the Mifflin-St Jeor equation.

    Parameters
    ----------
    weight_kg : body weight in kilograms
    height_cm : height in centimetres
    age : age in years
    sex : 'male' or 'female'

    Returns
    -------
    BMR in kcal/day
    """
    if sex == "male":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161


ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """
    Calculate Total Daily Energy Expenditure.

    Parameters
    ----------
    bmr : Basal Metabolic Rate in kcal/day
    activity_level : one of 'sedentary', 'light', 'moderate', 'active', 'very_active'

    Returns
    -------
    TDEE in kcal/day
    """
    return bmr * ACTIVITY_MULTIPLIERS[activity_level]


GOAL_CALORIE_ADJUSTMENT = {
    "lose_fat": -500,
    "maintain": 0,
    "gain_muscle": +300,
}


def calculate_macros(tdee: float, goal: str, weight_kg: float) -> dict:
    """
    Calculate daily macro targets based on TDEE, goal, and body weight.

    Protein: 1.6–2.2 g/kg depending on goal (higher for muscle gain
    and fat loss to preserve lean mass). Fat: ~25% of total calories.
    Carbs: remainder.

    Parameters
    ----------
    tdee : Total Daily Energy Expenditure in kcal/day
    goal : one of 'lose_fat', 'maintain', 'gain_muscle'
    weight_kg : body weight in kilograms

    Returns
    -------
    dict with keys: calories, protein_g, carbs_g, fat_g
    """
    calories = tdee + GOAL_CALORIE_ADJUSTMENT[goal]

    protein_g_per_kg = 2.2 if goal == "gain_muscle" else 2.0 if goal == "lose_fat" else 1.6
    protein_g = weight_kg * protein_g_per_kg
    protein_cal = protein_g * 4

    fat_cal = calories * 0.25
    fat_g = fat_cal / 9

    carbs_cal = calories - protein_cal - fat_cal
    carbs_g = max(carbs_cal, 0) / 4

    return {
        "calories": round(calories),
        "protein_g": round(protein_g),
        "carbs_g": round(carbs_g),
        "fat_g": round(fat_g),
    }
