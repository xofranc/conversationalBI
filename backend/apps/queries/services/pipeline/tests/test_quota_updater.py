# apps/queries/services/pipeline/tests/test_quota_updater.py
import pytest
from unittest.mock import Mock, patch

from ..quota_updater import QuotaUpdater


@pytest.mark.django_db
def test_quota_updater():
    middleware = QuotaUpdater()
    
    with patch('apps.queries.services.pipeline.quota_updater.UserService.increment_usage') as mock_increment:
        context = {'user': Mock()}
        result = middleware.process(context)
        
        mock_increment.assert_called_once_with(context['user'])
        assert result == context
