"""
Checkpoint 7B — Unit Tests for Explainable Anomaly Rule Engine

Tests:
  1. normal project
  2. long administrative delay rule
  3. high sanction amount rule
  4. early tenure recommendation rule
  5. multiple triggered rules (multi-signal)
  6. model anomaly without rule anomaly
  7. rule anomaly without model anomaly
  8. completely normal record
  9. correct feature-name output formatting
  10. deterministic results
"""

import pytest
import pandas as pd
import numpy as np

from ml_modules.financial.anomaly_rules import (
    RULE_LONG_DELAY,
    RULE_HIGH_SANCTION,
    RULE_EARLY_TENURE,
    RULE_MULTI_SIGNAL,
    RULE_MODEL_ANOMALY,
    RuleEngineConfig,
    evaluate_record_anomalies,
    evaluate_dataset_rules,
)


@pytest.fixture
def normal_record():
    return {
        "sanction_amount": 300000.0,
        "rec_to_sanc_days": 80.0,
        "days_since_tenure_start": 350.0,
    }


@pytest.fixture
def default_config():
    return RuleEngineConfig()


# ── 1. Completely Normal Record ────────────────────────────────────────────────
def test_completely_normal_record(normal_record, default_config):
    res = evaluate_record_anomalies(
        record=normal_record,
        model_prediction=1,
        anomaly_score=0.05,
        config=default_config,
    )
    assert res["is_anomalous"] is False
    assert res["anomaly_features"] == []
    assert res["anomaly_score"] == 0.05


# ── 2. Long Administrative Delay Rule ─────────────────────────────────────────
def test_long_administrative_delay(normal_record, default_config):
    rec = normal_record.copy()
    rec["rec_to_sanc_days"] = 350.0  # > 286 threshold
    res = evaluate_record_anomalies(
        record=rec,
        model_prediction=1,
        anomaly_score=0.02,
        config=default_config,
    )
    assert res["is_anomalous"] is True
    assert RULE_LONG_DELAY in res["anomaly_features"]
    assert len(res["anomaly_features"]) == 1


# ── 3. High Sanction Amount Rule ───────────────────────────────────────────────
def test_high_sanction_amount(normal_record, default_config):
    rec = normal_record.copy()
    rec["sanction_amount"] = 2500000.0  # > 1,198,014 threshold
    res = evaluate_record_anomalies(
        record=rec,
        model_prediction=1,
        anomaly_score=0.03,
        config=default_config,
    )
    assert res["is_anomalous"] is True
    assert RULE_HIGH_SANCTION in res["anomaly_features"]
    assert len(res["anomaly_features"]) == 1


# ── 4. Early Tenure Recommendation Rule ────────────────────────────────────────
def test_early_tenure_recommendation(normal_record, default_config):
    rec = normal_record.copy()
    rec["days_since_tenure_start"] = 60.0  # < 113 threshold
    res = evaluate_record_anomalies(
        record=rec,
        model_prediction=1,
        anomaly_score=0.01,
        config=default_config,
    )
    assert res["is_anomalous"] is True
    assert RULE_EARLY_TENURE in res["anomaly_features"]
    assert len(res["anomaly_features"]) == 1


# ── 5. Multiple Triggered Rules (Multi-Signal) ─────────────────────────────────
def test_multiple_triggered_rules_multi_signal(normal_record, default_config):
    rec = normal_record.copy()
    rec["rec_to_sanc_days"] = 450.0         # > 286
    rec["sanction_amount"] = 3000000.0       # > 1,198,014
    rec["days_since_tenure_start"] = 50.0   # < 113

    # Model anomaly (-1) + score <= cutoff
    res = evaluate_record_anomalies(
        record=rec,
        model_prediction=-1,
        anomaly_score=-0.15,
        config=default_config,
    )
    assert res["is_anomalous"] is True
    assert RULE_LONG_DELAY in res["anomaly_features"]
    assert RULE_HIGH_SANCTION in res["anomaly_features"]
    assert RULE_EARLY_TENURE in res["anomaly_features"]
    assert RULE_MULTI_SIGNAL in res["anomaly_features"]


# ── 6. Model Anomaly Without Rule Anomaly ──────────────────────────────────────
def test_model_anomaly_without_rule_anomaly(normal_record, default_config):
    res = evaluate_record_anomalies(
        record=normal_record,
        model_prediction=-1,
        anomaly_score=-0.10,
        config=default_config,
    )
    assert res["is_anomalous"] is True
    assert res["anomaly_features"] == [RULE_MODEL_ANOMALY]


# ── 7. Rule Anomaly Without Model Anomaly ──────────────────────────────────────
def test_rule_anomaly_without_model_anomaly(normal_record, default_config):
    rec = normal_record.copy()
    rec["rec_to_sanc_days"] = 300.0  # > 286

    # Model prediction 1 (normal), positive score
    res = evaluate_record_anomalies(
        record=rec,
        model_prediction=1,
        anomaly_score=0.04,
        config=default_config,
    )
    assert res["is_anomalous"] is True
    assert res["anomaly_features"] == [RULE_LONG_DELAY]


# ── 8. Log1p Input Format Compatibility ────────────────────────────────────────
def test_log1p_input_support(default_config):
    rec = {
        "log1p_sanction_amount": np.log1p(2000000.0),
        "rec_to_sanc_days": 50.0,
        "days_since_tenure_start": 200.0,
    }
    res = evaluate_record_anomalies(
        record=rec,
        model_prediction=1,
        anomaly_score=0.05,
        config=default_config,
    )
    assert res["is_anomalous"] is True
    assert RULE_HIGH_SANCTION in res["anomaly_features"]


# ── 9. Correct Feature Name Output Formatting ──────────────────────────────────
def test_correct_feature_name_outputs(default_config):
    rec = {
        "sanction_amount": 5000000.0,
        "rec_to_sanc_days": 600.0,
        "days_since_tenure_start": 300.0,
    }
    res = evaluate_record_anomalies(
        record=rec,
        model_prediction=-1,
        anomaly_score=-0.12,
        config=default_config,
    )
    # Output list contains exact string keys
    for feat in res["anomaly_features"]:
        assert isinstance(feat, str)
        assert feat in [
            RULE_LONG_DELAY,
            RULE_HIGH_SANCTION,
            RULE_EARLY_TENURE,
            RULE_MULTI_SIGNAL,
            RULE_MODEL_ANOMALY,
        ]


# ── 10. Deterministic Results ──────────────────────────────────────────────────
def test_deterministic_results(normal_record, default_config):
    res1 = evaluate_record_anomalies(normal_record, -1, -0.15, default_config)
    res2 = evaluate_record_anomalies(normal_record, -1, -0.15, default_config)
    assert res1 == res2


# ── 11. Batch Evaluation ───────────────────────────────────────────────────────
def test_evaluate_dataset_rules(normal_record, default_config):
    df = pd.DataFrame([
        normal_record,
        {"sanction_amount": 3000000.0, "rec_to_sanc_days": 80.0, "days_since_tenure_start": 300.0},
    ])
    preds = np.array([1, -1])
    scores = np.array([0.05, -0.10])

    res_df = evaluate_dataset_rules(df, preds, scores, default_config)
    assert len(res_df) == 2
    assert res_df.iloc[0]["is_anomalous"] == False
    assert res_df.iloc[1]["is_anomalous"] == True


# ── 12. Strict Model Score Cutoff & Prediction Independence Verifications ────
def test_model_score_cutoff_strictness(normal_record, default_config):
    # 1. score = -0.10 <= -0.093716 -> model anomaly
    res1 = evaluate_record_anomalies(normal_record, model_prediction=-1, anomaly_score=-0.10, config=default_config)
    assert res1["is_anomalous"] is True
    assert RULE_MODEL_ANOMALY in res1["anomaly_features"]

    # 2. score = -0.093716 (exact cutoff boundary) -> model anomaly
    res2 = evaluate_record_anomalies(normal_record, model_prediction=1, anomaly_score=-0.093716, config=default_config)
    assert res2["is_anomalous"] is True
    assert RULE_MODEL_ANOMALY in res2["anomaly_features"]

    # 3. score = -0.09 > -0.093716 -> NOT model anomaly
    res3 = evaluate_record_anomalies(normal_record, model_prediction=1, anomaly_score=-0.09, config=default_config)
    assert res3["is_anomalous"] is False
    assert res3["anomaly_features"] == []

    # 4. prediction = -1 with score = -0.09 -> NOT model anomaly (prediction == -1 ignored)
    res4 = evaluate_record_anomalies(normal_record, model_prediction=-1, anomaly_score=-0.09, config=default_config)
    assert res4["is_anomalous"] is False
    assert res4["anomaly_features"] == []

    # 5. domain rule alone can still trigger an alert (even if score = -0.09 > cutoff)
    rec_delay = normal_record.copy()
    rec_delay["rec_to_sanc_days"] = 350.0  # > 286
    res5 = evaluate_record_anomalies(rec_delay, model_prediction=1, anomaly_score=-0.09, config=default_config)
    assert res5["is_anomalous"] is True
    assert res5["anomaly_features"] == [RULE_LONG_DELAY]

    # 6. multiple domain rules + model anomaly (score <= cutoff) produces multi_signal_statistical_anomaly
    rec_multi = normal_record.copy()
    rec_multi["rec_to_sanc_days"] = 350.0       # > 286
    rec_multi["sanction_amount"] = 2500000.0     # > 1,198,014
    res6 = evaluate_record_anomalies(rec_multi, model_prediction=1, anomaly_score=-0.10, config=default_config)
    assert res6["is_anomalous"] is True
    assert RULE_LONG_DELAY in res6["anomaly_features"]
    assert RULE_HIGH_SANCTION in res6["anomaly_features"]
    assert RULE_MULTI_SIGNAL in res6["anomaly_features"]


