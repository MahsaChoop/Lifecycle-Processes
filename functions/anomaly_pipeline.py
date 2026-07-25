"""Run anomaly detection + state extraction and write tables (same as notebook cell 4)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from functions.anomaly import (
    build_weekly_titles_for_105,
    rolling_iqr_detect,
)
from functions.config import ANOMALY_EVENT_TYPE_ID, IQR_CONFIG, RESULTS_TABLES
from functions.state_extraction import VALID_SEVERITIES, extract_state_rule_based


def run_anomaly_state_extraction(weekly, eventsPerobj_df, objects_attributes, tables_dir=None):
    tables_dir = Path(tables_dir or RESULTS_TABLES)
    tables_dir.mkdir(parents=True, exist_ok=True)

    weekly_105_anomaly_frame = rolling_iqr_detect(weekly[ANOMALY_EVENT_TYPE_ID], **IQR_CONFIG)
    weekly_105_titles, event_105_title_join = build_weekly_titles_for_105(
        eventsPerobj_df,
        objects_attributes,
        event_type_id=ANOMALY_EVENT_TYPE_ID,
    )

    anomaly_context = weekly_105_anomaly_frame.loc[weekly_105_anomaly_frame['is_anomaly']].merge(
        weekly_105_titles,
        on='week_start',
        how='left',
    )
    anomaly_context['title_count'] = anomaly_context['title_count'].fillna(0).astype(int)
    anomaly_context['event_count'] = anomaly_context['event_count'].fillna(0).astype(int)
    anomaly_context['titles_in_week'] = anomaly_context['titles_in_week'].apply(
        lambda value: value if isinstance(value, list) else []
    )
    anomaly_context['event_descriptions'] = anomaly_context['event_descriptions'].apply(
        lambda value: value if isinstance(value, list) else []
    )
    anomaly_context['titles_text'] = anomaly_context['titles_text'].fillna('')

    state_columns = ['severity', 'component', 'reasoning', 'extraction_method', 'confidence']
    if anomaly_context.empty:
        state_rows = pd.DataFrame(columns=state_columns)
    else:
        state_rows = anomaly_context.apply(
            lambda row: extract_state_rule_based(row),
            axis=1,
            result_type='expand',
        ).reindex(columns=state_columns)

    anomaly_states = pd.concat([anomaly_context.reset_index(drop=True), state_rows], axis=1)

    expected_columns = [
        'week_start', 'value', 'is_anomaly', 'anomaly_direction', 'anomaly_score',
        'lower_bound', 'upper_bound', 'title_count', 'event_count',
        'severity', 'component', 'reasoning', 'extraction_method', 'confidence',
        'event_descriptions', 'titles_in_week',
    ]
    anomaly_states = anomaly_states.reindex(columns=expected_columns).sort_values('week_start')

    if not anomaly_states.empty:
        assert anomaly_states['severity'].isin(VALID_SEVERITIES).all(), 'Invalid severity found.'
        assert anomaly_states['component'].astype(str).str.split().str.len().le(4).all(), 'Component exceeds 4 words.'
        assert anomaly_states['reasoning'].astype(str).str.len().gt(0).all(), 'Missing reasoning found.'
        assert len(anomaly_states) == int(weekly_105_anomaly_frame['is_anomaly'].sum()), 'Anomaly row count mismatch.'

    print(f'Detected {len(anomaly_states)} rolling-IQR anomalies for event_type_id={ANOMALY_EVENT_TYPE_ID}.')
    print(
        'Joined title attribute rows: '
        f"{event_105_title_join['attribute_value'].notna().sum()} of {len(event_105_title_join)} event rows."
    )

    anomaly_states.to_csv(tables_dir / 'anomaly_states.csv', index=False)
    print(f"Saved anomaly states to {tables_dir / 'anomaly_states.csv'}")
    anomaly_context.to_csv(tables_dir / 'anomaly_context.csv', index=False)

    return weekly_105_anomaly_frame, anomaly_context, anomaly_states, event_105_title_join
