from ..introspection import BaseSqlDatabaseIntrospection
import pymssql

class DatabaseIntrospection(BaseSqlDatabaseIntrospection):
    data_types_reverse = {
        #'AUTO_FIELD_MARKER': 'AutoField',
        pymssql.SYBBIT: 'BooleanField',
        pymssql.XSYBCHAR: 'CharField',
        pymssql.XSYBNCHAR: 'CharField',
        pymssql.SYBDECIMAL: 'DecimalField',
        pymssql.SYBNUMERIC: 'DecimalField',
        #pymssql.adDBTimeStamp: 'DateTimeField',
        pymssql.SYBREAL: 'FloatField',
        pymssql.SYBFLT8: 'FloatField',
        pymssql.SYBINT4: 'IntegerField',
        pymssql.SYBINT8: 'BigIntegerField',
        pymssql.SYBINT2: 'IntegerField',
        pymssql.SYBINT1: 'IntegerField',
        pymssql.XSYBVARCHAR: 'CharField',
        pymssql.XSYBNVARCHAR: 'CharField',
        pymssql.SYBTEXT: 'TextField',
        pymssql.SYBNTEXT: 'TextField',
    }
