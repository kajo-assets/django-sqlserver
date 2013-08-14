from ..introspection import BaseSqlDatabaseIntrospection
import pytds

class DatabaseIntrospection(BaseSqlDatabaseIntrospection):
    data_types_reverse = {
        #'AUTO_FIELD_MARKER': 'AutoField',
        pytds.SYBBIT: 'BooleanField',
        pytds.XSYBCHAR: 'CharField',
        pytds.XSYBNCHAR: 'CharField',
        pytds.SYBDECIMAL: 'DecimalField',
        pytds.SYBNUMERIC: 'DecimalField',
        #pytds.adDBTimeStamp: 'DateTimeField',
        pytds.SYBREAL: 'FloatField',
        pytds.SYBFLT8: 'FloatField',
        pytds.SYBINT4: 'IntegerField',
        pytds.SYBINT8: 'BigIntegerField',
        pytds.SYBINT2: 'IntegerField',
        pytds.SYBINT1: 'IntegerField',
        pytds.XSYBVARCHAR: 'CharField',
        pytds.XSYBNVARCHAR: 'CharField',
        pytds.SYBTEXT: 'TextField',
        pytds.SYBNTEXT: 'TextField',
    }
