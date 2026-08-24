"""
MPLADS Early Warning System — Pipeline Runner
===============================================
One-command orchestrator: Generate Data → Train Models → Launch API Server.

Usage:
    python run_pipeline.py              # Full pipeline (generate + train + serve)
    python run_pipeline.py --no-serve   # Generate + train only (no API server)
    python run_pipeline.py --serve-only # Start API server (models must exist)
"""

import sys
import time
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="MPLADS Early Warning System Pipeline"
    )
    parser.add_argument(
        "--no-serve",
        action="store_true",
        help="Generate data and train models, but don't start the API server.",
    )
    parser.add_argument(
        "--serve-only",
        action="store_true",
        help="Skip data generation and training; start API server directly.",
    )
    parser.add_argument(
        "--records",
        type=int,
        default=8000,
        help="Number of synthetic records to generate (default: 8000).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the FastAPI server (default: 8000).",
    )
    args = parser.parse_args()

    pipeline_start = time.time()

    if not args.serve_only:
        # ---- Task 1: Generate synthetic data ----
        print("\n" + "=" * 60)
        print("  STEP 1: Generating Synthetic MPLADS Dataset")
        print("=" * 60)
        step_start = time.time()
        from src.data_generator import generate_dataset
        generate_dataset(n_records=args.records)
        step_time = time.time() - step_start
        print(f"         ⏱  Completed in {step_time:.1f}s")

        # ---- Task 2: Train XGBoost models ----
        print("\n" + "=" * 60)
        print("  STEP 2: Training XGBoost Prediction Models")
        print("=" * 60)
        step_start = time.time()
        from src.train_models import train_models
        metrics = train_models()
        step_time = time.time() - step_start
        print(f"         ⏱  Completed in {step_time:.1f}s")

        total_time = time.time() - pipeline_start

        print("\n" + "=" * 60)
        print("  PIPELINE SUMMARY")
        print("=" * 60)
        print(f"  Data: {args.records} records generated")
        print(f"  Cost Model  — RMSE: {metrics['cost_model_metrics']['rmse']:,.2f}, "
              f"MAE: {metrics['cost_model_metrics']['mae']:,.2f}, "
              f"R²: {metrics['cost_model_metrics']['r2']:.4f}")
        print(f"  Delay Model — RMSE: {metrics['delay_model_metrics']['rmse']:,.2f}, "
              f"MAE: {metrics['delay_model_metrics']['mae']:,.2f}, "
              f"R²: {metrics['delay_model_metrics']['r2']:.4f}")
        print(f"  Total time: {total_time:.1f}s")

        # Alert rules summary
        print("\n  📋 Active Alert Rules:")
        print("  ├─ TIME_WARNING    RED   → delay > 20% of expected duration")
        print("  ├─ TIME_WARNING    AMBER → delay > 10% of expected duration")
        print("  ├─ COST_ESCALATION RED   → cost overrun > 15% of sanctioned")
        print("  ├─ COST_ESCALATION AMBER → cost overrun > 5% of sanctioned")
        print("  ├─ STALLED_PROJECT RED   → progress < 40% & elapsed > 60%")
        print("  └─ ON_TRACK        GREEN → no thresholds violated")

    if not args.no_serve:
        # ---- Task 4: Start FastAPI server ----
        print("\n" + "=" * 60)
        print("  🚀 READY — Starting FastAPI Early Warning Server")
        print("=" * 60)
        print(f"  → API:      http://localhost:{args.port}")
        print(f"  → Docs:     http://localhost:{args.port}/docs")
        print(f"  → Health:   http://localhost:{args.port}/health")
        print(f"  → Endpoint: POST /api/v1/predict-early-warning")
        print("=" * 60 + "\n")

        import uvicorn
        uvicorn.run(
            "src.api:app",
            host="0.0.0.0",
            port=args.port,
            reload=False,
        )
    else:
        print("\n" + "=" * 60)
        print("  ✅ Pipeline complete!")
        print("=" * 60)
        print("  Run 'python run_pipeline.py --serve-only' to start the API.")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
