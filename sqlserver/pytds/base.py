import sys
from django.conf import settings
from django.db import utils
from django.db.backends.signals import connection_created
try:
    from django.utils.timezone import utc
except:
    pass

try:
    import pytds as Database
except ImportError:
    raise Exception('pytds is not available, run pip install python-tds to fix this')

from sqlserver.base import (
    SqlServerBaseWrapper,
    )

from .introspection import DatabaseIntrospection
from .operations import DatabaseOperations

class DatabaseWrapper(SqlServerBaseWrapper):
    Database = Database

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self.introspection = DatabaseIntrospection(self)
        try:
            self.ops = DatabaseOperations()
        except TypeError:
            self.ops = DatabaseOperations(self)

    def _cursor(self):
        if self.connection is None:
            self.connection = self.get_new_connection(self.settings_dict)
        return CursorWrapper(self.connection.cursor())

    def _set_autocommit(self, autocommit):
        self.connection.autocommit = autocommit

    def get_connection_params(self):
        return self.settings_dict

    def get_new_connection(self, settings_dict):
        """Connect to the database"""
        options = settings_dict.get('OPTIONS', {})
        autocommit=options.get('autocommit', False),
        if not self.use_transactions:
            autocommit = True
        connection = Database.connect(
            server=settings_dict['HOST'],
            database=settings_dict['NAME'],
            user=settings_dict['USER'],
            password=settings_dict['PASSWORD'],
            timeout=self.command_timeout,
            autocommit=autocommit,
            use_mars=options.get('use_mars', False),
            load_balancer=options.get('load_balancer', None),
            use_tz=utc if settings.USE_TZ else None,
        )
        # The OUTPUT clause is supported in 2005+ sql servers
        self.features.can_return_id_from_insert = connection.tds_version >= Database.TDS72
        connection_created.send(sender=self.__class__, connection=self)
        return connection

    def init_connection_state(self):
        pass


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
        except Database.IntegrityError, e:
            if not self.cursor.connection.mars_enabled:
                self.cursor.cancel()
            raise utils.IntegrityError, utils.IntegrityError(*tuple(e)), sys.exc_info()[2]
        except Database.DatabaseError, e:
            if not self.cursor.connection.mars_enabled:
                self.cursor.cancel()
            raise utils.DatabaseError, utils.DatabaseError(*tuple(e)), sys.exc_info()[2]
        except Database.Error:
            if not self.cursor.connection.mars_enabled:
                self.cursor.cancel()
            raise

    def executemany(self, sql, params):
        try:
            return self.cursor.executemany(sql, params)
        except Database.IntegrityError, e:
            raise utils.IntegrityError, utils.IntegrityError(*tuple(e)), sys.exc_info()[2]
        except Database.DatabaseError, e:
            raise utils.DatabaseError, utils.DatabaseError(*tuple(e)), sys.exc_info()[2]

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            return getattr(self.cursor, attr)

    def __iter__(self):
        return iter(self.cursor)
