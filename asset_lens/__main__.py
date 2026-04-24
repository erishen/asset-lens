"""
Main entry point for asset-lens.
项目主入口
"""

import warnings

warnings.filterwarnings("ignore", message="Pandas requires version")
warnings.filterwarnings("ignore", message=".*unclosed.*socket.*")
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

from asset_lens.cli import cli

if __name__ == "__main__":
    cli()
