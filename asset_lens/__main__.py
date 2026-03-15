"""
Main entry point for asset-lens.
项目主入口
"""

from asset_lens.cli import create_cli

cli = create_cli()

if __name__ == "__main__":
    cli()
