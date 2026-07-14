"""Tests for team-name normalization and merge logic (no API calls)."""

import pandas as pd
import pytest

from name_mapping import (
    add_merge_key,
    merge_features,
    normalize_name,
    report_coverage,
)


class TestNormalizeName:
    def test_maps_known_aliases(self):
        assert normalize_name("Mississippi") == normalize_name("Ole Miss")
        assert normalize_name("Southern California") == normalize_name("USC")
        assert normalize_name("Appalachian State") == normalize_name("App State")
        assert normalize_name("UT San Antonio") == normalize_name("UTSA")

    def test_strips_accents_and_punctuation(self):
        assert normalize_name("San José State") == normalize_name("San Jose State")
        assert normalize_name("Hawai'i") == normalize_name("Hawaii")

    def test_case_and_whitespace_insensitive(self):
        assert normalize_name("  ohio STATE ") == "ohio state"

    def test_distinct_teams_stay_distinct(self):
        assert normalize_name("Miami") != normalize_name("Miami (OH)")
        assert normalize_name("USC") != normalize_name("South Carolina")


class TestMergeFeatures:
    def _base(self):
        base = pd.DataFrame(
            {
                "team": ["Ole Miss", "USC", "Ohio State"],
                "fpi": [15.0, 12.0, 25.0],
                "conference": ["SEC", "Big Ten", "Big Ten"],
            }
        )
        return add_merge_key(base, "team")

    def test_merges_despite_alias_mismatch(self):
        feat = add_merge_key(
            pd.DataFrame(
                {
                    "school": ["Mississippi", "Southern California", "Ohio State"],
                    "talent": [900.0, 950.0, 990.0],
                }
            ),
            "school",
        ).drop(columns="school")
        merged, coverage = merge_features(self._base(), {"talent": feat})
        assert coverage["talent"]["matched"] == 3
        assert coverage["talent"]["unmatched_teams"] == []
        assert merged.loc[merged["team"] == "Ole Miss", "talent"].iloc[0] == 900.0

    def test_reports_unmatched_teams(self):
        feat = add_merge_key(
            pd.DataFrame({"school": ["Ohio State"], "talent": [990.0]}), "school"
        ).drop(columns="school")
        merged, coverage = merge_features(self._base(), {"talent": feat})
        assert coverage["talent"]["matched"] == 1
        assert set(coverage["talent"]["unmatched_teams"]) == {"Ole Miss", "USC"}
        assert merged["talent"].isna().sum() == 2

    def test_duplicate_feature_rows_do_not_multiply_base(self):
        feat = add_merge_key(
            pd.DataFrame(
                {"school": ["Ohio State", "Ohio State"], "talent": [990.0, 100.0]}
            ),
            "school",
        ).drop(columns="school")
        merged, _ = merge_features(self._base(), {"talent": feat})
        assert len(merged) == 3

    def test_report_coverage_format(self):
        _, coverage = merge_features(
            self._base(),
            {
                "talent": add_merge_key(
                    pd.DataFrame({"school": ["Ohio State"], "talent": [1.0]}), "school"
                ).drop(columns="school")
            },
        )
        text = report_coverage(coverage)
        assert "talent" in text and "1/3" in text and "Ole Miss" in text


class TestPickCol:
    def test_camel_and_snake_case(self):
        from analysis import pick_col

        camel = pd.DataFrame({"totalPPA": [1.0], "team": ["A"]})
        snake = pd.DataFrame({"total_ppa": [1.0], "team": ["A"]})
        candidates = ["totalPPA", "total_ppa"]
        assert pick_col(camel, candidates, "test") == "totalPPA"
        assert pick_col(snake, candidates, "test") == "total_ppa"
        with pytest.raises(KeyError):
            pick_col(pd.DataFrame({"x": [1]}), candidates, "test")
