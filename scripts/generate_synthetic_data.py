import os
import sys
import random
import numpy as np
import pandas as pd

def generate_mplads_data():
    # Fixed random seed for 100% reproducibility
    seed = 42
    np.random.seed(seed)
    random.seed(seed)

    total_projects = 500
    anomaly_counts = {
        "high_expenditure_low_progress": 6,
        "expenditure_exceeds_sanction": 6,
        "severe_progress_mismatch": 7,
        "zero_progress_high_release": 6
    }
    total_anomalies = sum(anomaly_counts.values())
    total_normal = total_projects - total_anomalies

    data = []
    project_counter = 1

    # 1. Generate Normal Projects (475 rows)
    for _ in range(total_normal):
        pid = f"MPLADS-2026-{project_counter:04d}"
        project_counter += 1

        # Monetary fields in actual INR/Rupees (₹5 Lakhs to ₹2.5 Crores)
        est_cost = float(round(random.uniform(500000, 25000000), -3))
        sanc_amt = float(round(est_cost * random.uniform(0.90, 1.00), -3))
        duration = random.randint(90, 730)
        elapsed = random.randint(1, duration)

        time_ratio = elapsed / duration

        # Realistic progress tracking time with natural variation/noise
        base_progress = time_ratio * 100
        noise = np.random.normal(0, 6)
        progress = int(round(np.clip(base_progress + noise, 5, 100)))

        # Ensure high time ratio or mature normal projects don't trigger anomaly rules
        if time_ratio >= 0.85:
            progress = max(progress, 65)

        # Funds released (milestone based with noise)
        funds_released_ratio = min(1.0, max(0.15, time_ratio + random.uniform(-0.08, 0.08)))
        funds_released = float(round(sanc_amt * funds_released_ratio, 2))
        funds_released = min(funds_released, sanc_amt)

        if funds_released / sanc_amt >= 0.50:
            progress = max(progress, 25)

        # Expenditure tracks progress & funds released (expenditure <= funds_released <= sanc_amt)
        exp_ratio = min(funds_released / sanc_amt, max(0.05, (progress / 100.0) * random.uniform(0.85, 1.0)))
        expenditure = float(round(sanc_amt * exp_ratio, 2))
        expenditure = min(expenditure, funds_released)

        if expenditure / sanc_amt >= 0.80:
            progress = max(progress, 70)

        data.append({
            "project_id": pid,
            "estimated_cost": est_cost,
            "sanctioned_amount": sanc_amt,
            "funds_released": funds_released,
            "expenditure": expenditure,
            "current_progress_pct": progress,
            "project_duration_days": duration,
            "days_elapsed": elapsed,
            "is_anomaly_injected": 0,
            "anomaly_type_injected": "none"
        })

    # 2. Inject Anomaly Projects (25 rows)
    # Category 1: high_expenditure_low_progress (6 rows)
    for _ in range(anomaly_counts["high_expenditure_low_progress"]):
        pid = f"MPLADS-2026-{project_counter:04d}"
        project_counter += 1

        est_cost = float(round(random.uniform(1000000, 20000000), -3))
        sanc_amt = float(round(est_cost * random.uniform(0.92, 1.00), -3))
        duration = random.randint(180, 500)
        elapsed = random.randint(90, duration)

        # expenditure = 80%–95% of sanctioned_amount
        exp_ratio = random.uniform(0.82, 0.94)
        expenditure = float(round(sanc_amt * exp_ratio, 2))

        # current_progress_pct = 5%–20%
        progress = random.randint(5, 20)

        # funds_released >= expenditure
        funds_released = float(round(sanc_amt * random.uniform(exp_ratio, 1.00), 2))
        funds_released = min(funds_released, sanc_amt)

        data.append({
            "project_id": pid,
            "estimated_cost": est_cost,
            "sanctioned_amount": sanc_amt,
            "funds_released": funds_released,
            "expenditure": expenditure,
            "current_progress_pct": progress,
            "project_duration_days": duration,
            "days_elapsed": elapsed,
            "is_anomaly_injected": 1,
            "anomaly_type_injected": "high_expenditure_low_progress"
        })

    # Category 2: expenditure_exceeds_sanction (6 rows)
    for _ in range(anomaly_counts["expenditure_exceeds_sanction"]):
        pid = f"MPLADS-2026-{project_counter:04d}"
        project_counter += 1

        est_cost = float(round(random.uniform(1000000, 20000000), -3))
        sanc_amt = float(round(est_cost * random.uniform(0.90, 1.00), -3))
        duration = random.randint(180, 500)
        elapsed = random.randint(90, duration)

        # expenditure = 110%–150% of sanctioned_amount
        expenditure = float(round(sanc_amt * random.uniform(1.12, 1.48), 2))
        progress = random.randint(50, 90)

        # funds_released <= sanctioned_amount
        funds_released = float(round(sanc_amt * random.uniform(0.85, 1.00), 2))
        funds_released = min(funds_released, sanc_amt)

        data.append({
            "project_id": pid,
            "estimated_cost": est_cost,
            "sanctioned_amount": sanc_amt,
            "funds_released": funds_released,
            "expenditure": expenditure,
            "current_progress_pct": progress,
            "project_duration_days": duration,
            "days_elapsed": elapsed,
            "is_anomaly_injected": 1,
            "anomaly_type_injected": "expenditure_exceeds_sanction"
        })

    # Category 3: severe_progress_mismatch (7 rows)
    for _ in range(anomaly_counts["severe_progress_mismatch"]):
        pid = f"MPLADS-2026-{project_counter:04d}"
        project_counter += 1

        est_cost = float(round(random.uniform(1000000, 20000000), -3))
        sanc_amt = float(round(est_cost * random.uniform(0.90, 1.00), -3))
        duration = random.randint(200, 600)
        elapsed = int(duration * random.uniform(0.86, 0.98))  # days_elapsed = 85%–100% of duration

        funds_released = float(round(sanc_amt * random.uniform(0.76, 0.89), 2))  # funds_released = 75%–90% of sanc
        progress = random.randint(5, 14)  # current_progress_pct < 15%, > 0
        expenditure = float(round(sanc_amt * random.uniform(0.10, 0.35), 2))  # exp / sanc < 0.80

        data.append({
            "project_id": pid,
            "estimated_cost": est_cost,
            "sanctioned_amount": sanc_amt,
            "funds_released": funds_released,
            "expenditure": expenditure,
            "current_progress_pct": progress,
            "project_duration_days": duration,
            "days_elapsed": elapsed,
            "is_anomaly_injected": 1,
            "anomaly_type_injected": "severe_progress_mismatch"
        })

    # Category 4: zero_progress_high_release (6 rows)
    for _ in range(anomaly_counts["zero_progress_high_release"]):
        pid = f"MPLADS-2026-{project_counter:04d}"
        project_counter += 1

        est_cost = float(round(random.uniform(1000000, 20000000), -3))
        sanc_amt = float(round(est_cost * random.uniform(0.90, 1.00), -3))
        duration = random.randint(200, 600)
        elapsed = random.randint(105, duration)  # days_elapsed > 100

        funds_released = float(round(sanc_amt * random.uniform(0.55, 0.82), 2))  # funds_released = 50%–85% of sanc
        progress = 0  # current_progress_pct = 0
        expenditure = float(round(sanc_amt * random.uniform(0.42, 0.70), 2))  # expenditure > 40% of sanc

        data.append({
            "project_id": pid,
            "estimated_cost": est_cost,
            "sanctioned_amount": sanc_amt,
            "funds_released": funds_released,
            "expenditure": expenditure,
            "current_progress_pct": progress,
            "project_duration_days": duration,
            "days_elapsed": elapsed,
            "is_anomaly_injected": 1,
            "anomaly_type_injected": "zero_progress_high_release"
        })

    # Shuffle dataset for random distribution across indices
    random.shuffle(data)

    df = pd.DataFrame(data)

    # Save to data/mock_mplads.csv
    os.makedirs("data", exist_ok=True)
    csv_path = os.path.join("data", "mock_mplads.csv")
    df.to_csv(csv_path, index=False)
    print(f"Dataset successfully created at {csv_path} with {len(df)} rows.")

    return df

def check_anomaly_definitions(row):
    # Rule 1: high_expenditure_low_progress
    c1 = (0.80 <= row['expenditure'] / row['sanctioned_amount'] <= 0.95) and (5 <= row['current_progress_pct'] <= 20)

    # Rule 2: expenditure_exceeds_sanction
    c2 = (row['expenditure'] > row['sanctioned_amount'])

    # Rule 3: severe_progress_mismatch
    c3 = ((row['days_elapsed'] / row['project_duration_days']) >= 0.85) and \
         (0.75 <= row['funds_released'] / row['sanctioned_amount'] <= 0.90) and \
         (0 < row['current_progress_pct'] < 15) and \
         ((row['expenditure'] / row['sanctioned_amount']) < 0.80)

    # Rule 4: zero_progress_high_release
    c4 = (row['current_progress_pct'] == 0) and \
         (0.50 <= row['funds_released'] / row['sanctioned_amount'] <= 0.85) and \
         ((row['expenditure'] / row['sanctioned_amount']) > 0.40) and \
         (row['days_elapsed'] > 100)

    matches = []
    if c1: matches.append("high_expenditure_low_progress")
    if c2: matches.append("expenditure_exceeds_sanction")
    if c3: matches.append("severe_progress_mismatch")
    if c4: matches.append("zero_progress_high_release")

    return matches

def verify_dataset(df):
    results = {}

    # 1. Basic counts
    results["total_rows"] = len(df)
    results["anomaly_rows"] = int(df['is_anomaly_injected'].sum())
    results["normal_rows"] = results["total_rows"] - results["anomaly_rows"]
    results["anomaly_pct"] = float((results["anomaly_rows"] / results["total_rows"]) * 100)
    results["anomaly_distribution"] = df[df['is_anomaly_injected'] == 1]['anomaly_type_injected'].value_counts().to_dict()

    # 2. Data Integrity Checks
    results["missing_values"] = int(df.isnull().sum().sum())
    results["duplicate_project_ids"] = int(df['project_id'].duplicated().sum())

    monetary_cols = ['estimated_cost', 'sanctioned_amount', 'funds_released', 'expenditure']
    results["negative_monetary_values"] = int((df[monetary_cols] < 0).sum().sum())

    results["progress_outside_0_100"] = int(((df['current_progress_pct'] < 0) | (df['current_progress_pct'] > 100)).sum())
    results["days_elapsed_gt_duration"] = int((df['days_elapsed'] > df['project_duration_days']).sum())

    # Normal projects constraint check (expenditure <= funds_released <= sanctioned_amount)
    normal_df = df[df['is_anomaly_injected'] == 0]
    normal_exp_violation = int((normal_df['expenditure'] > normal_df['funds_released']).sum() + 
                               (normal_df['funds_released'] > normal_df['sanctioned_amount']).sum())
    results["normal_constraint_violations"] = normal_exp_violation

    # 3. Anomaly Definition Verifications
    injected_satisfy_intended = 0
    injected_mutually_exclusive = 0
    normal_accidentally_satisfy = 0

    for _, row in df.iterrows():
        matches = check_anomaly_definitions(row)
        if row['is_anomaly_injected'] == 1:
            if len(matches) == 1:
                injected_mutually_exclusive += 1
                if matches[0] == row['anomaly_type_injected']:
                    injected_satisfy_intended += 1
        else:
            if len(matches) > 0:
                normal_accidentally_satisfy += 1

    results["injected_satisfy_intended"] = injected_satisfy_intended
    results["injected_mutually_exclusive"] = injected_mutually_exclusive
    results["normal_accidentally_satisfy"] = normal_accidentally_satisfy

    # Strict Assertions for Validation Requirements
    expected_dist = {
        "severe_progress_mismatch": 7,
        "expenditure_exceeds_sanction": 6,
        "high_expenditure_low_progress": 6,
        "zero_progress_high_release": 6
    }

    errors = []
    if results["total_rows"] != 500:
        errors.append(f"Total row count mismatch: expected 500, got {results['total_rows']}")
    if results["anomaly_rows"] != 25:
        errors.append(f"Anomaly count mismatch: expected 25, got {results['anomaly_rows']}")
    if results["normal_rows"] != 475:
        errors.append(f"Normal row count mismatch: expected 475, got {results['normal_rows']}")
    if results["anomaly_distribution"] != expected_dist:
        errors.append(f"Anomaly distribution mismatch: expected {expected_dist}, got {results['anomaly_distribution']}")
    if results["duplicate_project_ids"] != 0:
        errors.append(f"Duplicate project IDs found: {results['duplicate_project_ids']}")
    if results["missing_values"] != 0:
        errors.append(f"Missing values found: {results['missing_values']}")
    if results["negative_monetary_values"] != 0:
        errors.append(f"Negative monetary values found: {results['negative_monetary_values']}")
    if results["progress_outside_0_100"] != 0:
        errors.append(f"Progress outside 0-100 found: {results['progress_outside_0_100']}")
    if results["days_elapsed_gt_duration"] != 0:
        errors.append(f"Days elapsed > duration found: {results['days_elapsed_gt_duration']}")
    if results["normal_constraint_violations"] != 0:
        errors.append(f"Normal constraint violations: {results['normal_constraint_violations']}")
    if results["injected_satisfy_intended"] != 25:
        errors.append(f"Injected anomalies satisfying intended definition: expected 25, got {results['injected_satisfy_intended']}")
    if results["injected_mutually_exclusive"] != 25:
        errors.append(f"Injected anomalies mutually exclusive: expected 25, got {results['injected_mutually_exclusive']}")
    if results["normal_accidentally_satisfy"] != 0:
        errors.append(f"Normal projects accidentally satisfying anomaly definitions: {results['normal_accidentally_satisfy']}")

    results["validation_passed"] = (len(errors) == 0)
    results["validation_errors"] = errors

    return results

if __name__ == "__main__":
    df = generate_mplads_data()
    results = verify_dataset(df)

    print("\n================ VALIDATION RESULTS ================")
    for k, v in results.items():
        if k != "validation_errors":
            print(f"{k}: {v}")

    if not results["validation_passed"]:
        print("\n❌ VALIDATION FAILED WITH ERRORS:")
        for err in results["validation_errors"]:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("\n✅ ALL VALIDATION CHECKS PASSED SUCCESSFULLY!")
