from ..operations import DatabaseOperations as BaseDatabaseOperations
import pytds
try:
    from django.utils import timezone
except ImportError:
    # timezone added in Django 1.4, use provided partial backport
    from sqlserver import timezone

class DatabaseOperations(BaseDatabaseOperations):
    def value_to_db_time(self, value):
        if self.connection.connection.tds_version >= pytds.TDS73:
            return value

        if timezone.is_aware(value):
            raise ValueError("SQL Server backend does not support timezone-aware times.")

        # MS SQL 2005 doesn't support microseconds
        #...but it also doesn't really suport bare times
        if value is None:
            return None

        return value.replace(microsecond=0)
