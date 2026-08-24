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
        default=5000,
        help="Number of synthetic records to generate (default: 5000).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the FastAPI server (default: 8000).",
    )
    args = parser.parse_args()

    if not args.serve_only:
        # ---- Task 1: Generate synthetic data ----
        print("\n" + "=" * 60)
        print("  STEP 1: Generating Synthetic MPLADS Dataset")
        print("=" * 60)
        from src.data_generator import generate_dataset
        generate_dataset(n_records=args.records)

        # ---- Task 2: Train XGBoost models ----
        print("\n" + "=" * 60)
        print("  STEP 2: Training XGBoost Prediction Models")
        print("=" * 60)
        from src.train_models import train_models
        metrics = train_models()

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

    if not args.no_serve:
        # ---- Task 4: Start FastAPI server ----
        print("\n" + "=" * 60)
        print("  STEP 3: Starting FastAPI Early Warning Server")
        print("=" * 60)
        print(f"  → http://localhost:{args.port}")
        print(f"  → Docs: http://localhost:{args.port}/docs")
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
        print("\n✅ Pipeline complete. Run 'python run_pipeline.py --serve-only' to start the API.")


if __name__ == "__main__":
    main()
