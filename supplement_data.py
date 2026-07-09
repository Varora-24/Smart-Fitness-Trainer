# ================================================================
#  supplement_data.py  –  Educational supplement information
# ================================================================
#  Static, editable lookup table — NOT a model, NOT free-text
#  generation, NOT personalised dosing math.
#
#  Scope boundary (non-negotiable):
#  ✅  Goal-based educational info with general "commonly studied at" framing
#  ❌  No individualised dose calculations based on user weight/age/health
#  ❌  No deficiency diagnosis or medical condition claims
#  ❌  No omission of safety/interaction caveats
# ================================================================

SUPPLEMENT_INFO: dict[str, list[dict[str, str]]] = {
    "gain_muscle": [
        {
            "name": "Whey/Plant Protein Powder",
            "note": (
                "Helps meet daily protein targets when whole-food intake "
                "alone is difficult."
            ),
        },
        {
            "name": "Creatine Monohydrate",
            "note": (
                "Among the most studied supplements for strength and lean "
                "mass gains; commonly studied at 3-5g/day."
            ),
        },
        {
            "name": "Caffeine",
            "note": (
                "Commonly used pre-workout for perceived energy and focus; "
                "individual tolerance varies widely."
            ),
        },
    ],
    "lose_fat": [
        {
            "name": "Caffeine",
            "note": (
                "Commonly used pre-workout for perceived energy and focus; "
                "sensitivity varies widely between individuals."
            ),
        },
        {
            "name": "Fiber Supplement",
            "note": (
                "Can support satiety during a calorie deficit; whole-food "
                "fiber sources are generally preferred first."
            ),
        },
        {
            "name": "Whey/Plant Protein Powder",
            "note": (
                "Supports muscle preservation during a calorie deficit by "
                "helping meet elevated protein targets."
            ),
        },
    ],
    "maintain": [
        {
            "name": "Whey/Plant Protein Powder",
            "note": (
                "A convenient way to meet daily protein targets; not a "
                "replacement for balanced whole-food meals."
            ),
        },
        {
            "name": "Vitamin D",
            "note": (
                "Commonly discussed for individuals with limited sun exposure; "
                "blood testing can confirm levels."
            ),
        },
        {
            "name": "Omega-3 (Fish/Algae Oil)",
            "note": (
                "Commonly discussed for general cardiovascular health; "
                "prioritise oily fish 2x/week first."
            ),
        },
    ],
    "endurance": [
        {
            "name": "Electrolyte Mix",
            "note": (
                "Replaces sodium, potassium, and magnesium lost through "
                "prolonged sweating during extended training."
            ),
        },
        {
            "name": "Caffeine",
            "note": (
                "Well-studied ergogenic aid for endurance performance; "
                "individual tolerance and timing matter."
            ),
        },
        {
            "name": "Beta-Alanine",
            "note": (
                "May buffer lactic acid during high-intensity sustained "
                "efforts; commonly studied at 3-6g/day split across doses."
            ),
        },
    ],
    "general_health": [
        {
            "name": "Vitamin D",
            "note": (
                "Commonly discussed for individuals with limited sun exposure."
            ),
        },
        {
            "name": "Omega-3 (Fish/Algae Oil)",
            "note": (
                "Commonly discussed for general cardiovascular health."
            ),
        },
        {
            "name": "Magnesium",
            "note": (
                "Involved in hundreds of enzymatic reactions; many people "
                "don't reach RDA through diet alone."
            ),
        },
    ],
}

MANDATORY_DISCLAIMER = (
    "This is general educational information, not medical advice. Supplement "
    "needs vary by individual health status, medications, and circumstances. "
    "Talk to a doctor or registered dietitian before starting any new supplement, "
    "especially if you are pregnant, nursing, taking medication, or managing a "
    "health condition."
)
