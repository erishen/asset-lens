"""
Tests for enhanced CLI utilities.
增强版 CLI 工具测试
"""

from unittest.mock import patch


class TestColor:
    """颜色枚举测试"""

    def test_color_values(self):
        """测试颜色枚举值"""
        from asset_lens.utils.enhanced_cli import Color

        assert Color.RED.value == "red"
        assert Color.GREEN.value == "green"
        assert Color.YELLOW.value == "yellow"
        assert Color.BLUE.value == "blue"


class TestProgressBarConfig:
    """进度条配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        from asset_lens.utils.enhanced_cli import ProgressBarConfig

        config = ProgressBarConfig()
        assert config.description == "Processing"
        assert config.total == 100
        assert config.unit == "items"
        assert config.color == "cyan"

    def test_custom_config(self):
        """测试自定义配置"""
        from asset_lens.utils.enhanced_cli import ProgressBarConfig

        config = ProgressBarConfig(description="Loading", total=1000, unit="files", color="green")
        assert config.description == "Loading"
        assert config.total == 1000
        assert config.unit == "files"
        assert config.color == "green"


class TestEnhancedCLI:
    """增强版 CLI 测试"""

    def test_init(self):
        """测试初始化"""
        from asset_lens.utils.enhanced_cli import EnhancedCLI

        cli = EnhancedCLI()
        assert cli is not None

    def test_print_colored_no_rich(self):
        """测试彩色打印（无 Rich）"""
        from asset_lens.utils.enhanced_cli import Color, EnhancedCLI

        with patch("asset_lens.utils.enhanced_cli.RICH_AVAILABLE", False):
            with patch("asset_lens.utils.enhanced_cli.CLICK_AVAILABLE", False):
                cli = EnhancedCLI()
                with patch("asset_lens.utils.enhanced_cli.logger") as mock_logger:
                    cli.print_colored("test", Color.GREEN)
                    mock_logger.info.assert_called_once_with("test")

    def test_print_success(self):
        """测试打印成功消息"""
        from asset_lens.utils.enhanced_cli import EnhancedCLI

        cli = EnhancedCLI()
        with patch.object(cli, "print_colored") as mock_print:
            cli.print_success("操作成功")
            mock_print.assert_called_once()
            args = mock_print.call_args[0]
            assert "操作成功" in args[0]

    def test_print_error(self):
        """测试打印错误消息"""
        from asset_lens.utils.enhanced_cli import EnhancedCLI

        cli = EnhancedCLI()
        with patch.object(cli, "print_colored") as mock_print:
            cli.print_error("操作失败")
            mock_print.assert_called_once()

    def test_print_warning(self):
        """测试打印警告消息"""
        from asset_lens.utils.enhanced_cli import EnhancedCLI

        cli = EnhancedCLI()
        with patch.object(cli, "print_colored") as mock_print:
            cli.print_warning("警告信息")
            mock_print.assert_called_once()

    def test_print_info(self):
        """测试打印信息消息"""
        from asset_lens.utils.enhanced_cli import EnhancedCLI

        cli = EnhancedCLI()
        with patch.object(cli, "print_colored") as mock_print:
            cli.print_info("提示信息")
            mock_print.assert_called_once()

    def test_print_header_no_rich(self):
        """测试打印标题（无 Rich）"""
        from asset_lens.utils.enhanced_cli import EnhancedCLI

        with patch("asset_lens.utils.enhanced_cli.RICH_AVAILABLE", False):
            cli = EnhancedCLI()
            with patch("asset_lens.utils.enhanced_cli.logger") as mock_logger:
                cli.print_header("测试标题")
                assert mock_logger.info.call_count >= 3

    def test_print_subheader_no_rich(self):
        """测试打印子标题（无 Rich）"""
        from asset_lens.utils.enhanced_cli import EnhancedCLI

        with patch("asset_lens.utils.enhanced_cli.RICH_AVAILABLE", False):
            cli = EnhancedCLI()
            with patch("asset_lens.utils.enhanced_cli.logger") as mock_logger:
                cli.print_subheader("子标题")
                assert mock_logger.info.call_count >= 3

    def test_print_table_no_rich(self):
        """测试打印表格（无 Rich）"""
        from asset_lens.utils.enhanced_cli import EnhancedCLI

        with patch("asset_lens.utils.enhanced_cli.RICH_AVAILABLE", False):
            cli = EnhancedCLI()
            with patch("asset_lens.utils.enhanced_cli.logger") as mock_logger:
                cli.print_table("测试表格", ["列1", "列2"], [["值1", "值2"]])
                assert mock_logger.info.call_count >= 5

    def test_print_key_value(self):
        """测试打印键值对"""
        from asset_lens.utils.enhanced_cli import EnhancedCLI

        cli = EnhancedCLI()
        with patch("asset_lens.utils.enhanced_cli.logger") as mock_logger:
            cli.print_key_value("key", "value")
            mock_logger.info.assert_called_once()

    def test_print_json(self):
        """测试打印 JSON"""
        from asset_lens.utils.enhanced_cli import EnhancedCLI

        with patch("asset_lens.utils.enhanced_cli.RICH_AVAILABLE", False):
            cli = EnhancedCLI()
            with patch("asset_lens.utils.enhanced_cli.logger") as mock_logger:
                cli.print_json({"key": "value"})
                mock_logger.info.assert_called()

    def test_create_progress_bar(self):
        """测试创建进度条"""
        from asset_lens.utils.enhanced_cli import EnhancedCLI, ProgressBarConfig

        with patch("asset_lens.utils.enhanced_cli.RICH_AVAILABLE", False):
            with patch("asset_lens.utils.enhanced_cli.TQDM_AVAILABLE", False):
                cli = EnhancedCLI()
                config = ProgressBarConfig()
                bar = cli.create_progress_bar(config)
                assert bar is not None

    def test_progress_iterator(self):
        """测试进度迭代器"""
        from asset_lens.utils.enhanced_cli import EnhancedCLI

        with patch("asset_lens.utils.enhanced_cli.RICH_AVAILABLE", False):
            with patch("asset_lens.utils.enhanced_cli.TQDM_AVAILABLE", False):
                cli = EnhancedCLI()
                items = list(cli.progress_iterator([1, 2, 3], "Processing"))
                assert items == [1, 2, 3]

    def test_confirm_no_click(self):
        """测试确认操作（无 Click）"""
        from asset_lens.utils.enhanced_cli import EnhancedCLI

        with patch("asset_lens.utils.enhanced_cli.CLICK_AVAILABLE", False):
            cli = EnhancedCLI()
            with patch("builtins.input", return_value="y"):
                result = cli.confirm("确认吗？")
                assert result is True

            with patch("builtins.input", return_value="n"):
                result = cli.confirm("确认吗？")
                assert result is False

    def test_prompt_no_click(self):
        """测试提示输入（无 Click）"""
        from asset_lens.utils.enhanced_cli import EnhancedCLI

        with patch("asset_lens.utils.enhanced_cli.CLICK_AVAILABLE", False):
            cli = EnhancedCLI()
            with patch("builtins.input", return_value="test_input"):
                result = cli.prompt("请输入")
                assert result == "test_input"

    def test_prompt_with_default(self):
        """测试提示输入（有默认值）"""
        from asset_lens.utils.enhanced_cli import EnhancedCLI

        with patch("asset_lens.utils.enhanced_cli.CLICK_AVAILABLE", False):
            cli = EnhancedCLI()
            with patch("builtins.input", return_value=""):
                result = cli.prompt("请输入", default="default_value")
                assert result == "default_value"

    def test_clear_screen_no_click(self):
        """测试清屏（无 Click）"""
        from asset_lens.utils.enhanced_cli import EnhancedCLI

        with patch("asset_lens.utils.enhanced_cli.CLICK_AVAILABLE", False):
            cli = EnhancedCLI()
            with patch("os.system") as mock_system:
                cli.clear_screen()
                mock_system.assert_called_once()


class TestSimpleProgressBar:
    """简单进度条测试"""

    def test_init(self):
        """测试初始化"""
        from asset_lens.utils.enhanced_cli import ProgressBarConfig, SimpleProgressBar

        config = ProgressBarConfig(description="Test", total=10)
        bar = SimpleProgressBar(config)
        assert bar.config == config
        assert bar.current == 0

    def test_context_manager(self):
        """测试上下文管理器"""
        from asset_lens.utils.enhanced_cli import ProgressBarConfig, SimpleProgressBar

        config = ProgressBarConfig(description="Test", total=10)
        with patch("asset_lens.utils.enhanced_cli.logger"), SimpleProgressBar(config) as bar:
            assert bar.current == 0

    def test_update(self):
        """测试更新进度"""
        from asset_lens.utils.enhanced_cli import ProgressBarConfig, SimpleProgressBar

        config = ProgressBarConfig(description="Test", total=10)
        with patch("asset_lens.utils.enhanced_cli.logger"):
            bar = SimpleProgressBar(config)
            bar.__enter__()
            bar.update(2)
            assert bar.current == 2

    def test_set_description(self):
        """测试设置描述"""
        from asset_lens.utils.enhanced_cli import ProgressBarConfig, SimpleProgressBar

        config = ProgressBarConfig(description="Test", total=10)
        bar = SimpleProgressBar(config)
        bar.set_description("New Description")
        assert bar.config.description == "New Description"


class TestGlobalInstance:
    """全局实例测试"""

    def test_enhanced_cli_instance(self):
        """测试全局实例"""
        from asset_lens.utils.enhanced_cli import enhanced_cli

        assert enhanced_cli is not None
