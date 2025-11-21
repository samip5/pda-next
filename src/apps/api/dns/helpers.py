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

    if oldRecord.name == newRecord.name and oldRecord.record_type == newRecord.record_type:
        try:
            service.update_record(zone_name, newRecord.name, newRecord.record_type, oldRecord.content, newRecord.content)
            return f"Updated {oldRecord.name} {oldRecord.record_type}"
        except PowerDNSError as e:
            logger.error(e)
            raise Exception("Unable to update record(s)")
    elif oldRecord.name != newRecord.name or oldRecord.record_type != newRecord.record_type:
        try:
            service.delete_record(zone_name, oldRecord.name, oldRecord.record_type, oldRecord.content)
        except PowerDNSError as e:
            logger.error(e)
            raise Exception("Unable to update record(s)")

        try:
            service.create_record(zone_name, newRecord.name, newRecord.record_type, newRecord.content, newRecord.ttl)
            return f"Updated {oldRecord.name} {oldRecord.record_type}"
        except PowerDNSError as e:
            logger.error(e)
            raise Exception("Unable to update record(s)")

