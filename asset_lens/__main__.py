"""
Main entry point for asset-lens.
项目主入口
"""

from asset_lens.utils.warnings_config import suppress_common_warnings

suppress_common_warnings()

from asset_lens.cli import cli

if __name__ == "__main__":
    cli()
