# ================================================================
#  tests/test_supplement_data.py  –  Supplement data integrity tests
# ================================================================

from supplement_data import SUPPLEMENT_INFO, MANDATORY_DISCLAIMER


# All valid fitness_goal values that the db.py users table accepts
VALID_GOALS = ["gain_muscle", "lose_fat", "maintain", "endurance", "general_health"]


class TestSupplementData:
    """Verify the static supplement info table is complete and well-formed."""

    def test_every_valid_goal_has_entry(self):
        """No silent KeyError when a user picks any valid fitness_goal."""
        for goal in VALID_GOALS:
            assert goal in SUPPLEMENT_INFO, f"Missing SUPPLEMENT_INFO entry for goal: {goal}"
            assert isinstance(SUPPLEMENT_INFO[goal], list)
            assert len(SUPPLEMENT_INFO[goal]) > 0, f"Empty supplement list for goal: {goal}"

    def test_each_supplement_has_name_and_note(self):
        """Every supplement entry must have both 'name' and 'note' keys."""
        for goal, supplements in SUPPLEMENT_INFO.items():
            for i, supp in enumerate(supplements):
                assert "name" in supp, f"Missing 'name' in {goal}[{i}]"
                assert "note" in supp, f"Missing 'note' in {goal}[{i}]"
                assert len(supp["name"]) > 0
                assert len(supp["note"]) > 0

    def test_mandatory_disclaimer_exists(self):
        """The disclaimer string must be non-empty."""
        assert isinstance(MANDATORY_DISCLAIMER, str)
        assert len(MANDATORY_DISCLAIMER) > 50  # meaningful content, not a stub

    def test_disclaimer_mentions_medical_advice(self):
        """The disclaimer should clearly state it is not medical advice."""
        lower = MANDATORY_DISCLAIMER.lower()
        assert "not medical advice" in lower or "not personalised" in lower

    def test_disclaimer_mentions_doctor(self):
        """The disclaimer should recommend consulting a professional."""
        lower = MANDATORY_DISCLAIMER.lower()
        assert "doctor" in lower or "dietitian" in lower
