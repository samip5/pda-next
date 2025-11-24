from jsonschema import ValidationError

from apps.api.activity.models import Activity
from apps.api.activity.models.activity import ActionType
from apps.users.models import CustomUser


def addActivityLog(action: ActionType, details: str, user: CustomUser, apikey: str = '', api: bool = False):
    log = Activity(
        action=action,
        details=details,
        user=user,
        apikey=apikey,
        api=api,
    )
    try:
        log.full_clean()
        log.save()
    except ValidationError:
        return False
    return True
