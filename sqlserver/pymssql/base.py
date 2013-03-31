import sys
from django.conf import settings
from django.db import utils
from django.db.backends.signals import connection_created
try:
    from django.utils.timezone import utc
except:
    pass

try:
    import pymssql as Database
except ImportError:
    raise Exception('pymssql is not available, run pip install pymssql to fix this')

from sqlserver.base import (
    SqlServerBaseWrapper,
    )

from .introspection import DatabaseIntrospection
from .operations import DatabaseOperations

VERSION_SQL2000 = 8
VERSION_SQL2005 = 9
VERSION_SQL2008 = 10

class DatabaseWrapper(SqlServerBaseWrapper):
    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self.introspection = DatabaseIntrospection(self)
        try:
            self.ops = DatabaseOperations()
        except TypeError:
            self.ops = DatabaseOperations(self)

    def _cursor(self):
        if self.connection is None:
            """Connect to the database"""
            options = self.settings_dict.get('OPTIONS', {})
            self.connection = Database.connect(
                host=self.settings_dict['HOST'],
                database=self.settings_dict['NAME'],
                user=self.settings_dict['USER'],
                password=self.settings_dict['PASSWORD'],
                timeout=self.command_timeout,
            )
            # The OUTPUT clause is supported in 2005+ sql servers
            try:
                cur = self.connection.cursor()
                cur.execute("SELECT SERVERPROPERTY('productversion')")
                ver = cur.fetchone()[0]
                major = int(ver.split('.')[0])
            finally:
                cur.close()
            self.features.can_return_id_from_insert = major >= VERSION_SQL2005
            self.connection.autocommit(not self.use_transactions)
            connection_created.send(sender=self.__class__, connection=self)
        return CursorWrapper(self.connection.cursor())


class CursorWrapper(object):
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.cursor.close()

    def execute(self, sql, params = ()):
        try:
            if isinstance(params, list):
                params = tuple(params)
            return self.cursor.execute(sql, params)
        except Database.IntegrityError, e:
            raise utils.IntegrityError, utils.IntegrityError(*tuple(e)), sys.exc_info()[2]
        except Database.DatabaseError, e:
            raise utils.DatabaseError, utils.DatabaseError(*tuple(e)), sys.exc_info()[2]
        except Database.Error:
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
