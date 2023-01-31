from schemachange.cli import SecretManager


##### test Class #####
def test_SecretManager_given_no_secrets_when_redact_then_return_original_value():
    sm = SecretManager()
    result = sm.redact("My string")
    assert result == "My string"


def test_SecretManager_given_secrets_when_redact_on_none_then_return_none():
    sm = SecretManager()
    sm.add("world")
    result = sm.redact(None)
    assert result is None


def test_SecretManager_given_secrets_when_redact_then_return_redacted_value():
    sm = SecretManager()
    sm.add("world")
    result = sm.redact("Hello world!")
    assert result == "Hello *****!"


def test_SecretManager_given_secrets_when_clear_then_should_hold_zero_secrets():
    sm = SecretManager()
    sm.add("world")
    sm.add("Hello")

    # check private variable
    assert len(sm._SecretManager__secrets) == 2

    sm.clear()

    # check private variable
    assert len(sm._SecretManager__secrets) == 0


def test_SecretManager_given_one_secrets_when_add_range_with_None_then_Count_should_remain_one():
    sm = SecretManager()
    sm.add("world")
    sm.add_range(None)

    assert len(sm._SecretManager__secrets) == 1

def test_SecretManager_given_one_secrets_when_add_range_with_empty_set_then_Count_should_remain_one():
    sm = SecretManager()
    sm.add("world")

    range = set()
    sm.add_range(range)

    assert len(sm._SecretManager__secrets) == 1

def test_SecretManager_given_one_secrets_when_add_range_with_two_secrets_then_count_of_secrets_three():
    sm = SecretManager()
    sm.add("world")

    range = {"one", "two"}
    sm.add_range(range)

    # check private variable
    assert len(sm._SecretManager__secrets) == 3
    assert "world" in sm._SecretManager__secrets
    assert "one" in sm._SecretManager__secrets
    assert "two" in sm._SecretManager__secrets


##### test static methods #####

def test_SecretManager_check_global_assignment_round_trip():
    sm = SecretManager()

    SecretManager.set_global_manager(sm)
    assert SecretManager.get_global_manager() is sm


def test_SecretManager_global_redact():
    sm = SecretManager()
    sm.add("Hello")
    SecretManager.set_global_manager(sm)

    assert SecretManager.global_redact("Hello World!") == "***** World!"