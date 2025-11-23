import logging

from pydantic import ValidationError

from apps.api.dns.client import PowerDNSError
from apps.api.dns.models import Record
from apps.api.dns.services import PowerDNSService
logger = logging.getLogger('pda')


def recordUpdateHelper(zone_name: str, oldRecord: Record, newRecord: Record):
    service = PowerDNSService()

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

