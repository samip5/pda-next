import logging
import uuid
from typing import Any

from django.db.models import QuerySet
from pydantic import ValidationError

from apps.api.accounts.models import Account
from apps.api.dns.client import PowerDNSError
from apps.api.dns.models import Record, Zone
from apps.api.dns.services import PowerDNSService
from apps.api.templates.models import ZoneTemplate, RecordTemplate

logger = logging.getLogger('pda')

service = PowerDNSService()

def recordUpdateHelper(zone_name: str, oldRecord: Record, newRecord: Record):

    try:
        newRecord.full_clean()
        oldRecord.full_clean()
    except ValidationError as e:
        logger.error(e)
        raise Exception("Invalid record(s)")

    new_record_name = newRecord.name
    if newRecord.name == "@":
        new_record_name = zone_name
    old_record_name = oldRecord.name
    if oldRecord.name == "@":
        old_record_name = zone_name

    if oldRecord.name == newRecord.name and oldRecord.record_type == newRecord.record_type:
        try:
            service.update_record(zone_name, old_record_name, newRecord.record_type, oldRecord.content, newRecord.content, ttl=newRecord.ttl)
            return f"Updated {old_record_name} {oldRecord.record_type}"
        except PowerDNSError as e:
            logger.error(e)
            raise Exception("Unable to update record(s)")
    elif oldRecord.name != newRecord.name or oldRecord.record_type != newRecord.record_type:
        try:
            service.delete_record(zone_name, old_record_name, oldRecord.record_type, oldRecord.content)
        except PowerDNSError as e:
            logger.error(e)
            raise Exception("Unable to update record(s)")

        try:
            service.create_record(zone_name, new_record_name, newRecord.record_type, newRecord.content, newRecord.ttl)
            return f"Updated {old_record_name} {oldRecord.record_type}"
        except PowerDNSError as e:
            logger.error(e)
            raise Exception("Unable to update record(s)")
    return Exception("Unable to update record(s)")


zone_account = None

def get_zones() -> list[Any] | QuerySet[Zone, Zone]:
    try:
        powerdns_zones = service.get_zones("localhost")
        for zone in powerdns_zones:
            zone_account = None
            zone['nameservers'] = ["ns1.fuckmylife.fi"]

            if zone.get('nameservers') == '':
                zone['nameservers'] = ["ns1.kapsi.fi"]

            if _is_valid_uuid(zone.get('account', '')):
                zone_account = Account.objects.filter(id=zone.get('account')).first()

            zone = Zone(
              name=zone.get('name', ''),
              kind=zone.get('kind', Zone.ZONE_KIND_NATIVE),
              nameservers=zone.get('nameservers', []),
              server_id=zone.get('server_id', 'localhost'),
              powerdns_id=zone.get('id'),
              account=zone_account,
              dnssec=zone.get('dnssec', '')
            )

            cache_zone = Zone.objects.filter(name=zone.name).first()
            if not cache_zone:
                zone.full_clean()
                zone.save()
            elif cache_zone:
                Zone.objects.filter(name=zone.name).update(kind=zone.kind, nameservers=zone.nameservers,
                                                           server_id=zone.server_id, account=zone.account,
                                                           dnssec=zone.dnssec)

        return Zone.objects.all()
    except PowerDNSError as e:
        logger.error(e)
        return Zone.objects.all()

def get_zone(zone_name: str) -> Zone:
    if not zone_name.endswith('.'):
        zone_name = f"{zone_name}."

    try:
        zone = service.get_zone(zone_name)

        if _is_valid_uuid(zone.get('account', '')):
           zone_account = Account.objects.filter(id=zone.get('account')).first()

        zone = Zone(
            name=zone.get('name', ''),
            kind=zone.get('kind', Zone.ZONE_KIND_NATIVE),
            nameservers=["ns1.fuckmylife.fi"],
            server_id=zone.get('server_id', 'localhost'),
            powerdns_id=zone.get('id'),
            account=zone_account,
            dnssec=zone.get('dnssec', '')
        )

        cache_zone = Zone.objects.filter(name=zone.name).first()
        if not cache_zone:
            zone.full_clean()
            zone.save()
        elif cache_zone:
            Zone.objects.filter(name=zone.name).update(kind=zone.kind, nameservers=zone.nameservers,
                                                       server_id=zone.server_id, account=zone.account,
                                                       dnssec=zone.dnssec)
        return Zone.objects.get(name=zone_name)
    except PowerDNSError as e:
        logger.error(e)
        return Zone.objects.get(name=zone_name)

def get_records(zone_name: str) -> QuerySet[Record, Record] | None:
    try:
        zone = get_zone(zone_name)
        records = service.get_records(zone_name, zone.server_id)
        record_instances = []
        for rrset in records:
            rrset_name = rrset.get('name', '')
            rrset_type = rrset.get('type', '')
            rrset_ttl = rrset.get('ttl', 3600)

            for record_data in rrset.get('records', []):
                content = record_data.get('content', '')
                disabled = record_data.get('disabled', False)

                # Normalize name (remove zone suffix if present)
                normalized_name = rrset_name
                if normalized_name.endswith('.'):
                    normalized_name = normalized_name.rstrip('.')
                zone_name_clean = zone_name.rstrip('.')
                if normalized_name == zone_name_clean:
                    normalized_name = '@'
                elif normalized_name.endswith(f".{zone_name_clean}"):
                    normalized_name = normalized_name[:-len(f".{zone_name_clean}")]

                record = Record(
                    zone=zone,
                    name=normalized_name,
                    record_type=rrset_type,
                    content=content,
                    ttl=rrset_ttl,
                    disabled=disabled,
                )
                cache_record = Record.objects.filter(name=normalized_name, zone=zone, content=content).first()
                if not cache_record:
                    record.full_clean()
                    record.save()
                elif cache_record:
                    Record.objects.filter(name=normalized_name, zone=zone, content=content).update(content=record.content,
                                                               ttl=record.ttl, disabled=record.disabled)
                record_instances.append(record)
        return Record.objects.filter(zone=zone).all()
    except PowerDNSError as e:
        zone = get_zone(zone_name)
        Record.objects.filter(zone=zone).all()
        logger.error(e)

def _is_valid_uuid(value):
    try:
        uuid_obj = uuid.UUID(str(value))
        return True
    except ValueError:
        return False

def delete_record(zone_name: str, record: Record):
    try:
        zone = get_zone(zone_name)
        records = get_records(zone_name=zone.name)
        crecord = records.filter(name=record.name,content=record.content, record_type=record.record_type).first()
        record_name = str(crecord.name).replace("@", zone.name)
        crecord.delete()
        service.delete_record(zone.name, record_name, crecord.record_type, crecord.content)
        return True
    except PowerDNSError as e:
        logger.error(e)
        return False


def delete_zone(zone_name: str):
    try:
        zone = get_zone(zone_name)
        zone.delete()
        service.delete_zone(zone.name)
        return True
    except PowerDNSError as e:
        logger.error(e)
        return False


def create_zone_from_template(zone: Zone, template: ZoneTemplate = None):
    template = ZoneTemplate.objects.filter(id=template).first()
    if not zone.name.endswith('.'):
        zone.name = f"{zone.name}."

    try:
        if template is not None:
            resp = service.create_zone(zone_name=zone.name, kind=template.kind, account=str(zone.account.id),
                            nameservers=['ns1.fuckmylife.fi.'])
        else:
            resp = service.create_zone(zone_name=zone.name, kind=zone.kind, account=str(zone.account.id),
                            nameservers=['ns1.example.com.'])

        if resp is not PowerDNSError and template is not None:
            zone = get_zone(zone.name)
            template_records = RecordTemplate.objects.filter(zone_template=template)
            logger.info(template_records)
            for record in template_records:
                logger.info(record.name)
                record_name = str(record.name).replace("@", zone.name)
                record_content = record.content.replace("@", zone.name)
                if record.record_type == "TXT" and not record_content.startswith('"') and not record_content.endswith('"'):
                    record_content = f'"{record_content}"'
                create_record(zone, record_name, record.record_type, record_content, record.ttl)

    except Exception as e:
        logger.error(e)
    return


def create_record(zone: Zone, name: str, record_type: str, content: str, ttl: int=3600, disabled: bool=False):
    record = Record(
        zone=zone,
        name=name,
        record_type=record_type,
        content=content,
        ttl=ttl,
        disabled=disabled
    )
    logger.info(content)

    try:
        record.full_clean()
        record.save()
        service.create_record(zone.name, name, record_type, content, ttl)
    except ValidationError as e:
        logger.error(e)