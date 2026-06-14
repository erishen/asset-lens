"""
Trains the sector ML model.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from asset_lens.ml.sector_ml import sector_ml_predictor
from asset_lens.utils.logs import setup_logging

def main():
    """Main function to train the model."""
    setup_logging()
    sector_ml_predictor.train()

if __name__ == "__main__":
    main()
