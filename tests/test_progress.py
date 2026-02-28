"""
Tests for progress module.
"""

import pytest
from io import StringIO
import sys

from asset_lens.utils.progress import (
    ProgressBar,
    Spinner,
    TaskProgress,
    create_progress_bar,
)


class TestProgressBar:
    """Test ProgressBar class"""

    def test_init(self):
        """Test initialization"""
        bar = ProgressBar(total=100)
        assert bar.total == 100
        assert bar.width == 50
        assert bar.current == 0

    def test_update(self, capsys):
        """Test update"""
        bar = ProgressBar(total=100)
        bar.update(50)
        
        captured = capsys.readouterr()
        assert "50.0%" in captured.out

    def test_increment(self, capsys):
        """Test increment"""
        bar = ProgressBar(total=10)
        bar.increment()
        
        assert bar.current == 1

    def test_finish(self, capsys):
        """Test finish"""
        bar = ProgressBar(total=10)
        bar.finish("Done!")
        
        captured = capsys.readouterr()
        assert "Done!" in captured.out

    def test_custom_chars(self):
        """Test custom characters"""
        bar = ProgressBar(total=100, fill="#", empty="-")
        assert bar.fill == "#"
        assert bar.empty == "-"


class TestCreateProgressBar:
    """Test create_progress_bar function"""

    def test_create(self):
        """Test creating progress bar"""
        bar = create_progress_bar(100, "Testing")
        
        assert bar.total == 100
        assert "Testing" in bar.prefix


class TestSpinner:
    """Test Spinner class"""

    def test_init(self):
        """Test initialization"""
        spinner = Spinner("Loading")
        assert spinner.message == "Loading"
        assert spinner.current == 0

    def test_update(self, capsys):
        """Test update"""
        spinner = Spinner("Loading")
        spinner.update()
        
        assert spinner.current == 1

    def test_finish(self, capsys):
        """Test finish"""
        spinner = Spinner("Loading")
        spinner.finish("Done!")
        
        captured = capsys.readouterr()
        assert "Done!" in captured.out


class TestTaskProgress:
    """Test TaskProgress class"""

    def test_init(self):
        """Test initialization"""
        tasks = ["Task 1", "Task 2", "Task 3"]
        progress = TaskProgress(tasks)
        
        assert progress.tasks == tasks
        assert progress.current_task == 0
        assert len(progress.completed) == 0

    def test_start_task(self, capsys):
        """Test start task"""
        progress = TaskProgress(["Task 1"])
        progress.start_task("Task 1")
        
        captured = capsys.readouterr()
        assert "Task 1" in captured.out

    def test_complete_task(self, capsys):
        """Test complete task"""
        progress = TaskProgress(["Task 1"])
        progress.complete_task("Task 1", success=True)
        
        assert "Task 1" in progress.completed

    def test_complete_task_failed(self, capsys):
        """Test complete task with failure"""
        progress = TaskProgress(["Task 1"])
        progress.complete_task("Task 1", success=False)
        
        assert "Task 1" in progress.completed

    def test_summary(self, capsys):
        """Test summary"""
        progress = TaskProgress(["Task 1", "Task 2"])
        progress.completed = ["Task 1"]
        progress.summary()
        
        captured = capsys.readouterr()
        assert "1/2" in captured.out
