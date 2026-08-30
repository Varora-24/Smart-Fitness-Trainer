import pytest
from unittest.mock import MagicMock, patch
import core.data.db as db

def test_check_upload_limit_allowed():
    """Verify check_upload_limit allows upload when count < limit."""
    mock_client = MagicMock()
    mock_res = MagicMock()
    mock_res.count = 2  # 2 uploads in last hour
    
    # Mocking client.table("upload_logs").select(...).eq(...).gte(...).execute()
    mock_client.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value = mock_res
    
    with patch("core.data.db._get_client", return_value=mock_client):
        allowed, reason = db.check_upload_limit("test_user_id", limit=5)
        assert allowed is True
        assert reason == ""

def test_check_upload_limit_exceeded():
    """Verify check_upload_limit rejects upload when count >= limit."""
    mock_client = MagicMock()
    mock_res = MagicMock()
    mock_res.count = 5  # 5 uploads in last hour (limit is 5)
    
    mock_client.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value = mock_res
    
    with patch("core.data.db._get_client", return_value=mock_client):
        allowed, reason = db.check_upload_limit("test_user_id", limit=5)
        assert allowed is False
        assert reason == "limit_exceeded"

def test_check_upload_limit_db_error():
    """Verify check_upload_limit fail-safes securely if DB throws exception."""
    mock_client = MagicMock()
    
    mock_client.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.side_effect = Exception("DB Timeout")
    
    with patch("core.data.db._get_client", return_value=mock_client):
        allowed, reason = db.check_upload_limit("test_user_id", limit=5)
        assert allowed is False  # Must fail-safe securely!
        assert reason == "db_error"
