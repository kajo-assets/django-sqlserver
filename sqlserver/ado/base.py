import sys
from django.db import utils
from . import dbapi as Database
adodb = Database

from sqlserver.base import (
    SqlServerBaseWrapper,
    make_connection_string
)

from .introspection import DatabaseIntrospection

DatabaseError = Database.DatabaseError
IntegrityError = Database.IntegrityError


class DatabaseWrapper(SqlServerBaseWrapper):

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self.introspection = DatabaseIntrospection(self)

    def _get_new_connection(self, settings_dict):
        return Database.connect(
            make_connection_string(settings_dict),
            self.command_timeout,
            use_transactions=self.use_transactions,
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
        except adodb.IntegrityError, e:
            raise utils.IntegrityError, utils.IntegrityError(*tuple(e)), sys.exc_info()[2]
        except adodb.DatabaseError, e:
            raise utils.DatabaseError, utils.DatabaseError(*tuple(e)), sys.exc_info()[2]
        except adodb.Error:
            raise

    def executemany(self, sql, params):
        try:
            return self.cursor.executemany(sql, params)
        except adodb.IntegrityError, e:
            raise utils.IntegrityError, utils.IntegrityError(*tuple(e)), sys.exc_info()[2]
        except adodb.DatabaseError, e:
            raise utils.DatabaseError, utils.DatabaseError(*tuple(e)), sys.exc_info()[2]

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            return getattr(self.cursor, attr)

    def __iter__(self):
        return iter(self.cursor)
