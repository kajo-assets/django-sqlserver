"""Microsoft SQL Server database backend for Django."""
from django.db.backends.signals import connection_created

import dbapi as Database

from sqlserver.base import (
    SqlServerBaseWrapper,
    DatabaseFeatures,
    DatabaseCreation,
    DatabaseOperations,
    is_ip_address,
    connection_string_from_settings,
    make_connection_string
)

from introspection import DatabaseIntrospection

DatabaseError = Database.DatabaseError
IntegrityError = Database.IntegrityError


class DatabaseWrapper(SqlServerBaseWrapper):

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self.introspection = DatabaseIntrospection(self)

    def __connect(self):
        """Connect to the database"""
        self.connection = Database.connect(
            make_connection_string(self.settings_dict),
            self.command_timeout,
            use_transactions=self.use_transactions,
        )

        if self.connection.is_sql2000:
            # SQL 2000 doesn't support the OUTPUT clause
            self.features.can_return_id_from_insert = False

        connection_created.send(sender=self.__class__, connection=self)
        return self.connection

    def _cursor(self):
        if self.connection is None:
            self.__connect()
        return Database.Cursor(self.connection)
