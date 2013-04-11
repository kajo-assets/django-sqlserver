import sys
from django.db import utils
from django.core.exceptions import ImproperlyConfigured, ValidationError
import six
from . import dbapi as Database
adodb = Database

from sqlserver.base import SqlServerBaseWrapper

from .introspection import DatabaseIntrospection

DatabaseError = Database.DatabaseError
IntegrityError = Database.IntegrityError


def is_ip_address(value):
    """
    Returns True if value is a valid IP address, otherwise False.
    """
    try:
        # IPv6 added with Django 1.4
        from django.core.validators import validate_ipv46_address as ip_validator
    except ImportError:
        # Fallback to only IPv4 for older Django
        from django.core.validators import validate_ipv4_address as ip_validator

    try:
        ip_validator(value)
    except ValidationError:
        return False
    return True


def connection_string_from_settings():
    from django.conf import settings
    return make_connection_string(settings)


def make_connection_string(settings):
    class wrap(object):
        def __init__(self, mapping):
            self._dict = mapping

        def __getattr__(self, name):
            d = self._dict
            result = None
            if hasattr(d, "get"):
                if name in d:
                    result = d.get(name)
                else:
                    result = d.get('DATABASE_' + name)
            elif hasattr(d, 'DATABASE_' + name):
                result = getattr(d, 'DATABASE_' + name)
            else:
                result = getattr(d, name, None)
            return result

    settings = wrap(settings)

    db_name = settings.NAME.strip()
    db_host = settings.HOST or '127.0.0.1'
    if len(db_name) == 0:
        raise ImproperlyConfigured("You need to specify a DATABASE NAME in your Django settings file.")

    # Connection strings courtesy of:
    # http://www.connectionstrings.com/?carrier=sqlserver

    # If a port is given, force a TCP/IP connection. The host should be an IP address in this case.
    if settings.PORT:
        if not is_ip_address(db_host):
            raise ImproperlyConfigured("When using DATABASE PORT, DATABASE HOST must be an IP address.")
        try:
            port = int(settings.PORT)
        except ValueError:
            raise ImproperlyConfigured("DATABASE PORT must be a number.")
        db_host = '{0},{1};Network Library=DBMSSOCN'.format(db_host, port)

    # If no user is specified, use integrated security.
    if settings.USER != '':
        auth_string = 'UID={0};PWD={1}'.format(settings.USER, settings.PASSWORD)
    else:
        auth_string = 'Integrated Security=SSPI'

    parts = [
        'DATA SOURCE={0};Initial Catalog={1}'.format(db_host, db_name),
        auth_string
    ]

    options = getattr(settings, 'OPTIONS')
    if not options:
        options = {}

    if not options.get('provider', None):
        options['provider'] = 'sqlncli10'

    parts.append('PROVIDER={0}'.format(options['provider']))

    if options['provider'].lower().find('=sqlcli') != -1:
        # native client needs a compatibility mode that behaves like OLEDB
        parts.append('DataTypeCompatibility=80')

    if options.get('use_mars', True):
        parts.append('MARS Connection=True')

    if options.get('extra_params', None):
        parts.append(options['extra_params'])

    return ";".join(parts)


class DatabaseWrapper(SqlServerBaseWrapper):

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self.introspection = DatabaseIntrospection(self)

    def _get_new_connection(self, settings_dict):
        options = settings_dict.get('OPTIONS', {})
        autocommit = options.get('autocommit', False)
        return Database.connect(
            make_connection_string(settings_dict),
            self.command_timeout,
            use_transactions=not autocommit,
        )

    def __connect(self):
        """Connect to the database"""
        self.connection = self.get_new_connection(self.settings_dict)

    def _cursor(self):
        if self.connection is None:
            self.__connect()
        return CursorWrapper(Database.Cursor(self.connection))

    def _is_sql2005_and_up(self, conn):
        return int(conn.adoConnProperties.get('DBMS Version').split('.')[0]) >= 9

    def _is_sql2008_and_up(self, conn):
        return int(conn.adoConnProperties.get('DBMS Version').split('.')[0]) >= 10


class CursorWrapper(object):
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.cursor.close()

    def execute(self, sql, params = ()):
        try:
            return self.cursor.execute(sql, params)
        except adodb.IntegrityError as e:
            six.reraise(utils.IntegrityError, utils.IntegrityError(*tuple(e.args)), sys.exc_info()[2])
        except adodb.DatabaseError as e:
            six.reraise(utils.DatabaseError, utils.DatabaseError(*tuple(e.args)), sys.exc_info()[2])

    def executemany(self, sql, params):
        try:
            return self.cursor.executemany(sql, params)
        except adodb.IntegrityError as e:
            six.reraise(utils.IntegrityError, utils.IntegrityError(*tuple(e.args)), sys.exc_info()[2])
        except adodb.DatabaseError as e:
            six.reraise(utils.DatabaseError, utils.DatabaseError(*tuple(e.args)), sys.exc_info()[2])

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            return getattr(self.cursor, attr)

    def __iter__(self):
        return iter(self.cursor)
