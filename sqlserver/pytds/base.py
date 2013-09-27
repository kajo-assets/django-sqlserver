from django.conf import settings
try:
    from django.utils.timezone import utc
except:
    pass

try:
    import pytds
except ImportError:
    pytds = None
    raise Exception('pytds is not available, run pip install python-tds to fix this')

from sqlserver.base import SqlServerBaseWrapper

from .introspection import DatabaseIntrospection

Database = pytds


def utc_tzinfo_factory(offset):
    if offset != 0:
        raise AssertionError("database connection isn't set to UTC")
    return utc


class DatabaseWrapper(SqlServerBaseWrapper):
    Database = pytds

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self.introspection = DatabaseIntrospection(self)

    def create_cursor(self):
        cursor = self.connection.cursor()
        cursor.tzinfo_factory = utc_tzinfo_factory if settings.USE_TZ else None
        return cursor

    def _set_autocommit(self, autocommit):
        self.connection.autocommit = autocommit

    def get_connection_params(self):
        settings_dict = self.settings_dict
        options = settings_dict.get('OPTIONS', {})
        autocommit = options.get('autocommit', False)
        conn_params = {
            'server': settings_dict['HOST'],
            'database': settings_dict['NAME'],
            'user': settings_dict['USER'],
            'password': settings_dict['PASSWORD'],
            'timeout': self.command_timeout,
            'autocommit': autocommit,
            'use_mars': options.get('use_mars', False),
            'load_balancer': options.get('load_balancer', None),
            'use_tz': utc if getattr(settings, 'USE_TZ', False) else None,
        }
        return conn_params

    def _get_new_connection(self, conn_params):
        return pytds.connect(**conn_params)

    def _enter_transaction_management(self, managed):
        if self.features.uses_autocommit and managed:
            self.connection.autocommit = False

    def _leave_transaction_management(self, managed):
        if self.features.uses_autocommit and not managed:
            self.connection.autocommit = True

    def _is_sql2005_and_up(self, conn):
        return conn.tds_version >= pytds.TDS72

    def _is_sql2008_and_up(self, conn):
        return conn.tds_version >= pytds.TDS73
