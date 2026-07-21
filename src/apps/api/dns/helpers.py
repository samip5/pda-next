import logging
import uuid
import ipaddress
import re
from typing import Any, Dict, List

from django.db.models import QuerySet
from pydantic import ValidationError

from apps.api.accounts.models import Account
from apps.api.dns.client import PowerDNSError
from apps.api.dns.models import Record, Zone, record
from apps.api.dns.services import PowerDNSService
from apps.api.templates.models import ZoneTemplate, RecordTemplate
from django.core.exceptions import ValidationError
logger = logging.getLogger('pda')

service = PowerDNSService()

def recordUpdateHelper(zone_name: str, oldRecord: Record, newRecord: Record):

    # try:
    #     newRecord.full_clean()
    #     oldRecord.full_clean()
    # except ValidationError as e:
    #     logger.error(e)
    #     raise Exception("Invalid record(s)")

    new_record_name = str(newRecord.name).replace("@", zone_name)
    old_record_name = str(oldRecord.name).replace("@", zone_name)
    zone = get_zone(zone_name)
    if oldRecord.name == newRecord.name and oldRecord.record_type == newRecord.record_type:
        try:
            cache_record = Record.objects.filter(name=oldRecord.name, record_type=oldRecord.record_type, zone=zone).first()
            if cache_record:
                cache_record.delete()
            service.update_record(zone_name, old_record_name, newRecord.record_type, oldRecord.content, newRecord.content, ttl=newRecord.ttl)
            return f"Updated {old_record_name} {oldRecord.record_type}"
        except PowerDNSError as e:
            logger.error(e)
            raise Exception("Unable to update record(s)")
    elif oldRecord.name != newRecord.name or oldRecord.record_type != newRecord.record_type:
        try:
            cache_record = Record.objects.filter(name=oldRecord.name, record_type=oldRecord.record_type, zone=zone).first()
            if cache_record:
                cache_record.delete()
            service.delete_record(zone_name, old_record_name, oldRecord.record_type, oldRecord.content)
        except PowerDNSError as e:
            logger.error(e)
            raise Exception("Unable to update record(s)")
        try:
            cache_record = Record.objects.filter(name=oldRecord.name, record_type=oldRecord.record_type, zone=zone).first()
            if cache_record:
                cache_record.delete()
            service.create_record(zone_name, new_record_name, newRecord.record_type, newRecord.content, newRecord.ttl)
            return f"Updated {old_record_name} {oldRecord.record_type}"
        except PowerDNSError as e:
            logger.error(e)
            raise Exception("Unable to update record(s)")
    return Exception("Unable to update record(s)")



def get_zones() -> list[Any] | QuerySet[Zone, Zone]:
    try:
        powerdns_zones = service.get_zones("localhost")
        for zone in powerdns_zones:
            zone['nameservers'] = ["ns1.fuckmylife.fi"]

            if zone.get('nameservers') == '':
                zone['nameservers'] = ["ns1.kapsi.fi"]

            zone_account = None
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
        zone_account = None
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

def update_zone(updated_zone: Zone):
    try:
        cache_zone = Zone.objects.filter(name=updated_zone.name).first()
        cache_zone.delete()

        updated_zone.full_clean()
        updated_zone.save()
        return service.update_zone(zone_name=updated_zone.name, account=str(updated_zone.account.id),
                            nameservers=updated_zone.nameservers,
                            dnssec=updated_zone.dnssec)
    except Exception as e:
        logger.error(e)
        return False

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
                if record.record_type == Record.RECORD_TYPE_SOA and not cache_record:
                    Record.objects.filter(name=normalized_name, zone=zone).delete()
                    record.full_clean()
                    record.save()

                record_instances.append(record)
        return Record.objects.filter(zone=zone).all()
    except PowerDNSError as e:
        zone = get_zone(zone_name)
        Record.objects.filter(zone=zone).all()
        logger.error(e)

def get_record(zone_name: str, record_name: str, record_type: str, record_content: str = None) -> QuerySet[Record, Record] | None:
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
                if record.record_type == Record.RECORD_TYPE_SOA and not cache_record:
                    Record.objects.filter(name=normalized_name, zone=zone).delete()
                    record.full_clean()
                    record.save()

                record_instances.append(record)
        if record_content:
            return Record.objects.filter(name=record_name, record_type=record_type, zone=zone, content=record_content).first()
        return Record.objects.filter(name=record_name, record_type=record_type, zone=zone).first()
    except PowerDNSError as e:
        zone = get_zone(zone_name)
        logger.error(e)
        if record_content:
            return Record.objects.filter(name=record_name, record_type=record_type, zone=zone, content=record_content).first()
        return Record.objects.filter(name=record_name, record_type=record_type, zone=zone).first()

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


def get_dnssec_keys(zone_name: str):
    try:
        return service.get_dnssec_keys(zone_name)
    except PowerDNSError as e:
        logger.error(e)
        return False

def create_dnssec_key(zone_name: str):
    try:
        return service.create_dnssec_key(zone_name)
    except PowerDNSError as e:
        logger.error(e)
        return False

def delete_dnssec_key(zone_name: str, key_id: str):
    try:
        return service.delete_dnssec_key(zone_name, key_id)
    except PowerDNSError as e:
        logger.error(e)
        return False

DIGEST_TYPE_MAP = {
    1: "SHA-1 (Deprecated)",
    2: "SHA-256 (Recommended)",
    3: "GOST R 34.11-94",
    4: "SHA-384",
}
def parse_dnssec_keys(dnssec_keys: str):
    processed_keys = []
    keys_list = dnssec_keys if isinstance(dnssec_keys, list) else [dnssec_keys]

    for key_data in keys_list:
        key_data.pop("privatekey", None)
        parsed_ds_records = []
        for ds_string in key_data.get("ds", []):
            parts = ds_string.split(" ")
            if len(parts) >= 4:
                digest_type_num = int(parts[2])
                parsed_ds_records.append({
                    "raw": ds_string,
                    "key_tag": parts[0],
                    "algorithm": parts[1],
                    "digest_type": parts[2],
                    "digest_type_name": DIGEST_TYPE_MAP.get(
                        digest_type_num, "Unknown"
                    ),
                    "digest": parts[3],
                })

        # Attach the structured array back to the key object
        key_data["parsed_ds"] = parsed_ds_records
        processed_keys.append(key_data)
    return processed_keys


def get_zone_metadata(
        zone_name: str,
        metadata_kind:str = None
):
    try:
        return service.get_zone_metadata(zone_name, metadata_kind)
    except PowerDNSError as e:
        logger.error(e)
        return False

def set_zone_metadata(
        zone_name: str,
        metadata: List[Any],
        metadata_kind: str = None
):
    try:
        return service.set_zone_metadata(zone_name, metadata, metadata_kind)
    except PowerDNSError as e:
        logger.error(e)
        return False

def delete_zone_metadata(zone_name: str, metadata_kind: str = None):
    try:
        return service.delete_zone_metadata(zone_name, metadata_kind)
    except PowerDNSError as e:
        logger.error(e)
        return False

def create_zone_from_template(zone: Zone, template: ZoneTemplate = None):
    template = ZoneTemplate.objects.filter(id=template).first()
    if not zone.name.endswith('.'):
        zone.name = f"{zone.name}."
    zone_account_id = ""
    if zone_account_id is not None:
        zone_account_id = str(zone.account.id)
    try:
        if template is not None:
            resp = service.create_zone(zone_name=zone.name, kind=template.kind, account=zone_account_id,
                            nameservers=['ns1.fuckmylife.fi.'])
        else:
            resp = service.create_zone(zone_name=zone.name, kind=zone.kind, account=zone_account_id,
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
    _record = Record(
        zone=zone,
        name=name,
        record_type=record_type,
        content=content,
        ttl=ttl,
        disabled=disabled
    )
    logger.info(content)
    parsed_content = content
    if record_type in ["CNAME", "NS"]:
        if not content.endswith('.'):
            parsed_content = f"{content}."
            _record.content = parsed_content

    try:
        _record.full_clean()
        _record.save()
        service.create_record(zone.name, name, record_type, parsed_content, ttl)
    except ValidationError as e:
        logger.error(e)

def validate_ip_v4(value):
    try:
        ip = ipaddress.ip_address(value)
        if ip.version != 4:
            raise ValueError
    except ValueError as e:
        logger.error(e)
        raise ValidationError("Invalid Ipv4 address.")

def validate_ip_v6(value):
    try:
        ip = ipaddress.ip_address(value)
        if ip.version != 6:
            raise ValueError
    except ValueError as e:
        logger.error(e)
        raise ValidationError("Invalid Ipv6 address.")

def validate_domain(value):
    domain_pattern = re.compile(
        r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*$'
    )
    try:
        if not domain_pattern.match(value):
            raise ValueError
    except ValueError as e:
        logger.error(e)
        raise ValidationError("Invalid Domain name.")

VALIDATORS = {
    'A': validate_ip_v4,
    'AAAA': validate_ip_v6,
    'CNAME': validate_domain,
    'NS': validate_domain,
}

def validate_record(_record: Record):
    validator = VALIDATORS.get(_record.record_type.upper())
    if validator:
        validator(_record.content)
    else:
        pass

TSIG_ALGORITHMS = ["hmac-md5", "hmac-sha1", "hmac-sha224", "hmac-sha256", "hmac-sha384", "hmac-sha512"]
def get_tsig_keys():
    try:
        return service.get_tsig_keys()
    except PowerDNSError as e:
        logger.error(e)
        return False

def get_tsig_key(key_id: str):
    try:
        return service.get_tsig_key(key_id)
    except PowerDNSError as e:
        logger.error(e)
        return False

def create_tsig_key(name: str, key: str = None, algorithm: str = 'hmac-sha-256'):
    if algorithm not in TSIG_ALGORITHMS:
        raise ValueError(f"Algorithm must be one of {TSIG_ALGORITHMS}")
    try:
        return service.create_tsig_key(name, key, algorithm)
    except PowerDNSError as e:
        logger.error(e)
        return False

def edit_tsig_key(key_id: str, name: str, key: str = None, algorithm: str = 'hmac-sha-256'):
    if algorithm not in TSIG_ALGORITHMS:
        raise ValueError(f"Algorithm must be one of {TSIG_ALGORITHMS}")
    try:
        return service.edit_tsig_key(key_id, name, key, algorithm)
    except PowerDNSError as e:
        logger.error(e)
        return False

def delete_tsig_key(key_id: str):
    try:
        return service.delete_tsig_key(key_id)
    except PowerDNSError as e:
        logger.error(e)
        return False
