#!/usr/bin/env python3
"""
Demo 模式启动脚本
设置 demo_mode=True 并启动 uvicorn Web 服务器

使用方法:
    python scripts/start_demo.py [--port 8000] [--host 0.0.0.0]
"""

import argparse
import os
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Asset Lens Demo 模式启动器")
    parser.add_argument("--port", type=int, default=8000, help="服务端口 (默认: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="监听地址 (默认: 0.0.0.0)")
    parser.add_argument("--reload", action="store_true", help="启用热重载 (仅开发环境)")
    args = parser.parse_args()

    # 设置 Demo 模式环境变量
    os.environ["ASSET_LENS_DEMO_MODE"] = "true"
    os.environ["ASSET_LENS_DATA_MODE"] = "sample"
    os.environ["CORS_ORIGINS"] = "*"

    # 确保项目根目录在 sys.path 中
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # 生成模拟数据
    print("🎭 正在准备 Demo 模式...")
    try:
        from scripts.seed_demo import generate_demo_csv

        data_dir = project_root / "data" / "sample_data"
        generate_demo_csv(data_dir)
        print("✅ 模拟数据生成完成")
    except Exception as e:
        print(f"⚠️ 模拟数据生成失败: {e}，将使用已有数据")

    # 启动 uvicorn
    print(f"🚀 启动 Asset Lens Demo 服务器: http://{args.host}:{args.port}")
    print(f"📊 访问 Dashboard: http://localhost:{args.port}")
    print(f"📖 API 文档: http://localhost:{args.port}/docs")
    print("按 Ctrl+C 停止服务\n")

    try:
        import uvicorn

        uvicorn.run(
            "asset_lens.web.api:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info",
        )
    except ImportError:
        print("❌ 未安装 uvicorn，请运行: pip install uvicorn")
        sys.exit(1)


if __name__ == "__main__":
    main()
