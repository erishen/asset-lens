"""
Tests for logger module.
"""

import logging
import tempfile
from pathlib import Path

from asset_lens.utils.logger import ColoredFormatter, SensitiveInfoFilter, get_logger, setup_logger


class TestSensitiveInfoFilter:
    """Test SensitiveInfoFilter class"""

    def test_filter_api_key(self):
        """Test filtering API key"""
        log_filter = SensitiveInfoFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="API_KEY=secret123",
            args=(),
            exc_info=None,
        )

        result = log_filter.filter(record)
        assert result is True
        assert "SENSITIVE" in record.msg

    def test_filter_password(self):
        """Test filtering password"""
        log_filter = SensitiveInfoFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="password=mypassword",
            args=(),
            exc_info=None,
        )

        result = log_filter.filter(record)
        assert result is True
        assert "SENSITIVE" in record.msg

    def test_pass_normal_message(self):
        """Test passing normal message"""
        log_filter = SensitiveInfoFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Normal log message",
            args=(),
            exc_info=None,
        )

        result = log_filter.filter(record)
        assert result is True
        assert record.msg == "Normal log message"


class TestColoredFormatter:
    """Test ColoredFormatter class"""

    def test_format_info(self):
        """Test formatting INFO level"""
        formatter = ColoredFormatter(fmt="%(levelname)s | %(message)s", datefmt="%Y-%m-%d")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        assert "INFO" in result
        assert "Test message" in result

    def test_format_error(self):
        """Test formatting ERROR level"""
        formatter = ColoredFormatter(fmt="%(levelname)s | %(message)s", datefmt="%Y-%m-%d")
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        assert "ERROR" in result
        assert "Error message" in result


class TestSetupLogger:
    """Test setup_logger function"""

    def test_setup_logger_default(self):
        """Test setup logger with default settings"""
        logger = setup_logger("test_logger_1")

        assert logger is not None
        assert logger.name == "test_logger_1"
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

    def test_setup_logger_with_file(self):
        """Test setup logger with file handler"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = setup_logger("test_logger_2", log_file=log_file, use_color=False)

            assert logger is not None
            assert log_file.exists()

    def test_setup_logger_debug_level(self):
        """Test setup logger with DEBUG level"""
        logger = setup_logger("test_logger_3", level=logging.DEBUG)

        assert logger.level == logging.DEBUG

    def test_setup_logger_no_color(self):
        """Test setup logger without color"""
        logger = setup_logger("test_logger_4", use_color=False)

        assert logger is not None


class TestGetLogger:
    """Test get_logger function"""

    def test_get_logger(self):
        """Test getting logger"""
        logger = get_logger("test_get_logger")

        assert logger is not None
        assert logger.name == "test_get_logger"

    def test_get_logger_default_name(self):
        """Test getting logger with default name"""
        logger = get_logger()

        assert logger is not None
        assert logger.name == "asset_lens"
