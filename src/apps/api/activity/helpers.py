from jsonschema import ValidationError
from pydantic import UUID4

from apps.api.activity.models import Activity


def addActivityLog(action: str, details: str, user: UUID4, apikey: str, api: bool):
    log = Activity(
        action=action,
        details=details,
        user="",
        apikey=apikey,
        api=api,
    )
    try:
        log.full_clean()
        log.save()
    except ValidationError:
        return False
    return True
