"""Microsoft SQL Server database backend for Django."""
from django.db import utils
from django.db.backends import BaseDatabaseWrapper, BaseDatabaseFeatures, BaseDatabaseValidation, BaseDatabaseClient
from django.db.backends.signals import connection_created

from .creation import DatabaseCreation
from .operations import DatabaseOperations


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
    allows_group_by_ordinal = False
    supports_microsecond_precision = False
    supports_subqueries_in_group_by = False
    allow_sliced_subqueries = False
    uses_savepoints = True


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
        super(SqlServerBaseWrapper, self).__init__(*args, **kwargs)

        self.features = DatabaseFeatures(self)
        autocommit = self.settings_dict["OPTIONS"].get("autocommit", False)
        self.features.uses_autocommit = autocommit
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
        self.features.has_bulk_insert = self._is_sql2008_and_up(conn)
        if type(self).__module__.startswith('sqlserver.pytds.'):
            # only pytds support new sql server date types
            supports_new_date_types = self._is_sql2008_and_up(conn)
            self.features.supports_microsecond_precision = supports_new_date_types
            if supports_new_date_types:
                self.creation._patch_for_sql2008_and_up()
        if settings_dict["OPTIONS"].get("allow_nulls_in_unique_constraints", True):
            self.features.ignores_nulls_in_unique_constraints = self._is_sql2008_and_up(conn)
            if self._is_sql2008_and_up(conn):
                self.creation.sql_create_model = self.creation.sql_create_model_sql2008
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
        cursor.execute("EXEC sp_MSforeachtable 'ALTER TABLE ? NOCHECK CONSTRAINT all'")
        # this breakes test on ado, see Issue #2
        while cursor.nextset():
            pass
        cursor.close()
        return True

    def enable_constraint_checking(self):
        """
        Turn on constraint checking for every table
        """
        if self.connection:
            cursor = self.connection.cursor()
        else:
            cursor = self._cursor()
        cursor.execute("EXEC sp_MSforeachtable 'ALTER TABLE ? WITH NOCHECK CHECK CONSTRAINT all'")
        # this breakes test on ado, see Issue #2
        while cursor.nextset():
            pass
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
            if cursor.description:
                raise utils.IntegrityError(cursor.fetchall())
        else:
            qn = self.ops.quote_name
            for name in table_names:
                cursor.execute('DBCC CHECKCONSTRAINTS({0}) WITH ALL_CONSTRAINTS'.format(
                    qn(name)
                ))
                if cursor.description:
                    raise utils.IntegrityError(cursor.fetchall())

    def _savepoint_commit(self, sid):
        pass
