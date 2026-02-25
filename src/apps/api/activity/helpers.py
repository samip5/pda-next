from jsonschema import ValidationError

from apps.api.activity.models import Activity
from apps.api.activity.models.activity import ActionType
from apps.users.models import CustomUser


def addActivityLog(action: ActionType, info:str, details: str, user: CustomUser, apikey: str = '', api: bool = False):
    log = Activity(
        action=action,
        details=details,
        info=info,
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


def getMemberDetails(new_members: set, old_members: set = None,) -> str:
    parts = []
    if old_members is None:
        if new_members:
            users = CustomUser.objects.filter(id__in=new_members).values_list("username", flat=True)
            parts.append("Members:\n" + ", ".join(users))
    else:
        added = new_members - old_members
        removed = old_members - new_members
        if added:
            added_users = CustomUser.objects.filter(id__in=added).values_list("username", flat=True)
            parts.append("Added members:\n" + ", ".join(added_users))
        if removed:
            removed_users = CustomUser.objects.filter(id__in=removed).values_list("username", flat=True)
            parts.append("Removed members:\n" + ", ".join(removed_users))
    return "\n".join(parts)

def getFieldDetails(new_fields: dict, old_fields: dict = None) -> str:
    parts = []
    for field, new_value in new_fields.items():
        if old_fields is not None:
            old_value = old_fields.get(field)
            if old_value != new_value:
                parts.append(f"{field.capitalize()}: {old_value} → {new_value}")
        else:
            parts.append(f"{field.capitalize()}: {new_value}")
    return "\n".join(parts)



def getSingleUserDetails(field_name, new_user_id, old_user_id = None) -> str:
    if old_user_id is not None:
        if old_user_id == new_user_id:
            return ""
        old_display = CustomUser.objects.filter(id=old_user_id).first()
        new_display = CustomUser.objects.filter(id=new_user_id).first()
        return f"{field_name}: {old_display} → {new_display}"
    else:
        new_display = CustomUser.objects.filter(id=new_user_id).first()
        return f"{field_name}: {new_display}"


def mergeActivityDetails(*args) -> str:
    return "\n".join(filter(None, args))




# new_members = set(account_instance.members.values_list("id", flat=True))
# new_fields = {
#     "name": account_instance.name,
#     "mail": account_instance.mail,
#     "contact": account_instance.contact,
#     "description": account_instance.description
# }
# new_owner = account_instance.owner
#
# details = mergeActivityDetails(
#     getFieldChangeDetails(old_fields, new_fields),
#     getSingleUserChangeDetails(old_owner.id, new_owner.id, "owner"),
#     getMemberChangeDetails(old_members, new_members))
# addActivityLog(ActionType.ACCOUNT_UPDATE, f"{id}", details, request.user)