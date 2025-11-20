from django.db import models, transaction
import logging
import json
from ast import literal_eval

logger = logging.getLogger(__name__)


class AppSettings:
    """
    Minimal helper for defaults and type conversion.
    Extend `defaults` as needed for your project.
    """
    defaults = {
        'maintenance': False,
        'forward_records_allow_edit': {"A": True, "CNAME": True, "TXT": True},
        'reverse_records_allow_edit': {"PTR": True},
    }

    @staticmethod
    def convert_type(key, value):
        """
        Convert values into Python types where possible.
        """
        if value is None or isinstance(value, (dict, list, bool, int, float)):
            return value

        s = str(value)

        # literal_eval: handles Python literal-like input
        try:
            return literal_eval(s)
        except Exception:
            pass

        # JSON decode
        try:
            return json.loads(s)
        except Exception:
            pass

        # Fallback: plain string
        return s


class Setting(models.Model):
    """
    Stores configurable settings as key/value pairs.
    Values are stored as text but parsed when fetched.
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    value = models.TextField(null=True, blank=True)

    ZONE_TYPE_FORWARD = 'forward'
    ZONE_TYPE_REVERSE = 'reverse'

    def __str__(self):
        return f"{self.name}={self.value}"

    #
    # -----------------------------
    #  GET METHODS
    # -----------------------------
    #
    @classmethod
    def get(cls, setting):
        """
        Retrieve a setting and convert the stored string
        back into a Python object where possible.
        Falls back to defaults if missing.
        """
        obj = cls.objects.filter(name=setting).first()

        if obj is None:
            return AppSettings.defaults.get(setting)

        raw = obj.value
        if raw is None:
            return None

        # Try JSON → literal_eval → raw string
        if isinstance(raw, str):
            # JSON
            try:
                return json.loads(raw)
            except Exception:
                pass

            # literal_eval (dicts, lists, ints, bools)
            try:
                return literal_eval(raw)
            except Exception:
                pass

        return raw

    #
    # -----------------------------
    #  SETTING VALUES
    # -----------------------------
    #

    @classmethod
    def set_maintenance(cls, mode):
        """
        Set maintenance mode to True/False.
        """
        try:
            with transaction.atomic():
                obj, created = cls.objects.get_or_create(
                    name='maintenance',
                    defaults={'value': str(AppSettings.defaults['maintenance'])},
                )

                mode_str = str(mode)
                if obj.value != mode_str:
                    obj.value = mode_str
                    obj.save()

            return True

        except Exception as e:
            logger.error('Cannot set maintenance to %s. DETAIL: %s', mode, e)
            logger.debug(e, exc_info=True)
            return False

    @classmethod
    def toggle(cls, setting):
        """
        Toggle a boolean setting.
        """
        try:
            with transaction.atomic():
                obj, created = cls.objects.get_or_create(
                    name=setting,
                    defaults={'value': str(AppSettings.defaults.get(setting, False))},
                )

                current = obj.value
                # Normalize to a Python bool
                if isinstance(current, str):
                    normalized = current == "True"
                else:
                    normalized = bool(current)

                obj.value = "False" if normalized else "True"
                obj.save()

            return True

        except Exception as e:
            logger.error('Cannot toggle setting %s. DETAIL: %s', setting, e)
            logger.debug(e, exc_info=True)
            return False

    @classmethod
    def set(cls, setting, value):
        """
        Set a setting to any value (bool, list, dict, etc).
        """
        try:
            with transaction.atomic():
                obj, created = cls.objects.get_or_create(
                    name=setting,
                    defaults={'value': None},
                )

                converted = AppSettings.convert_type(setting, value)

                if isinstance(converted, (dict, list)):
                    obj.value = json.dumps(converted)
                else:
                    obj.value = str(converted) if converted is not None else None

                obj.save()

            return True

        except Exception as e:
            logger.error('Cannot edit setting %s. DETAIL: %s', setting, e)
            logger.debug(e, exc_info=True)
            return False

    #
    # -----------------------------
    #  SUPPORT METHODS
    # -----------------------------
    #

    @classmethod
    def get_supported_record_types(cls, zone_type):
        """
        Return the list of editable record types depending on zone type.
        """
        if zone_type == cls.ZONE_TYPE_FORWARD:
            setting_value = cls.get('forward_records_allow_edit')
        elif zone_type == cls.ZONE_TYPE_REVERSE:
            setting_value = cls.get('reverse_records_allow_edit')
        else:
            setting_value = {}

        # Ensure a dict
        if isinstance(setting_value, str):
            # Try JSON → literal_eval → default dict
            try:
                records = json.loads(setting_value)
            except Exception:
                try:
                    records = literal_eval(setting_value)
                except Exception:
                    records = {}
        elif isinstance(setting_value, dict):
            records = setting_value
        else:
            records = {}

        # Extract record types where allowed=True
        return [r for r, allowed in records.items() if allowed]
