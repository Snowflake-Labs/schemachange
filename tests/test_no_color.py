# Copyright 2025 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path


class TestNoColor:
    def test_no_color_env_var_disables_colors(self):
        """Test that setting NO_COLOR=1 disables colored output."""
        test_script = """
import schemachange
import structlog
logger = structlog.getLogger()
logger.info("Test message", key="value")
"""

        result_with_colors = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
            env={k: v for k, v in os.environ.items() if k != "NO_COLOR"},
            cwd=Path(__file__).parent.parent,
        )

        result_without_colors = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
            env={**os.environ, "NO_COLOR": "1"},
            cwd=Path(__file__).parent.parent,
        )

        assert result_with_colors.returncode == 0
        assert result_without_colors.returncode == 0

        output_with_colors = result_with_colors.stderr + result_with_colors.stdout
        output_without_colors = result_without_colors.stderr + result_without_colors.stdout

        assert "Test message" in output_with_colors
        assert "Test message" in output_without_colors

        # On Windows, ANSI color codes might not be present by default
        # So we only verify that NO_COLOR prevents them if they would otherwise be present
        is_windows = platform.system() == "Windows"
        has_ansi_with_colors = "\x1b[" in output_with_colors

        if not is_windows:
            # On Unix-like systems, ANSI codes should be present
            assert has_ansi_with_colors, "ANSI escape codes should be present on Unix-like systems"

        # Verify ANSI escape codes are absent when NO_COLOR is set
        # This should work on all platforms
        assert "\x1b[" not in output_without_colors, "NO_COLOR should disable ANSI escape codes"

    def test_no_color_env_var_with_schemachange_import(self):
        """Test that NO_COLOR works when importing schemachange module."""
        test_script = """
import schemachange
import structlog
logger = structlog.getLogger()
logger.info("Schemachange test", foo="bar")
"""

        result_with_colors = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
            env={k: v for k, v in os.environ.items() if k != "NO_COLOR"},
            cwd=Path(__file__).parent.parent,
        )

        result_without_colors = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
            env={**os.environ, "NO_COLOR": "1"},
            cwd=Path(__file__).parent.parent,
        )

        assert result_with_colors.returncode == 0
        assert result_without_colors.returncode == 0

        output_with_colors = result_with_colors.stderr + result_with_colors.stdout
        output_without_colors = result_without_colors.stderr + result_without_colors.stdout

        assert "Schemachange test" in output_with_colors
        assert "Schemachange test" in output_without_colors

        # On Windows, ANSI color codes might not be present by default
        # So we only verify that NO_COLOR prevents them if they would otherwise be present
        is_windows = platform.system() == "Windows"
        has_ansi_with_colors = "\x1b[" in output_with_colors

        if not is_windows:
            # On Unix-like systems, ANSI codes should be present
            assert has_ansi_with_colors, "ANSI escape codes should be present on Unix-like systems"

        # Verify ANSI escape codes are absent when NO_COLOR is set
        # This should work on all platforms
        assert "\x1b[" not in output_without_colors, "NO_COLOR should disable ANSI escape codes"
