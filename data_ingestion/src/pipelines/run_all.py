"""Run the available ingestion pipelines sequentially."""

import sys
from datetime import datetime
from pathlib import Path

# Ensure the repository root and src package are importable when run as a script.
SRC_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = SRC_ROOT.parent
for path in (REPO_ROOT, SRC_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from src.us.fincen.pipeline import FincenPipeline
from src.sg.sso.pipeline import SsoPipeline
from src.eu.history.pipeline import EUHistoryPipeline
from src.eu.feed.pipeline import EUFeedPipeline


def run_pipeline(pipeline_class, name, test_mode):
    """Run a single pipeline with error handling."""
    print(f"\n{'='*60}")
    print(f"{datetime.now().isoformat(sep=' ', timespec="seconds")} STARTING {name} PIPELINE")
    print("=" * 60)
    start_time = datetime.now()

    try:
        pipeline = pipeline_class(test_mode=test_mode)
        pipeline.run()
        duration = datetime.now() - start_time
        print(f"\n✅ {name} pipeline completed successfully in {int(duration.total_seconds())}s")
        return True
    except Exception as e:
        duration = datetime.now() - start_time
        print(f"\n❌ {name} pipeline failed after {int(duration.total_seconds())}s")
        print(f"Unexpected Error:", e)
        return False


def main(history=False, test_mode=False):

    historical_pipelines = [
        (EUHistoryPipeline, "EURLEX HISTORY (EU)")
    ]
    pipelines = [
        (FincenPipeline, "FINCEN (US)"),
        (SsoPipeline, "SSO (SG)"),
        (EUFeedPipeline, "EURLEX FEED (EU)")
    ]
    results = []

    """Run all pipelines."""
    print("STARTING DATA INGESTION PIPELINES")
    print(f"Timestamp: {datetime.now().isoformat(sep=' ', timespec="seconds")}")
    total_start_time = datetime.now()
    
    # Run history pipelines if required
    if history:
        for class_, name in historical_pipelines:
            success = run_pipeline(class_, name, test_mode)
            results.append((name, success))

    # Run pipelines
    for class_, name in pipelines:
        success = run_pipeline(class_, name, test_mode)
        results.append((name, success))

    # Print summary
    total_duration = datetime.now() - total_start_time
    successful = sum(1 for _, success in results if success)
    print(f"\n{'='*60}")
    print("📊 PIPELINE EXECUTION SUMMARY")
    print("=" * 60)
    for name, success in results:
        status = '✅ SUCCESS' if success else '❌ FAILED'
        print(f"{name}: {status}")

    print(f"Total execution time: {int(total_duration.total_seconds())}s")
    print(f"Number of successful pipelines: {successful}/{len(results)}")

    if successful == len(results):
        print("🎉 All pipelines completed successfully!")

    return successful == len(results)


if __name__ == "__main__":
    success = main(history=False, test_mode=True)
    print(success)
    # sys.exit(0 if success else 1)
