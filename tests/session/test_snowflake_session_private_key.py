import pytest
from unittest.mock import Mock, patch

from schemachange.session.SnowflakeSession import SnowflakeSession
from schemachange.config.ChangeHistoryTable import ChangeHistoryTable


class TestSnowflakeSessionPrivateKey:
    """Test parameter delegation for private key authentication in SnowflakeSession"""

    def setup_method(self):
        """Setup for each test method"""
        self.mock_logger = Mock()
        self.change_history_table = ChangeHistoryTable()

    def test_private_key_parameter_delegation(self):
        """Test that private key parameters are correctly delegated to the connector"""
        with patch('schemachange.session.SnowflakeSession.snowflake.connector.connect') as mock_connect:
            mock_connect.return_value = Mock()
            mock_connect.return_value.session_id = "test_session"
            mock_connect.return_value.account = "test_account"
            mock_connect.return_value.user = "test_user"
            mock_connect.return_value.role = "test_role"
            mock_connect.return_value.warehouse = "test_warehouse"
            mock_connect.return_value.database = "test_database"
            mock_connect.return_value.schema = "test_schema"

            # Test parameter mapping: private_key_path -> private_key_file
            session = SnowflakeSession(
                schemachange_version="4.0.1",
                application="test",
                change_history_table=self.change_history_table,
                logger=self.mock_logger,
                private_key_path="/path/to/key.p8"
            )
            
            assert session is not None
            # Verify the parameter was correctly mapped and passed to connector
            mock_connect.assert_called_once()
            call_kwargs = mock_connect.call_args[1]
            assert call_kwargs["private_key_file"] == "/path/to/key.p8"

    def test_connector_errors_passed_through(self):
        """Test that connector errors are passed through without modification"""
        with patch('schemachange.session.SnowflakeSession.snowflake.connector.connect') as mock_connect:
            original_error = ValueError("Could not deserialize key data")
            mock_connect.side_effect = original_error
            
            with pytest.raises(ValueError) as exc_info:
                SnowflakeSession(
                    schemachange_version="4.0.1",
                    application="test",
                    change_history_table=self.change_history_table,
                    logger=self.mock_logger,
                    private_key_path="/path/to/key.p8"
                )
            
            # Should be the original connector error, unmodified
            assert exc_info.value is original_error

    def test_no_private_key_parameter_omitted(self):
        """Test that missing private key parameter is correctly omitted from connector call"""
        with patch('schemachange.session.SnowflakeSession.snowflake.connector.connect') as mock_connect:
            mock_connect.return_value = Mock()
            mock_connect.return_value.session_id = "test_session"
            mock_connect.return_value.account = "test_account"
            mock_connect.return_value.user = "test_user"
            mock_connect.return_value.role = "test_role"
            mock_connect.return_value.warehouse = "test_warehouse"
            mock_connect.return_value.database = "test_database"
            mock_connect.return_value.schema = "test_schema"

            session = SnowflakeSession(
                schemachange_version="4.0.1",
                application="test",
                change_history_table=self.change_history_table,
                logger=self.mock_logger
                # No private_key_path provided
            )
            
            assert session is not None
            # Verify private_key_file parameter was not passed to connector
            mock_connect.assert_called_once()
            call_kwargs = mock_connect.call_args[1]
            assert "private_key_file" not in call_kwargs 