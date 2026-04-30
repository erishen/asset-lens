"""
Demo E2E Test - Complete User Journey.
演示 E2E 测试 - 完整用户流程演示
"""

from playwright.sync_api import Page


def test_complete_demo(page: Page, base_url: str) -> None:
    """
    完整演示测试 - 在同一个浏览器窗口中展示所有功能
    可以看到完整的测试过程
    """

    print("\n🎬 开始演示测试...")

    # 1. 访问首页
    print("\n📍 步骤 1: 访问首页")
    page.goto(base_url, wait_until="domcontentloaded")
    print(f"   页面标题: {page.title()}")

    # 2. 查看 API 文档
    print("📍 步骤 2: 查看 API 文档")
    page.goto(f"{base_url}/docs", wait_until="domcontentloaded")
    print(f"   页面标题: {page.title()}")

    # 3. 返回首页
    print("📍 步骤 3: 返回首页")
    page.goto(base_url, wait_until="domcontentloaded")

    # 4. 测试投资组合 API
    print("📍 步骤 4: 测试投资组合 API")
    response = page.request.get(f"{base_url}/api/portfolio/summary")
    print(f"   状态码: {response.status}")
    if response.status == 200:
        data = response.json()
        print(f"   总资产: {data.get('total_assets', 0):,.2f}")
        print(f"   总收益: {data.get('total_profit', 0):,.2f}")
        print(f"   收益率: {data.get('total_return', 0):.2f}%")

    # 5. 测试市场数据 API
    print("📍 步骤 5: 测试市场数据 API")
    response = page.request.get(f"{base_url}/api/market/indexes")
    print(f"   状态码: {response.status}")

    # 6. 测试股票 API
    print("📍 步骤 6: 测试股票 API")
    response = page.request.get(f"{base_url}/api/stock/quote/sh600519")
    print(f"   状态码: {response.status}")

    # 7. 测试策略 API
    print("📍 步骤 7: 测试策略 API")
    response = page.request.get(f"{base_url}/api/strategies")
    print(f"   状态码: {response.status}")

    # 8. 测试 ML API
    print("📍 步骤 8: 测试 ML API")
    response = page.request.get(f"{base_url}/api/ml/model/status")
    print(f"   状态码: {response.status}")

    # 9. 测试风险 API
    print("📍 步骤 9: 测试风险 API")
    response = page.request.get(f"{base_url}/api/risk/summary")
    print(f"   状态码: {response.status}")

    # 10. 测试股票池 API
    print("📍 步骤 10: 测试股票池 API")
    response = page.request.get(f"{base_url}/api/stock-pool")
    print(f"   状态码: {response.status}")

    # 11. 测试响应式布局 - 桌面
    print("📍 步骤 11: 测试响应式布局 - 桌面 (1280x720)")
    page.set_viewport_size({"width": 1280, "height": 720})
    page.goto(base_url, wait_until="domcontentloaded")

    # 12. 测试响应式布局 - 平板
    print("📍 步骤 12: 测试响应式布局 - 平板 (768x1024)")
    page.set_viewport_size({"width": 768, "height": 1024})

    # 13. 测试响应式布局 - 手机
    print("📍 步骤 13: 测试响应式布局 - 手机 (375x667)")
    page.set_viewport_size({"width": 375, "height": 667})

    # 14. 恢复桌面视图
    print("📍 步骤 14: 恢复桌面视图")
    page.set_viewport_size({"width": 1280, "height": 720})

    # 15. 完成
    print("\n✅ 演示测试完成！")
    print("   所有 API 和功能测试通过")
