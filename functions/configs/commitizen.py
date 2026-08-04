"""Dataset config: Commitizen."""
from functions.config import DATA_RAW, RESULTS_FIGURES, RESULTS_FIGURES_NO_TITLES, RESULTS_TABLES

DATASET_NAME = "commitizen"
DUCKDB_PATH = DATA_RAW / "commitizen.duckdb"
SQLITE_PATH = DATA_RAW / "ocel2_commitizen.sqlite"

CLOSED_EVENT_TYPE_ID = 105
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
FIGURES_NO_TITLES_DIR = RESULTS_FIGURES_NO_TITLES / DATASET_NAME

# OCEL2 event tables present in this dataset's sqlite file (43 tables).
# Kept in the order the pre-refactor SUBTABLES list used, so the UNION ALL and
# the non-stable sort downstream of it produce identical output.
EVENT_SUBTABLES = [
    "event_assigned", "event_closed", "event_commented", "event_committed",
    "event_created", "event_cross_referenced", "event_labeled", "event_merged",
    "event_referenced", "event_renamed", "event_reopened", "event_reviewed",
    "event_review_requested", "event_subscribed", "event_head_ref_deleted",
    "event_head_ref_force_pushed", "event_ready_for_review",
    "event_convert_to_draft", "event_unlabeled", "event_milestoned",
    "event_demilestoned", "event_unassigned", "event_mentioned",
    "event_auto_merge_disabled", "event_auto_rebase_enabled",
    "event_auto_squash_enabled", "event_base_ref_changed",
    "event_base_ref_deleted", "event_base_ref_force_pushed",
    "event_connected", "event_converted_to_discussion",
    "event_copilot_work_finished", "event_copilot_work_started",
    "event_head_ref_restored", "event_issue_type_added",
    "event_issue_type_changed", "event_locked", "event_parent_issue_added",
    "event_pinned", "event_review_request_removed",
    "event_sub_issue_added", "event_unsubscribed", "event_unpinned",
]
