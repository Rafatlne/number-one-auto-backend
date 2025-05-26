from io import StringIO
import pytest

from django.core.management import call_command


@pytest.mark.django_db
def test_printurls():
    out = StringIO()
    call_command("printurls", stdout=out)
    assert "api-root" in out.getvalue()
