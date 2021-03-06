from __future__ import absolute_import

import datetime
import django
import django.core.exceptions
from django.conf import settings
from django.db.backends import BaseDatabaseOperations
try:
    from django.utils.encoding import smart_text
except:
    from django.utils.encoding import smart_unicode as smart_text

try:
    import pytz
except ImportError:
    pytz = None

from django.utils import timezone

from . import fields as mssql_fields

def total_seconds(td):
    if hasattr(td, 'total_seconds'):
        return td.total_seconds()
    else:
        return td.days * 24 * 60 * 60 + td.seconds


class DatabaseOperations(BaseDatabaseOperations):
    compiler_module = "sqlserver.compiler"

    _convert_values_map = {
        # custom fields
        'DateTimeOffsetField':  mssql_fields.DateTimeOffsetField(),
        'LegacyDateField':      mssql_fields.LegacyDateField(),
        'LegacyDateTimeField':  mssql_fields.LegacyDateTimeField(),
        'LegacyTimeField':      mssql_fields.LegacyTimeField(),
        'NewDateField':         mssql_fields.DateField(),
        'NewDateTimeField':     mssql_fields.DateTimeField(),
        'NewTimeField':         mssql_fields.TimeField(),
    }

    def __init__(self, *args, **kwargs):
        super(DatabaseOperations, self).__init__(*args, **kwargs)

        if self.connection.use_legacy_date_fields:
            self._convert_values_map.update({
                'DateField':        self._convert_values_map['LegacyDateField'],
                'DateTimeField':    self._convert_values_map['LegacyDateTimeField'],
                'TimeField':        self._convert_values_map['LegacyTimeField'],
            })
        else:
            self._convert_values_map.update({
                'DateField':        self._convert_values_map['NewDateField'],
                'DateTimeField':    self._convert_values_map['NewDateTimeField'],
                'TimeField':        self._convert_values_map['NewTimeField'],
            })

    def cache_key_culling_sql(self):
        return """
            SELECT [cache_key]
              FROM (SELECT [cache_key], ROW_NUMBER() OVER (ORDER BY [cache_key]) AS [rank] FROM %s) AS [RankedCache]
             WHERE [rank] = %%s + 1
        """

    def date_extract_sql(self, lookup_type, field_name):
        if lookup_type == 'week_day':
            lookup_type = 'weekday'
        return 'DATEPART({0}, {1})'.format(
            lookup_type,
            self.quote_name(field_name),
        )

    def datetime_extract_sql(self, lookup_type, field_name, tzname):
        if settings.USE_TZ:
            if pytz is None:
                from django.core.exceptions import ImproperlyConfigured
                raise ImproperlyConfigured("This query requires pytz, "
                                           "but it isn't installed.")
            tz = pytz.timezone(tzname)
            td = tz.utcoffset(datetime.datetime(2000, 1, 1))
            total_minutes = total_seconds(td) // 60
            hours, minutes = divmod(total_minutes, 60)
            tzoffset = "%+03d:%02d" % (hours, minutes)
            field_name = "CAST(SWITCHOFFSET(TODATETIMEOFFSET(%s, '+00:00'), '%s') AS DATETIME2)" % (field_name, tzoffset)
        if lookup_type == 'week_day':
            lookup_type = 'weekday'
        return 'DATEPART({0}, {1})'.format(
            lookup_type,
            field_name,
            ), []

    def date_interval_sql(self, sql, connector, timedelta):
        """
        implements the interval functionality for expressions
        format for SQL Server.
        """
        sign = 1 if connector == '+' else -1
        seconds = ((timedelta.days * 86400) + timedelta.seconds) * sign
        out = sql
        if seconds:
            out = 'DATEADD(SECOND, {0}, CAST({1} as datetime))'.format(seconds, sql)
        if timedelta.microseconds:
            # DATEADD with datetime doesn't support ms, must cast up
            out = 'DATEADD(MICROSECOND, {ms}, CAST({sql} as datetime2))'.format(
                ms=timedelta.microseconds * sign,
                sql=out,
            )
        return out

    def date_trunc_sql(self, lookup_type, field_name):
        return "DATEADD(%s, DATEDIFF(%s, 0, %s), 0)" % (lookup_type, lookup_type, field_name)

    def datetime_trunc_sql(self, lookup_type, field_name, tzname):
        if settings.USE_TZ:
            if pytz is None:
                from django.core.exceptions import ImproperlyConfigured
                raise ImproperlyConfigured("This query requires pytz, "
                                           "but it isn't installed.")
            tz = pytz.timezone(tzname)
            td = tz.utcoffset(datetime.datetime(2000, 1, 1))
            total_minutes = total_seconds(td) // 60
            hours, minutes = divmod(total_minutes, 60)
            tzoffset = "%+03d:%02d" % (hours, minutes)
            field_name = "CAST(SWITCHOFFSET(TODATETIMEOFFSET(%s, '+00:00'), '%s') AS DATETIME2)" % (field_name, tzoffset)
        return "DATEADD(%s, DATEDIFF(%s, '20000101', %s), '20000101')" % (lookup_type, lookup_type, field_name), []

    def last_insert_id(self, cursor, table_name, pk_name):
        """
        Fetch the last inserted ID by executing another query.
        """
        # IDENT_CURRENT   returns the last identity value generated for a
        #                 specific table in any session and any scope.
        # http://msdn.microsoft.com/en-us/library/ms175098.aspx
        cursor.execute("SELECT CAST(IDENT_CURRENT(%s) as bigint)", [self.quote_name(table_name)])
        return cursor.fetchone()[0]

    def lookup_cast(self, lookup_type):
        if lookup_type in ('iexact', 'icontains', 'istartswith', 'iendswith'):
            return "UPPER(%s)"
        return "%s"

    def return_insert_id(self):
        """
        MSSQL implements the RETURNING SQL standard extension differently from
        the core database backends and this function is essentially a no-op.
        The SQL is altered in the SQLInsertCompiler to add the necessary OUTPUT
        clause.
        """
        if django.VERSION[0] == 1 and django.VERSION[1] < 5:
            # This gets around inflexibility of SQLInsertCompiler's need to
            # append an SQL fragment at the end of the insert query, which also must
            # expect the full quoted table and column name.
            return ('/* %s */', '')

        # Django #19096 - As of Django 1.5, can return None, None to bypass the
        # core's SQL mangling.
        return (None, None)

    def no_limit_value(self):
        return None

    def prep_for_like_query(self, x):
        """Prepares a value for use in a LIKE query."""
        return (
            smart_text(x).\
                replace("\\", "\\\\").\
                replace("%", "\%").\
                replace("_", "\_").\
                replace("[", "\[").\
                replace("]", "\]")
            )

    def quote_name(self, name):
        if name.startswith('[') and name.endswith(']'):
            return name # already quoted
        return '[%s]' % name

    def random_function_sql(self):
        return 'NEWID()'

    def regex_lookup(self, lookup_type):
        # Case sensitivity
        match_option = {'iregex':0, 'regex':1}[lookup_type]
        return "dbo.REGEXP_LIKE(%%s, %%s, %s)=1" % (match_option,)

    def sql_flush(self, style, tables, sequences, allow_cascade=False):
        """
        Returns a list of SQL statements required to remove all data from
        the given database tables (without actually removing the tables
        themselves).

        The `style` argument is a Style object as returned by either
        color_style() or no_style() in django.core.management.color.

        Originally taken from django-pyodbc project.
        """
        if not tables:
            return list()

        qn = self.quote_name

        # Cannot use TRUNCATE on tables that are referenced by a FOREIGN KEY; use DELETE instead.
        # (which is slow)
        cursor = self.connection.cursor()
        # Try to minimize the risks of the braindeaded inconsistency in
        # DBCC CHEKIDENT(table, RESEED, n) behavior.
        seqs = []
        for seq in sequences:
            cursor.execute("SELECT COUNT(*) FROM %s" % qn(seq["table"]))
            rowcnt = cursor.fetchone()[0]
            elem = dict()

            if rowcnt:
                elem['start_id'] = 0
            else:
                elem['start_id'] = 1

            elem.update(seq)
            seqs.append(elem)

        cursor.execute("SELECT TABLE_NAME, CONSTRAINT_NAME FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS WHERE CONSTRAINT_TYPE IN ('CHECK', 'FOREIGN KEY')")
        fks = cursor.fetchall()

        sql_list = list()

        # Turn off constraints.
        sql_list.extend(['ALTER TABLE %s NOCHECK CONSTRAINT %s;' % (
            qn(fk[0]), qn(fk[1])) for fk in fks if fk[0] is not None and fk[1] is not None])

        # Delete data from tables.
        sql_list.extend(['%s %s %s;' % (
            style.SQL_KEYWORD('DELETE'),
            style.SQL_KEYWORD('FROM'),
            style.SQL_FIELD(qn(t))
            ) for t in tables])

        # Reset the counters on each table.
        sql_list.extend(['%s %s (%s, %s, %s) %s %s;' % (
            style.SQL_KEYWORD('DBCC'),
            style.SQL_KEYWORD('CHECKIDENT'),
            style.SQL_FIELD(qn(seq["table"])),
            style.SQL_KEYWORD('RESEED'),
            style.SQL_FIELD('%d' % seq['start_id']),
            style.SQL_KEYWORD('WITH'),
            style.SQL_KEYWORD('NO_INFOMSGS'),
            ) for seq in seqs])

        # Turn constraints back on.
        sql_list.extend(['ALTER TABLE %s CHECK CONSTRAINT %s;' % (
            qn(fk[0]), qn(fk[1])) for fk in fks if fk[0] is not None and fk[1] is not None])

        return sql_list

    def tablespace_sql(self, tablespace, inline=False):
        return "ON %s" % self.quote_name(tablespace)

    def value_to_db_datetime(self, value):
        if value is None:
            return None

        if timezone.is_aware(value):# and not self.connection.features.supports_timezones:
            if getattr(settings, 'USE_TZ', False):
                value = value.astimezone(timezone.utc).replace(tzinfo=None)
            else:
                raise ValueError("SQL Server backend does not support timezone-aware datetimes.")

        if not self.connection.features.supports_microsecond_precision:
            value = value.replace(microsecond=0)
        return value

    def value_to_db_time(self, value):
        if self.connection._is_sql2008_and_up(self.connection.connection):
            return value

        if timezone.is_aware(value):
            if not getattr(settings, 'USE_TZ', False) and hasattr(value, 'astimezone'):
                value = timezone.make_naive(value, timezone.utc)
            else:
                raise ValueError("SQL Server backend does not support timezone-aware times.")

        # MS SQL 2005 doesn't support microseconds
        #...but it also doesn't really suport bare times
        if value is None:
            return None

        if not self.connection.features.supports_microsecond_precision:
            value = value.replace(microsecond=0)
        return value

    def value_to_db_decimal(self, value, max_digits, decimal_places):
        if value is None or value == '':
            return None
        return value # Should be a decimal type (or string)

    def year_lookup_bounds(self, value):
        """
        Returns a two-elements list with the lower and upper bound to be used
        with a BETWEEN operator to query a field value using a year lookup

        `value` is an int, containing the looked-up year.
        """
        first = datetime.datetime(value, 1, 1)
        if self.connection.features.supports_microsecond_precision:
            second = datetime.datetime(value, 12, 31, 23, 59, 59, 999999)
        else:
            second = datetime.datetime(value, 12, 31, 23, 59, 59, 997)
        return [first, second]

    def bulk_batch_size(self, fields, objs):
        """
        Returns the maximum allowed batch size for the backend. The fields
        are the fields going to be inserted in the batch, the objs contains
        all the objects to be inserted.
        """
        return min(len(objs), 2100 // len(fields), 1000)

    def convert_values(self, value, field):
        """
        MSSQL needs help with date fields that might come out as strings.
        """
        if field:
            internal_type = field.get_internal_type()
            if internal_type in self._convert_values_map:
                value = self._convert_values_map[internal_type].to_python(value)
            else:
                value = super(DatabaseOperations, self).convert_values(value, field)
        return value

    def bulk_insert_sql(self, fields, num_values):
        """
        Format the SQL for bulk insert
        """
        items_sql = "(%s)" % ", ".join(["%s"] * len(fields))
        return "VALUES " + ", ".join([items_sql] * num_values)

    def max_name_length(self):
        """
        MSSQL supports identifier names up to 128
        """
        return 128

    def _supports_stddev(self):
        """
        Work around for django ticket #18334.
        This backend supports StdDev and the SQLCompilers will remap to
        the correct function names.
        """
        return True

    def enable_identity_insert(self, table):
        """
        Backends can implement as needed to enable inserts in to
        the identity column.

        Should return True if identity inserts have been enabled.
        """
        if table:
            cursor = self.connection.cursor()
            cursor.execute('SET IDENTITY_INSERT {0} ON'.format(
                self.connection.ops.quote_name(table)
            ))
            return True
        return False

    def disable_identity_insert(self, table):
        """
        Backends can implement as needed to disable inserts in to
        the identity column.

        Should return True if identity inserts have been disabled.
        """
        if table:
            cursor = self.connection.cursor()
            cursor.execute('SET IDENTITY_INSERT {0} OFF'.format(
                self.connection.ops.quote_name(table)
            ))
            return True
        return False

    def savepoint_create_sql(self, sid):
        return "SAVE TRAN %s" % self.quote_name(sid)

    def savepoint_rollback_sql(self, sid):
        return "ROLLBACK TRAN %s" % self.quote_name(sid)
