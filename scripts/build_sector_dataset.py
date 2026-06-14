"""
Builds the dataset for the sector ML model.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from asset_lens.ml.sector_data_builder import SectorDataBuilder
from asset_lens.utils.logs import setup_logging

def main():
    """Main function to build the dataset."""
    setup_logging()
    # Build dataset for the last 2 years
    end_date = "2024-06-01"
    start_date = "2022-06-01"
    
    builder = SectorDataBuilder(start_date=start_date, end_date=end_date)
    builder.build_dataset()

if __name__ == "__main__":
    main()
