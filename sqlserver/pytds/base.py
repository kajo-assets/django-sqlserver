import sys
from django.conf import settings
from django.db import utils
import six
try:
    from django.utils.timezone import utc
except:
    pass

try:
    import pytds
except ImportError:
    raise Exception('pytds is not available, run pip install python-tds to fix this')

from sqlserver.base import (
    SqlServerBaseWrapper,
    )

from .introspection import DatabaseIntrospection

class DatabaseWrapper(SqlServerBaseWrapper):
    Database = pytds

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self.introspection = DatabaseIntrospection(self)

    def _cursor(self):
        if self.connection is None:
            self.connection = self.get_new_connection(self.settings_dict)
        return CursorWrapper(self.connection.cursor())

    def _set_autocommit(self, autocommit):
        self.connection.autocommit = autocommit

    def _get_new_connection(self, settings_dict):
        """Connect to the database"""
        options = settings_dict.get('OPTIONS', {})
        autocommit = options.get('autocommit', False)
        return pytds.connect(
            server=settings_dict['HOST'],
            database=settings_dict['NAME'],
            user=settings_dict['USER'],
            password=settings_dict['PASSWORD'],
            timeout=self.command_timeout,
            autocommit=autocommit,
            use_mars=options.get('use_mars', False),
            load_balancer=options.get('load_balancer', None),
            use_tz=utc if getattr(settings, 'USE_TZ', False) else None,
        )

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
        except pytds.IntegrityError as e:
            six.reraise(utils.IntegrityError, utils.IntegrityError(*tuple(e.args)), sys.exc_info()[2])
        except pytds.DatabaseError as e:
            six.reraise(utils.DatabaseError, utils.DatabaseError(*tuple(e.args)), sys.exc_info()[2])
        except:
            raise

    def executemany(self, sql, params):
        try:
            return self.cursor.executemany(sql, params)
        except pytds.IntegrityError as e:
            six.reraise(utils.IntegrityError, utils.IntegrityError(*tuple(e.args)), sys.exc_info()[2])
        except pytds.DatabaseError as e:
            six.reraise(utils.DatabaseError, utils.DatabaseError(*tuple(e.args)), sys.exc_info()[2])

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            return getattr(self.cursor, attr)

    def __iter__(self):
        return iter(self.cursor)
