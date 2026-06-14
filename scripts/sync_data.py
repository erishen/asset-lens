#!/usr/bin/env python3
"""
同步 ts-demo 真实数据到 asset-lens

用法:
    python scripts/sync_data.py              # 同步所有数据
    python scripts/sync_data.py --latest     # 只同步最新数据
    python scripts/sync_data.py --dry-run    # 预览同步内容，不实际执行
"""

import argparse
import filecmp
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """获取项目根目录"""
    script_dir = Path(__file__).resolve().parent
    return script_dir.parent


def get_ts_demo_root() -> Path:
    """获取 ts-demo 项目根目录"""
    project_root = get_project_root()
    return project_root.parent / "ts-demo"


def get_source_dirs(ts_demo_root: Path) -> list[Path]:
    """获取 ts-demo 中的所有数据目录"""
    data_dir = ts_demo_root / "data"
    if not data_dir.exists():
        return []

    source_dirs = [item for item in data_dir.iterdir() if item.is_dir() and item.name.startswith("money_csv_")]

    return sorted(source_dirs)


def sync_directory(source: Path, target: Path, dry_run: bool = False) -> dict:
    """
    同步单个目录

    Args:
        source: 源目录
        target: 目标目录
        dry_run: 是否只预览不执行

    Returns:
        同步结果统计
    """
    result = {
        "source": source.name,
        "status": "skip",
        "files_added": 0,
        "files_updated": 0,
        "files_unchanged": 0,
    }

    if not source.exists():
        result["status"] = "error"
        result["error"] = "源目录不存在"
        return result

    if dry_run:
        if target.exists():
            result["status"] = "update"
            for src_file in source.iterdir():
                if src_file.is_file():
                    tgt_file = target / src_file.name
                    if not tgt_file.exists():
                        result["files_added"] += 1
                    elif not filecmp.cmp(src_file, tgt_file, shallow=False):
                        result["files_updated"] += 1
                    else:
                        result["files_unchanged"] += 1
        else:
            result["status"] = "new"
            result["files_added"] = len([f for f in source.iterdir() if f.is_file()])
    else:
        if target.exists():
            result["status"] = "update"
            for src_file in source.iterdir():
                if src_file.is_file():
                    tgt_file = target / src_file.name
                    if not tgt_file.exists():
                        shutil.copy2(src_file, tgt_file)
                        result["files_added"] += 1
                    elif not filecmp.cmp(src_file, tgt_file, shallow=False):
                        shutil.copy2(src_file, tgt_file)
                        result["files_updated"] += 1
                    else:
                        result["files_unchanged"] += 1
        else:
            shutil.copytree(source, target)
            result["status"] = "new"
            result["files_added"] = len([f for f in source.iterdir() if f.is_file()])

    return result


def sync_all_data(dry_run: bool = False, latest_only: bool = False) -> list[dict]:
    """
    同步所有数据

    Args:
        dry_run: 是否只预览不执行
        latest_only: 是否只同步最新数据

    Returns:
        同步结果列表
    """
    project_root = get_project_root()
    ts_demo_root = get_ts_demo_root()
    target_base = project_root / "data" / "real"

    if not ts_demo_root.exists():
        logger.error("ts-demo 项目不存在: %s", ts_demo_root)
        return []

    source_dirs = get_source_dirs(ts_demo_root)

    if not source_dirs:
        logger.error("未找到任何数据目录")
        return []

    if latest_only:
        source_dirs = [source_dirs[-1]]

    results = []

    for source_dir in source_dirs:
        target_dir = target_base / source_dir.name
        result = sync_directory(source_dir, target_dir, dry_run)
        results.append(result)

    return results


def print_results(results: list[dict], dry_run: bool = False):
    """打印同步结果"""
    if not results:
        return

    action = "预览" if dry_run else "同步"
    print(f"\n{'='*60}")
    print(f"📊 数据{action}结果")
    print(f"{'='*60}\n")

    total_added = 0
    total_updated = 0
    total_unchanged = 0

    for result in results:
        status_icon = {
            "new": "🆕",
            "update": "📝",
            "skip": "⏭️",
            "error": "❌",
        }.get(result["status"], "❓")

        status_text = {
            "new": "新建",
            "update": "更新",
            "skip": "跳过",
            "error": "错误",
        }.get(result["status"], "未知")

        print(f"{status_icon} {result['source']}: {status_text}")

        if result["status"] in ["new", "update"]:
            if result["files_added"]:
                print(f"   ➕ 新增文件: {result['files_added']}")
            if result["files_updated"]:
                print(f"   📝 更新文件: {result['files_updated']}")
            if result["files_unchanged"]:
                print(f"   ✅ 未变化: {result['files_unchanged']}")
            total_added += result["files_added"]
            total_updated += result["files_updated"]
            total_unchanged += result["files_unchanged"]

        if "error" in result:
            print(f"   ❌ 错误: {result['error']}")

    print(f"\n{'-'*60}")
    print(f"📈 汇总: 新增 {total_added} | 更新 {total_updated} | 未变化 {total_unchanged}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="同步 ts-demo 真实数据到 asset-lens",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python scripts/sync_data.py              # 同步所有数据
    python scripts/sync_data.py --latest     # 只同步最新数据
    python scripts/sync_data.py --dry-run    # 预览同步内容
        """,
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="只同步最新数据",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览同步内容，不实际执行",
    )

    args = parser.parse_args()

    print(f"\n🔄 开始{'预览' if args.dry_run else '同步'}数据...")

    results = sync_all_data(dry_run=args.dry_run, latest_only=args.latest)

    print_results(results, dry_run=args.dry_run)

    if results and not args.dry_run:
        print("✅ 数据同步完成！")


if __name__ == "__main__":
    main()
