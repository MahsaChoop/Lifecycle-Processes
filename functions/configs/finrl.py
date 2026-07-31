"""Dataset config: FinRL."""
from functions.config import DATA_RAW, RESULTS_FIGURES, RESULTS_TABLES

DATASET_NAME = "FinRL"
DUCKDB_PATH = DATA_RAW / "FinRL.duckdb"
SQLITE_PATH = DATA_RAW / "FinRL.sqlite"

CLOSED_EVENT_TYPE_ID = 110
CREATE_EVENT_TYPE_ID = 31
COMMIT_EVENT_TYPE_ID = 43
TITLE_ATTRIBUTE_ID = 6
COMMIT_MESSAGE_ATTRIBUTE_ID = 18

ISSUE_OBJECT_TYPE = "issue"
COMMIT_OBJECT_TYPE = "commit"
END_ACTIVITY_1 = "closed"
END_ACTIVITY_2 = "head_ref_deleted"

TABLES_DIR = RESULTS_TABLES / DATASET_NAME
FIGURES_DIR = RESULTS_FIGURES / DATASET_NAME

# OCEL2 event tables present in this dataset's sqlite file (27 tables).
EVENT_SUBTABLES = [
    "event_assigned",
    "event_base_ref_changed",
    "event_base_ref_deleted",
    "event_closed",
    "event_comment_deleted",
    "event_commented",
    "event_committed",
    "event_connected",
    "event_convert_to_draft",
    "event_created",
    "event_cross_referenced",
    "event_head_ref_deleted",
    "event_head_ref_force_pushed",
    "event_head_ref_restored",
    "event_labeled",
    "event_mentioned",
    "event_merged",
    "event_ready_for_review",
    "event_referenced",
    "event_renamed",
    "event_reopened",
    "event_review_requested",
    "event_reviewed",
    "event_subscribed",
    "event_unassigned",
    "event_unlabeled",
    "event_unsubscribed",
]
