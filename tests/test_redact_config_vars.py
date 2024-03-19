import pytest
from schemachange.cli import redact_config_vars, SecretManager


def test_redact_config_vars_given_secret_val_should_redact_it():
    config_vars = {'secret' : 'secret_val'}
    sm = SecretManager()
    SecretManager.set_global_manager(sm)
    sm.add('secret_val')
    results = redact_config_vars(config_vars)
    redacted = {'secret' : '**********'}
    assert results == redacted


def test_redact_config_vars_given_number_like_secret_should_redact_it():
    config_vars = {'secret' : '123'}
    sm = SecretManager()
    SecretManager.set_global_manager(sm)
    sm.add('123')
    results = redact_config_vars(config_vars)
    redacted = {'secret' : '***'}
    assert results == redacted


def test_redact_config_vars_given_number_like_secret_should_redact_it_but_not_an_actual_number():
    config_vars = {'secret' : '123', 'public': 123}
    sm = SecretManager()
    SecretManager.set_global_manager(sm)
    sm.add('123')
    results = redact_config_vars(config_vars)
    redacted = {'secret' : '***', 'public': 123}
    assert results == redacted


def test_redact_config_vars_given_secret_should_redact_it_in_any_string_it_finds_it():
    config_vars = {'secrets': {'password' : 'hi'}, 'jdbc': 'jdbc:mysql://127.0.0.1;user=john;password=hi'}
    sm = SecretManager()
    SecretManager.set_global_manager(sm)
    sm.add('hi')
    results = redact_config_vars(config_vars)
    redacted = {'secrets': {'password' : '**'}, 'jdbc': 'jdbc:mysql://127.0.0.1;user=john;password=**'}
    assert results == redacted


def test_redact_config_vars_given_secret_should_redact_it_in_any_string_it_finds_it_even_in_lists():
    # At the moment, it's not documented that we could specify lists as values for variables, but,
    # nothing is preventing people from trying things. Just in case, redact_config_vars is
    # able to also redact strings inside lists. That's why this test is here.
    # Finally note that tuples are not scanned, just making the point that this redact function cannot
    # do everything; YAML deserialises lists as Python lists, not tuples, so we have no use case for tuples.
    config_vars = {'secrets': {'password' : 'hi'}, 'jdbc': 'jdbc:mysql://127.0.0.1',
                   'accounts': [{'user': 'john', 'password': '**'}], 'greetings': ['hi', 'hello'], 'greetings_tuple': ('hi',)}
    sm = SecretManager()
    SecretManager.set_global_manager(sm)
    sm.add('hi')
    results = redact_config_vars(config_vars)
    redacted = {'secrets': {'password' : '**'}, 'jdbc': 'jdbc:mysql://127.0.0.1',
                'accounts': [{'user': 'john', 'password': '**'}], 'greetings': ['**', 'hello'], 'greetings_tuple': ('hi',)}
    assert results == redacted


