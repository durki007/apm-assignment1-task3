"""Single source of truth for Part 1 (olympic transport) design constants and names."""
from apm_assignment.paths import DATA_DIR, MODELS_DIR, FIGURES_DIR, ROOT_DIR  # noqa: F401

# ── Reproducibility ────────────────────────────────────────────────────────
SEED = 42

# ── Object types (§4.1) ───────────────────────────────────────────────────
OBJECT_TYPES = ["Passenger", "TravelTicket", "GroupBooking", "Departure"]

# Roles referenced by requirements
OT_OA     = "TravelTicket"   # attribute-carrying type (R vi)
OT_SYNC   = "Passenger"      # synchronizing type (R viii)
OT_PAIRED1 = "Passenger"
OT_PAIRED2 = "TravelTicket"
OT_PARENT = "GroupBooking"
OT_CHILD  = "Passenger"

# ── Event types (§4.3) ────────────────────────────────────────────────────
EVENT_TYPES = [
    "CreateGroupBooking",
    "IssueTravelTicket",
    "AssignToDeparture",
    "BoardViaAccreditationLane",
    "ValidateAtPublicGate",
    "Depart",
    "CompleteJourney",
]

# Roles referenced by requirements
ET_GROUP = "AssignToDeparture"   # batch group event (R viii)
ET_SYNC  = "Depart"              # synchronization event (R viii)
ET_X1    = "BoardViaAccreditationLane"   # data-driven branch 1 (R vii)
ET_X2    = "ValidateAtPublicGate"        # data-driven branch 2 (R vii)

# ── Object attribute (§4.2) ───────────────────────────────────────────────
OA_NAME        = "fare_class"
FARE_CLASSES   = ["accredited", "standard"]
CROSSOVER_PROB = 0.1   # probability of taking the "wrong" boarding lane

# ── Sizing (§4.9) ─────────────────────────────────────────────────────────
N_BOOKINGS                  = 12
PASSENGERS_PER_BOOKING_RANGE = (2, 5)   # inclusive on both ends
N_DEPARTURES                = 10

# ── E2O specification (§4.4) ──────────────────────────────────────────────
# Maps each event type to the object types it relates to.
E2O_SPEC = {
    "CreateGroupBooking":       ["Passenger", "GroupBooking"],
    "IssueTravelTicket":        ["Passenger", "TravelTicket"],
    "AssignToDeparture":        ["Passenger", "Departure"],
    "BoardViaAccreditationLane": ["Passenger", "TravelTicket"],
    "ValidateAtPublicGate":     ["Passenger", "TravelTicket"],
    "Depart":                   ["Passenger", "Departure"],
    "CompleteJourney":          ["Passenger"],
}

# ── O2O specification (§4.5) ──────────────────────────────────────────────
# List of (source_type, qualifier, target_type, cardinality_note)
O2O_SPEC = [
    ("Passenger", "holds",      "TravelTicket", "one-to-one"),
    ("Passenger", "belongs_to", "GroupBooking",  "many-to-one"),
]
