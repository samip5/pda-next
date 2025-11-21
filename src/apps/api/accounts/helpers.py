from apps.api.accounts.models import Account


def updateAccount(id, name, description, contact, mail):
    account = Account.objects.filter(id=id).first()
    if name:
        account.name = name
    if description:
        account.description = description
    if contact:
        account.contact = contact
    if mail:
        account.mail = mail
    account.full_clean()
    account.save()

    return account
