# ================================================================
#  tests/test_nutrition.py  –  Nutrition calculator unit tests
# ================================================================

import pytest
from nutrition import (
    calculate_bmr,
    calculate_tdee,
    calculate_macros,
    ACTIVITY_MULTIPLIERS,
    GOAL_CALORIE_ADJUSTMENT,
)


class TestBMR:
    """Verify Mifflin-St Jeor BMR formula."""

    def test_male_bmr_known_value(self):
        """
        Reference: 70kg, 175cm, 25yo male.
        10(70) + 6.25(175) - 5(25) + 5 = 700 + 1093.75 - 125 + 5 = 1673.75
        """
        bmr = calculate_bmr(weight_kg=70, height_cm=175, age=25, sex="male")
        assert bmr == pytest.approx(1673.75, rel=1e-3)

    def test_female_bmr_known_value(self):
        """
        Reference: 60kg, 165cm, 30yo female.
        10(60) + 6.25(165) - 5(30) - 161 = 600 + 1031.25 - 150 - 161 = 1320.25
        """
        bmr = calculate_bmr(weight_kg=60, height_cm=165, age=30, sex="female")
        assert bmr == pytest.approx(1320.25, rel=1e-3)

    def test_male_bmr_higher_than_female_same_stats(self):
        """For identical stats, male BMR should be higher (by +5 vs -161)."""
        male = calculate_bmr(70, 170, 30, "male")
        female = calculate_bmr(70, 170, 30, "female")
        assert male > female

    def test_bmr_increases_with_weight(self):
        light = calculate_bmr(60, 170, 30, "male")
        heavy = calculate_bmr(90, 170, 30, "male")
        assert heavy > light


class TestTDEE:
    """Verify TDEE calculation with activity multipliers."""

    def test_sedentary_is_lowest(self):
        bmr = 1700
        sedentary = calculate_tdee(bmr, "sedentary")
        active = calculate_tdee(bmr, "active")
        assert sedentary < active

    def test_tdee_correct_multiplier(self):
        bmr = 1500
        for level, mult in ACTIVITY_MULTIPLIERS.items():
            assert calculate_tdee(bmr, level) == pytest.approx(bmr * mult)

    def test_invalid_activity_raises(self):
        with pytest.raises(KeyError):
            calculate_tdee(1700, "invalid_level")


class TestMacros:
    """Verify macro calculation logic."""

    def test_macros_sum_to_target_calories(self):
        """Protein + Carbs + Fat calories should ≈ target calories."""
        tdee = 2500
        for goal in GOAL_CALORIE_ADJUSTMENT:
            macros = calculate_macros(tdee, goal, weight_kg=75)
            target = tdee + GOAL_CALORIE_ADJUSTMENT[goal]
            # protein*4 + carbs*4 + fat*9 should be close to target
            reconstructed = macros["protein_g"] * 4 + macros["carbs_g"] * 4 + macros["fat_g"] * 9
            assert reconstructed == pytest.approx(target, abs=15)  # rounding tolerance

    def test_lose_fat_reduces_calories(self):
        tdee = 2200
        lose = calculate_macros(tdee, "lose_fat", 70)
        maintain = calculate_macros(tdee, "maintain", 70)
        assert lose["calories"] < maintain["calories"]

    def test_gain_muscle_increases_calories(self):
        tdee = 2200
        gain = calculate_macros(tdee, "gain_muscle", 70)
        maintain = calculate_macros(tdee, "maintain", 70)
        assert gain["calories"] > maintain["calories"]

    def test_muscle_gain_has_highest_protein(self):
        tdee = 2200
        gain = calculate_macros(tdee, "gain_muscle", 70)
        maintain = calculate_macros(tdee, "maintain", 70)
        assert gain["protein_g"] > maintain["protein_g"]

    def test_all_values_non_negative(self):
        macros = calculate_macros(1800, "lose_fat", 50)
        assert macros["calories"] > 0
        assert macros["protein_g"] >= 0
        assert macros["carbs_g"] >= 0
        assert macros["fat_g"] >= 0

    def test_return_keys(self):
        macros = calculate_macros(2000, "maintain", 70)
        assert set(macros.keys()) == {"calories", "protein_g", "carbs_g", "fat_g"}
