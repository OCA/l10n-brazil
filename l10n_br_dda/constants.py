# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

# Model names live here so a rename (still to be confirmed) touches one place.
DEBIT_MODEL = "l10n_br_dda.debit"
SOURCE_MODEL = "l10n_br_dda.debit.source"
ALLOCATION_MODEL = "l10n_br_dda.allocation"
MATCH_MODEL = "l10n_br_dda.match"

STATES = [
    ("new", "New"),
    ("suggested", "Suggested"),
    ("linked", "Linked"),
    ("in_payment", "In payment order"),
    ("paid", "Paid"),
    ("paid_elsewhere", "Paid elsewhere"),
    ("ignored", "Ignored"),
    ("suspect", "Suspect"),
    ("cancelled", "Cancelled by beneficiary"),
    ("expired", "Expired"),
]
# States in which the boleto still waits for a decision (matching runs on them).
OPEN_STATES = ("new", "suggested", "suspect")
# States in which an allocation holds its payable line.
ACTIVE_STATES = ("linked", "in_payment")

SOURCE_TYPES = [("api", "API"), ("cnab", "CNAB file"), ("manual", "Manual")]

# Alert codes, comma separated in the alert_codes field.
ALERT_UNKNOWN_PARTNER = "unknown_partner"
ALERT_NO_TITLE = "no_title"
ALERT_DUPLICATE = "possible_duplicate"
ALERT_ASSIGNMENT = "assignment"

# Statuses of a boleto at the source (same names as the brbank library).
STATUS_OPEN = "ABERTO"
STATUS_PAID = "PAGO"
STATUS_CANCELLED = "CANCELADO"
STATUS_WRITTEN_OFF = "BAIXADO"
STATUS_REFUSED = "RECUSADO"

# Matching weights (PRD, section "Matching (v1)").
SCORE_IDENTITY_FULL = 40
SCORE_IDENTITY_PARTIAL = 25
SCORE_AMOUNT_EQUAL = 30
SCORE_AMOUNT_TOLERANCE = 15
SCORE_DUE_EQUAL = 20
SCORE_DUE_WINDOW = 10
SCORE_NUMBER_EQUAL = 10
MIN_SCORE = 50
MAX_MULTI_PARCELS = 5
MAX_MULTI_POOL = 10

IDENTITY_FULL = "full"
IDENTITY_ASSIGNMENT = "assignment"
IDENTITY_ROOT = "root"
