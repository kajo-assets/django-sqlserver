"""Microsoft SQL Server database backend for Django."""
from django.db import utils
from django.db.backends import BaseDatabaseWrapper, BaseDatabaseFeatures, BaseDatabaseValidation, BaseDatabaseClient
from django.db.backends.signals import connection_created

from creation import DatabaseCreation
from operations import DatabaseOperations


class DatabaseFeatures(BaseDatabaseFeatures):
    uses_custom_query_class = True
    has_bulk_insert = False

    supports_timezones = False
    supports_sequence_reset = False

    can_return_id_from_insert = True

    supports_regex_backreferencing = False

    # Disable test modeltests.lookup.tests.LookupTests.test_lookup_date_as_str
    supports_date_lookup_using_string = False

    supports_tablespaces = True

    ignores_nulls_in_unique_constraints = False
    allows_group_by_pk = False
    supports_microsecond_precision = False


class SqlServerBaseWrapper(BaseDatabaseWrapper):
    vendor = 'microsoft'

    operators = {
        "exact": "= %s",
        "iexact": "LIKE UPPER(%s) ESCAPE '\\'",
        "contains": "LIKE %s ESCAPE '\\'",
        "icontains": "LIKE UPPER(%s) ESCAPE '\\'",
        "gt": "> %s",
        "gte": ">= %s",
        "lt": "< %s",
        "lte": "<= %s",
        "startswith": "LIKE %s ESCAPE '\\'",
        "endswith": "LIKE %s ESCAPE '\\'",
        "istartswith": "LIKE UPPER(%s) ESCAPE '\\'",
        "iendswith": "LIKE UPPER(%s) ESCAPE '\\'",
    }

    def __init__(self, *args, **kwargs):
        self.use_transactions = kwargs.pop('use_transactions', None)

        super(SqlServerBaseWrapper, self).__init__(*args, **kwargs)

        try:
            # django < 1.3
            self.features = DatabaseFeatures()
        except TypeError:
            # django >= 1.3
            self.features = DatabaseFeatures(self)

        try:
            self.ops = DatabaseOperations()
        except TypeError:
            self.ops = DatabaseOperations(self)

        self.client = BaseDatabaseClient(self)
        self.creation = DatabaseCreation(self)
        self.validation = BaseDatabaseValidation(self)

        try:
            self.command_timeout = int(self.settings_dict.get('COMMAND_TIMEOUT', 30))
        except ValueError:
            self.command_timeout = 30

        try:
            options = self.settings_dict.get('OPTIONS', {})
            self.cast_avg_to_float = not bool(options.get('disable_avg_cast', False))
        except ValueError:
            self.cast_avg_to_float = False

        self.ops.features = self.features
        self.ops.is_sql2000 = self.is_sql2000
        self.ops.is_sql2005 = self.is_sql2005
        self.ops.is_sql2008 = self.is_sql2008

    def get_connection_params(self):
        return self.settings_dict

    def get_new_connection(self, settings_dict):
        """Connect to the database"""
        conn = self._get_new_connection(settings_dict)
        # The OUTPUT clause is supported in 2005+ sql servers
        self.features.can_return_id_from_insert = self._is_sql2005_and_up(conn)
        #self.features.has_bulk_insert = self._is_sql2008_and_up(conn)
        self.features.supports_microsecond_precision = self._is_sql2008_and_up(conn)
        self.creation._patch_for_sql2008_and_up()
        connection_created.send(sender=self.__class__, connection=self)
        return conn

    def _get_new_connection(self, settings_dict):
        raise NotImplementedError

    def init_connection_state(self):
        pass

    def __connect(self):
        """Connect to the database"""
        raise NotImplementedError

    def is_sql2000(self):
        """
        Returns True if the current connection is SQL2000. Establishes a
        connection if needed.
        """
        if not self.connection:
            self.__connect()
        return self.connection.is_sql2000

    def is_sql2005(self):
        """
        Returns True if the current connection is SQL2005. Establishes a
        connection if needed.
        """
        if not self.connection:
            self.__connect()
        return self.connection.is_sql2005

    def is_sql2008(self):
        """
        Returns True if the current connection is SQL2008. Establishes a
        connection if needed.
        """
        if not self.connection:
            self.__connect()
        return self.connection.is_sql2008

    def _is_sql2005_and_up(self, conn):
        raise NotImplementedError

    def _is_sql2008_and_up(self, conn):
        raise NotImplementedError

    def _cursor(self):
        raise NotImplementedError

    def disable_constraint_checking(self):
        """
        Turn off constraint checking for every table
        """
        if self.connection:
            cursor = self.connection.cursor()
        else:
            cursor = self._cursor()
        cursor.execute('EXEC sp_MSforeachtable "ALTER TABLE ? NOCHECK CONSTRAINT all"')
        cursor.close()

    def enable_constraint_checking(self):
        """
        Turn on constraint checking for every table
        """
        if self.connection:
            cursor = self.connection.cursor()
        else:
            cursor = self._cursor()
        cursor.execute('EXEC sp_MSforeachtable "ALTER TABLE ? WITH CHECK CHECK CONSTRAINT all"')
        cursor.close()

    def check_constraints(self, table_names=None):
        """
        Check the table constraints.
        """
        if self.connection:
            cursor = self.connection.cursor()
        else:
            cursor = self._cursor()
        if not table_names:
            cursor.execute('DBCC CHECKCONSTRAINTS WITH ALL_CONSTRAINTS')
        else:
            qn = self.ops.quote_name
            for name in table_names:
                cursor.execute('DBCC CHECKCONSTRAINTS({0}) WITH ALL_CONSTRAINTS'.format(
                    qn(name)
                ))
        if cursor.description:
            raise utils.IntegrityError(cursor.fetchall())
