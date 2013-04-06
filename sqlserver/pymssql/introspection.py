from ..introspection import BaseSqlDatabaseIntrospection
import pymssql

class DatabaseIntrospection(BaseSqlDatabaseIntrospection):
    data_types_reverse = {
        #'AUTO_FIELD_MARKER': 'AutoField',
        #pymssql.STRING: 'CharField',
        #pymssql.NUMBER: 'IntegerField',
        #pymssql.DECIMAL: 'DecimalField',
        #pymssql.DATETIME: 'DateTimeField',
    }
