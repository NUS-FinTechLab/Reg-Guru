"""
Run all ingestion pipelines for different regions.
This script orchestrates the execution of FinCEN (US) and SSO (Singapore) pipelines.
"""

import sys
import os
from datetime import datetime

# Add the parent directories to the Python path to resolve imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..')
sys.path.insert(0, src_dir)

# Import pipeline classes
from us.fincen.pipeline import FincenPipeline
from sg.sso.pipeline import SsoPipeline

def run_pipeline(pipeline_class, name):
    """Run a single pipeline with error handling."""
    print(f"\n{'='*60}")
    print(f"STARTING {name} PIPELINE")
    print('='*60)
    start_time = datetime.now()
    
    try:
        pipeline = pipeline_class()
        pipeline.run()
        duration = datetime.now() - start_time
        print(f"\n✅ {name} pipeline completed successfully in {duration}")
        return True
    except Exception as e:
        duration = datetime.now() - start_time
        print(f"\n❌ {name} pipeline failed after {duration}")
        print(f"Error: {str(e)}")
        return False

def main():
    """Run all pipelines."""
    print("STARTING DATA INGESTION PIPELINES")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    total_start_time = datetime.now()
    
    # Run both pipelines
    fincen_success = run_pipeline(FincenPipeline, "FINCEN (US)")
    sso_success = run_pipeline(SsoPipeline, "SSO (SINGAPORE)")
    
    # Print summary
    total_duration = datetime.now() - total_start_time
    successful = sum([fincen_success, sso_success])
    
    print(f"\n{'='*60}")
    print("📊 PIPELINE EXECUTION SUMMARY")
    print('='*60)
    print(f"FINCEN: {'✅ SUCCESS' if fincen_success else '❌ FAILED'}")
    print(f"SSO: {'✅ SUCCESS' if sso_success else '❌ FAILED'}")
    print(f"\nTotal execution time: {total_duration}")
    print(f"Successful pipelines: {successful}/2")
    
    if successful == 2:
        print("🎉 All pipelines completed successfully!")
    
    return successful == 2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)