import logging
from typing import Any

from django.db.models import QuerySet
from pydantic import ValidationError

from apps.api.accounts.models import Account
from apps.api.dns.client import PowerDNSError
from apps.api.dns.models import Record, Zone
from apps.api.dns.services import PowerDNSService
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

            if zone.get('account', '') != "":
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
    try:
        zone = service.get_zone(zone_name)

        if zone.get('account', '') != "":
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
        return Zone.objects.get(name=zone_name)
    except PowerDNSError as e:
        logger.error(e)
        return Zone.objects.get(name=zone_name)

def get_records(zone_name: str):
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
        return record_instances
    except PowerDNSError as e:
        zone = get_zone(zone_name)
        Record.objects.filter(zone=zone).all()
        logger.error(e)

