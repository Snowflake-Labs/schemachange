from __future__ import annotations

from unittest import mock

import pytest

from schemachange.config.RenderConfig import RenderConfig


@mock.patch("pathlib.Path.is_file", return_value=False)
def test_render_config_invalid_path(_):
    with pytest.raises(Exception) as e_info:
        RenderConfig.factory(script_path="invalid path")
    assert "invalid file path" in str(e_info)
