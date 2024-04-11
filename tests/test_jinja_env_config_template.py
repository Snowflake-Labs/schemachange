from jinja2 import DictLoader
from schemachange.cli import JinjaTemplateProcessor, _jinja_env_defaults


def test_jinja_environment_variables_set():
    jinja_env_args = {"trim_blocks": True,
                      "lstrip_blocks": True,
                      "block_start_string": "<%",
                      "block_end_string": "%>",
                      "variable_start_string": "[[",
                      "variable_end_string": "]]"}
    processor = JinjaTemplateProcessor("", None, jinja_env_args)
    templates = {"test.sql": """<% for item in items %>[[ item ]] <% endfor %>"""}
    expected_env_args = set(jinja_env_args.keys()) | _jinja_env_defaults
    unexpected_env_args = expected_env_args ^ set(processor._env_args.keys())
    # Ensure all Jinja environment variables are set including the defaults
    assert len(unexpected_env_args) == 0, f"Unexpected jinja environment variables set: {unexpected_env_args}"
    processor.override_loader(DictLoader(templates))
    # Test that Jinja environment variables are taking effect
    result = processor.render("test.sql", {"items": ['a', 'b', 'c']}, True)
    assert result == 'a b c', f"Unexpected result: {result}"