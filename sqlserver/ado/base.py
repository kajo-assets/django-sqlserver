"""Microsoft SQL Server database backend for Django."""

from . import dbapi as Database

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
        return Database.Cursor(self.connection)

    def _is_sql2005_and_up(self, conn):
        return int(conn.adoConnProperties.get('DBMS Version').split('.')[0]) >= 9

    def _is_sql2008_and_up(self, conn):
        return int(conn.adoConnProperties.get('DBMS Version').split('.')[0]) >= 10
