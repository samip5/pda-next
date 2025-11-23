from jsonschema import ValidationError

from apps.api.activity.models import Activity


def addActivityLog(action: str, details: str, user: int, apikey: str, api: bool):
    log = Activity(
        action=action,
        details=details,
        user=str(user),
        apikey=apikey,
        api=api,
    )
    try:
        log.full_clean()
        log.save()
    except ValidationError:
        return False
    return True
