# ================================================================
#  config.py  –  AI Smart Fitness Trainer v3 Pro
# ================================================================
#  Single source of truth for ALL constants, thresholds, paths,
#  and exercise definitions.  Import freely; never hardcode values
#  in other modules.
# ================================================================


# ── Window ───────────────────────────────────────────────────────
WINDOW_TITLE  = "AI Smart Fitness Trainer v3 Pro"
FRAME_WIDTH   = 1280
FRAME_HEIGHT  = 720
CLASSIFIER_SWITCH_MARGIN = 1.3  # Winning score must exceed current by this multiplier

# ── MediaPipe ────────────────────────────────────────────────────
DETECTION_CONFIDENCE    = 0.7
TRACKING_CONFIDENCE     = 0.85
MODEL_COMPLEXITY        = 1          # 0=lite  1=full  2=heavy

# ── Landmark visibility gate ─────────────────────────────────────
# If a required landmark's visibility score is below this value
# the tracker skips the frame and shows a guidance message.
LANDMARK_VISIBILITY_THRESHOLD = 0.5

# ── Angle smoothing ──────────────────────────────────────────────
ANGLE_SMOOTH_FRAMES = 5              # moving-average window

# ── Movement velocity (anti-jerk) ────────────────────────────────
# Maximum acceptable angle change per frame (degrees).
# Changes above this reduce the control score.
MAX_VELOCITY_DEG_PER_FRAME = 15.0

# ── Form-score weights (must sum to 1.0) ─────────────────────────
FORM_WEIGHT_SYMMETRY  = 0.35
FORM_WEIGHT_ROM       = 0.30
FORM_WEIGHT_POSTURE   = 0.20
FORM_WEIGHT_CONTROL   = 0.15

# ── Rep-quality thresholds ───────────────────────────────────────
# A rep is "clean" when its quality score >= this value.
CLEAN_REP_SCORE_THRESHOLD = 60.0

# ── ML model / dataset paths ─────────────────────────────────────
DATASET_CSV_PATH  = "rep_dataset.csv"
MODEL_SKOPS_PATH  = "rep_quality_model.skops"
MAX_CONSECUTIVE_FAILURES = 30

# ── Voice coach ──────────────────────────────────────────────────
VOICE_ENABLED       = True
VOICE_COOLDOWN_SECS = 3.0

# ── Camera setup ─────────────────────────────────────────────────
SETUP_LANDMARKS = {
    "Head"      : [0],
    "Shoulders" : [11, 12],
    "Hips"      : [23, 24],
    "Knees"     : [25, 26],
    "Ankles"    : [27, 28],
}
SETUP_VISIBILITY_THRESHOLD = 0.6
SETUP_HOLD_SECONDS         = 2.0

# ── Anti-cheat / feedback strings ────────────────────────────────
SYMMETRY_WARN_TEXT       = "Uneven Movement!"
VISIBILITY_WARN_TEXT     = "Ensure full body is visible."

LANDMARK_NAMES = {
    0: "Nose", 1: "Left Eye", 2: "Right Eye", 3: "Left Ear", 4: "Right Ear",
    11: "Left Shoulder", 12: "Right Shoulder",
    13: "Left Elbow", 14: "Right Elbow",
    15: "Left Wrist", 16: "Right Wrist",
    23: "Left Hip", 24: "Right Hip",
    25: "Left Knee", 26: "Right Knee",
    27: "Left Ankle", 28: "Right Ankle",
    29: "Left Heel", 30: "Right Heel",
    31: "Left Foot", 32: "Right Foot"
}
FEEDBACK_DEPTH_THRESHOLD = 50          # % depth below which "go lower" fires

# ── UI colours (BGR for OpenCV) ──────────────────────────────────
COLOR_GREEN     = (0, 255, 0)
COLOR_RED       = (0, 0, 255)
COLOR_WHITE     = (255, 255, 255)
COLOR_BLACK     = (0, 0, 0)
COLOR_ORANGE    = (0, 165, 255)
COLOR_CYAN      = (255, 255, 0)
COLOR_YELLOW    = (0, 255, 255)
COLOR_DARK_GRAY = (40, 40, 40)
COLOR_PURPLE    = (180, 0, 180)
COLOR_BLUE      = (255, 100, 0)

# ================================================================
#  EXERCISE CONFIGURATION
# ================================================================
#
#  Key fields explained
#  --------------------
#  display_name          : shown in UI
#  key                   : keyboard shortcut (ord character)
#  landmarks_left/right  : (p1,p2,p3) for the PRIMARY angle
#  angle_range           : (min_angle, max_angle) → 0–100 % depth
#  stage_down_threshold  : primary angle below this → stage="down"
#  stage_up_threshold    : primary angle above this (from down) → rep
#  rom_min_angle         : minimum angle that must be reached (ROM check)
#  symmetry_threshold    : max left/right diff before asymmetry flag
#  posture_chain_*       : (p1,p2,p3) for secondary posture validation
#  posture_min/max_angle : acceptable range for posture chain angle
#  clean_depth           : min depth % for clean-rep classification
#  kcal_per_rep          : calorie constant
#  required_landmarks    : landmark IDs that must be visible
#  feedback_low/good     : coaching strings
#  autodetect_signals    : list of signal names used by ExerciseClassifier
#
# ================================================================

EXERCISE_CONFIG = {

    # ── Squats ──────────────────────────────────────────────────
    "squats": {
        "image_url"           : "app/static/images/squats.jpg",
        "image_source"        : "SmartTrainer AI Vector Reference",
        "description"         : "A compound, full-body exercise that trains primarily the muscles of the thighs, hips and buttocks.",
        "display_name"        : "Squats",
        "key"                 : ord('s'),

        # Primary joint: knee (hip→knee→ankle)
        "landmarks_left"      : (23, 25, 27),
        "landmarks_right"     : (24, 26, 28),
        "angle_range"         : (90, 170),   # 170° = standing, 90° = deep squat
        # State machine: angle falls below down_threshold → "down"
        #                angle rises above up_threshold from "down" → rep
        "stage_down_threshold": 120,   # angle falls below this → "down"
        # Diagnostic on squats1 showed max angle of 159.1° — just below 160.
        # Lowered to 150° to reliably catch the stand-up transition.
        "stage_up_threshold"  : 150,   # angle rises above this (from down) → rep counted
        # ROM: knee angle must reach below this during the rep
        "rom_min_angle"       : 110,

        # Posture: torso (shoulder→hip→knee) must stay upright
        # Left chain: 11,23,25  Right chain: 12,24,26
        "posture_chain_left"  : (11, 23, 25),
        "posture_chain_right" : (12, 24, 26),
        "posture_min_angle"   : 60,    # too low → leaning too far forward
        "posture_max_angle"   : 180,

        "symmetry_threshold"  : 25,
        "clean_depth"         : 70,
        "kcal_per_rep"        : 0.32,
        "depth_direction"     : "down",

        "required_landmarks"  : [11, 12, 23, 24, 25, 26, 27, 28],

        "feedback_low"        : "Go Lower!",
        "feedback_good"       : "Good Squat!",
        "feedback_posture"    : "Keep Back Straight!",

        # ── Quality Gate Overrides (Independent Layer) ──────────────
        "min_duration_secs"   : 1.2,
        "min_rom_travel_deg"  : 45.0,
        "max_posture_deviation_deg": 18.0,

        "autodetect_signals"  : ["knee_flex", "hip_upright"],
    },

    # ── Push-Ups ────────────────────────────────────────────────
    "pushups": {
        "image_url"           : "app/static/images/pushups.jpg",
        "image_source"        : "SmartTrainer AI Vector Reference",
        "description"         : "A common calisthenics exercise beginning from the prone position, exercising the pectoral muscles, triceps, and anterior deltoids.",
        "display_name"        : "Push-Ups",
        "key"                 : ord('p'),

        # Primary joint: elbow (shoulder→elbow→wrist)
        "landmarks_left"      : (11, 13, 15),
        "landmarks_right"     : (12, 14, 16),
        "angle_range"         : (70, 170),   # 170° = up, 70° = chest to floor
        "stage_down_threshold": 100,   # elbow clearly bent
        "stage_up_threshold"  : 155,   # elbow clearly extended
        "rom_min_angle"       : 100,

        # Posture: body plank alignment (shoulder→hip→ankle)
        "posture_chain_left"  : (11, 23, 27),
        "posture_chain_right" : (12, 24, 28),
        "posture_min_angle"   : 155,   # below → hips sagging
        "posture_max_angle"   : 200,   # above → hips piking up

        "symmetry_threshold"  : 20,
        "clean_depth"         : 70,
        "kcal_per_rep"        : 0.29,
        "depth_direction"     : "down",

        # Diagnostic confirmed: ankles (27,28) are almost NEVER visible from the
        # side during push-ups (person is horizontal, feet at weird angle).
        # Required set reduced to landmarks actually visible in side-view push-ups.
        "required_landmarks"  : [11, 12, 13, 14, 23, 24],

        "feedback_low"        : "Go Deeper!",
        "feedback_good"       : "Perfect!",
        "feedback_posture"    : "Keep Body Straight!",

        # ── Quality Gate Overrides (Independent Layer) ──────────────
        "min_duration_secs"   : 1.0,
        "min_rom_travel_deg"  : 45.0,
        "max_posture_deviation_deg": 15.0,

        "autodetect_signals"  : ["elbow_flex", "torso_horizontal"],
    },

    # ── Bicep Curls ─────────────────────────────────────────────
    "curls": {
        "image_url"           : "app/static/images/curls.jpg",
        "image_source"        : "SmartTrainer AI Vector Reference",
        "description"         : "A weight-training exercise that targets the biceps brachii muscle.",
        "display_name"        : "Bicep Curls",
        "key"                 : ord('c'),

        # Primary joint: elbow (shoulder→elbow→wrist)
        "landmarks_left"      : (11, 13, 15),
        "landmarks_right"     : (12, 14, 16),
        "angle_range"         : (50, 170),   # 170° = arm straight, 50° = full curl
        "stage_down_threshold": 90,    # arm clearly curled (elbow <90°)
        "stage_up_threshold"  : 150,   # arm clearly extended
        "rom_min_angle"       : 80,

        # Posture: shoulder must stay still (shoulder→elbow→hip)
        # We validate that the shoulder-elbow angle doesn't swing
        "posture_chain_left"  : (23, 11, 13),
        "posture_chain_right" : (24, 12, 14),
        "posture_min_angle"   : 0,
        "posture_max_angle"   : 175,    # corrected to allow relaxed posture
        "posture_delta_threshold": 20, # for relative swing check

        "symmetry_threshold"  : 30,
        "clean_depth"         : 70,
        "kcal_per_rep"        : 0.18,
        "depth_direction"     : "down",

        "required_landmarks"  : [11, 12, 13, 14, 15, 16],

        "feedback_low"        : "Curl Higher!",
        "feedback_good"       : "Great Range!",
        "feedback_posture"    : "Keep Elbows Still!",

        # ── Quality Gate Overrides (Independent Layer) ──────────────
        "min_duration_secs"   : 1.0,
        "min_rom_travel_deg"  : 50.0,
        "max_posture_deviation_deg": 10.0,  # dedicated quality gate check (does not affect 20deg base posture score)

        "autodetect_signals"  : ["elbow_flex", "torso_upright"],
    },

    # ── Lunges ──────────────────────────────────────────────────
    "lunges": {
        "image_url"           : "app/static/images/lunges.jpg",
        "image_source"        : "SmartTrainer AI Vector Reference",
        "description"         : "A single-leg bodyweight exercise that works the hips, glutes, quads, hamstrings, and core.",
        "display_name"        : "Lunges",
        "key"                 : ord('l'),

        # Primary joint: front knee (hip→knee→ankle) – right leg
        "landmarks_left"      : (23, 25, 27),
        "landmarks_right"     : (24, 26, 28),
        "angle_range"         : (80, 170),
        "stage_down_threshold": 110,   # front knee clearly bent
        "stage_up_threshold"  : 155,   # leg clearly straightened
        "rom_min_angle"       : 105,

        # Posture: torso upright (shoulder→hip→knee)
        "posture_chain_left"  : (11, 23, 25),
        "posture_chain_right" : (12, 24, 26),
        "posture_min_angle"   : 70,
        "posture_max_angle"   : 180,

        "symmetry_threshold"  : 30,    # lunges are inherently asymmetric
        "clean_depth"         : 65,
        "kcal_per_rep"        : 0.28,
        "depth_direction"     : "down",

        "required_landmarks"  : [11, 12, 23, 24, 25, 26, 27, 28],

        "feedback_low"        : "Lunge Deeper!",
        "feedback_good"       : "Great Lunge!",
        "feedback_posture"    : "Keep Torso Upright!",

        # ── Quality Gate Overrides (Independent Layer) ──────────────
        "min_duration_secs"   : 1.3,
        "min_rom_travel_deg"  : 40.0,
        "max_posture_deviation_deg": 15.0,

        "autodetect_signals"  : ["knee_flex", "split_stance"],
    },

    # ── Shoulder Press ───────────────────────────────────────────
    "shoulder_press": {
        "image_url"           : "app/static/images/shoulder_press.jpg",
        "image_source"        : "SmartTrainer AI Vector Reference",
        "description"         : "An exercise in which a weight is pressed straight upwards from the shoulders until the arms are locked out overhead.",
        "display_name"        : "Shoulder Press",
        "key"                 : ord('h'),   # 'h' for o'H'P (overhead press)

        # Primary joint: elbow (shoulder→elbow→wrist) overhead extension
        "landmarks_left"      : (11, 13, 15),
        "landmarks_right"     : (12, 14, 16),
        "angle_range"         : (80, 170),
        "stage_down_threshold": 100,   # elbow clearly bent at starting position
        # Diagnostic: only 16 frames hit 155°. Lowered to 145° to catch the
        # full extension that our angle smoother rounds down slightly.
        "stage_up_threshold"  : 145,   # arm clearly pressed overhead
        "rom_min_angle"       : 105,

        # Posture: torso alignment – no leaning back (hip→shoulder→elbow)
        "posture_chain_left"  : (23, 11, 13),
        "posture_chain_right" : (24, 12, 14),
        "posture_min_angle"   : 60,
        "posture_max_angle"   : 185,   # corrected for overhead extension range

        "symmetry_threshold"  : 20,
        "clean_depth"         : 65,
        "kcal_per_rep"        : 0.20,
        "depth_direction"     : "up",

        "required_landmarks"  : [11, 12, 13, 14, 15, 16, 23, 24],

        "feedback_low"        : "Press Higher!",
        "feedback_good"       : "Full Extension!",
        "feedback_posture"    : "Don't Arch Your Back!",

        # ── Quality Gate Overrides (Independent Layer) ──────────────
        "min_duration_secs"   : 1.1,
        "min_rom_travel_deg"  : 40.0,
        "max_posture_deviation_deg": 15.0,

        "autodetect_signals"  : ["elbow_flex", "arms_overhead"],
    },
}

# ================================================================
#  YOGA POSE CONFIGURATION
# ================================================================
#  Separate from EXERCISE_CONFIG: yoga is hold-based, not rep-based.
#  landmark_checks: chain=(p1,p2,p3) angle at p2, range=(lo,hi) degrees.
#  All chains verified in scratch/yoga_angle_dryrun_v3.py (32/32 PASS).
# ================================================================

YOGA_POSE_CONFIG: dict = {

    "mountain_pose": {
        "image_url"           : "app/static/images/mountain_pose.jpg",
        "image_source"        : "SmartTrainer AI Vector Reference",
        "description"         : "Tadasana (Mountain Pose) is a basic standing asana in modern yoga as exercise.",
        "display_name": "Mountain Pose", "sanskrit": "Tadasana",
        "min_hold_secs": 15, "alignment_threshold": 75,
        "landmark_checks": [
            {"chain": (23, 25, 27), "range": (165, 180), "feedback": "Straighten your left leg"},
            {"chain": (24, 26, 28), "range": (165, 180), "feedback": "Straighten your right leg"},
            {"chain": (25, 23, 11), "range": (160, 180), "feedback": "Stand tall - hips over ankles"},
            {"chain": (26, 24, 12), "range": (160, 180), "feedback": "Stand tall - hips over ankles"},
            {"chain": (23, 11, 13), "range": (0, 30),    "feedback": "Relax your left arm to your side"},
            {"chain": (24, 12, 14), "range": (0, 30),    "feedback": "Relax your right arm to your side"},
        ],
        "cues": {"start": "Stand with feet together, arms at your sides",
                 "hold": "Stay grounded and breathe steadily",
                 "complete": "Mountain Pose complete!"},
    },

    "tree_pose": {
        "image_url"           : "app/static/images/tree_pose.jpg",
        "image_source"        : "SmartTrainer AI Vector Reference",
        "description"         : "Vrksasana (Tree Pose) is a balancing asana. It is one of the very few standing poses in medieval hatha yoga.",
        "display_name": "Tree Pose", "sanskrit": "Vrikshasana",
        "min_hold_secs": 20, "alignment_threshold": 75,
        "landmark_checks": [
            {"chain": (23, 25, 27), "range": (165, 180), "feedback": "Straighten your standing leg"},
            {"chain": (25, 23, 11), "range": (155, 180), "feedback": "Square your hips and stand tall"},
            {"chain": (24, 26, 28), "range": (50, 110),  "feedback": "Raise your bent knee higher and rotate it outward"},
        ],
        "cues": {"start": "Stand on your left leg, raise right foot to inner thigh",
                 "hold": "Find your balance - breathe steadily",
                 "complete": "Tree Pose complete!"},
    },

    "warrior_ii": {
        "image_url"           : "app/static/images/warrior_2.jpg",
        "image_source"        : "SmartTrainer AI Vector Reference",
        "description"         : "Virabhadrasana II (Warrior II Pose) is a standing yoga pose that enhances strength, stability, and endurance.",
        "display_name": "Warrior II", "sanskrit": "Virabhadrasana II",
        "min_hold_secs": 30, "alignment_threshold": 75,
        "landmark_checks": [
            {"chain": (11, 13, 15), "range": (165, 180), "feedback": "Straighten your left arm"},
            {"chain": (12, 14, 16), "range": (165, 180), "feedback": "Straighten your right arm"},
            {"chain": (23, 11, 13), "range": (70, 110),  "feedback": "Extend left arm to shoulder height"},
            {"chain": (24, 12, 14), "range": (70, 110),  "feedback": "Extend right arm to shoulder height"},
            {"chain": (11, 23, 25), "range": (100, 160), "feedback": "Sink hips lower, widen your stance"},
            {"chain": (12, 24, 26), "range": (100, 160), "feedback": "Sink hips lower, widen your stance"},
        ],
        "cues": {"start": "Wide stance - front knee bent, arms extended to the sides at shoulder height",
                 "hold": "Hold strong - gaze over your front fingertips",
                 "complete": "Warrior II complete!"},
    },

    "chair_pose": {
        "image_url"           : "app/static/images/chair_pose.jpg",
        "image_source"        : "SmartTrainer AI Vector Reference",
        "description"         : "Utkatasana (Chair Pose) is a standing asana that stretches the shoulders and chest and strengthens the thighs and ankles.",
        "display_name": "Chair Pose", "sanskrit": "Utkatasana",
        "min_hold_secs": 45, "alignment_threshold": 75,
        # torso-lean (25->23->11) AND arm-overhead (23->11->13) must both pass.
        # Forward fold alone fails arm check. Upright squat alone fails torso check.
        "landmark_checks": [
            {"chain": (23, 11, 13), "range": (130, 180), "feedback": "Raise your left arm overhead"},
            {"chain": (24, 12, 14), "range": (130, 180), "feedback": "Raise your right arm overhead"},
            {"chain": (11, 13, 15), "range": (155, 180), "feedback": "Straighten your left arm"},
            {"chain": (12, 14, 16), "range": (155, 180), "feedback": "Straighten your right arm"},
            {"chain": (25, 23, 11), "range": (120, 165), "feedback": "Sit deeper - lean torso slightly forward from hips"},
            {"chain": (26, 24, 12), "range": (120, 165), "feedback": "Sit deeper - lean torso slightly forward from hips"},
        ],
        "cues": {"start": "Feet together, sink into a partial squat, raise arms overhead",
                 "hold": "Hold the burn - arms up, weight in your heels",
                 "complete": "Chair Pose complete!"},
    },

    "triangle_pose": {
        "image_url"           : "app/static/images/triangle_pose.jpg",
        "image_source"        : "SmartTrainer AI Vector Reference",
        "description"         : "Trikonasana (Triangle Pose) is a standing asana that stretches the legs and torso, mobilizes the hips, and promotes deep breathing.",
        "display_name": "Triangle Pose", "sanskrit": "Trikonasana",
        "min_hold_secs": 20, "alignment_threshold": 75,
        "landmark_checks": [
            {"chain": (11, 23, 24), "range": (50, 90),   "feedback": "Tilt your torso further sideways - reach toward the floor"},
            {"chain": (11, 13, 15), "range": (140, 180), "feedback": "Extend your top arm straight up"},
            {"chain": (24, 12, 14), "range": (140, 180), "feedback": "Reach your bottom hand toward the floor"},
            {"chain": (23, 25, 27), "range": (160, 180), "feedback": "Straighten your left leg"},
            {"chain": (24, 26, 28), "range": (160, 180), "feedback": "Straighten your right leg"},
        ],
        "cues": {"start": "Wide stance - right hand toward floor, left arm reaching up",
                 "hold": "Both legs straight, top arm up - breathe into the stretch",
                 "complete": "Triangle Pose complete!"},
    },

    "warrior_i": {
        "image_url"           : "app/static/images/warrior_1.jpg",
        "image_source"        : "SmartTrainer AI Vector Reference",
        "description"         : "Virabhadrasana I (Warrior I Pose) is a lunge with the back foot planted and arms reaching overhead, stretching the front body.",
        "display_name": "Warrior I", "sanskrit": "Virabhadrasana I",
        "min_hold_secs": 30, "alignment_threshold": 75,
        "landmark_checks": [
            {"chain": (23, 11, 13), "range": (130, 180), "feedback": "Raise your left arm overhead"},
            {"chain": (24, 12, 14), "range": (130, 180), "feedback": "Raise your right arm overhead"},
            {"chain": (11, 13, 15), "range": (155, 180), "feedback": "Straighten your left arm"},
            {"chain": (12, 14, 16), "range": (155, 180), "feedback": "Straighten your right arm"},
            {"chain": (26, 24, 12), "range": (140, 180), "feedback": "Square your torso forward"},
            {"chain": (11, 23, 25), "range": (120, 165), "feedback": "Sink deeper into your front knee lunge"},
        ],
        "cues": {"start": "Lunge stance - front knee over ankle, arms raised overhead",
                 "hold": "Strong foundation - hips square, arms pressing up",
                 "complete": "Warrior I complete!"},
    },
}

