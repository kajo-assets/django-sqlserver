from ..introspection import BaseSqlDatabaseIntrospection
#import ado_consts

class DatabaseIntrospection(BaseSqlDatabaseIntrospection):
    def get_table_description(self, cursor, table_name, identity_check=True):
        """Return a description of the table, with DB-API cursor.description interface.

        The 'auto_check' parameter has been added to the function argspec.
        If set to True, the function will check each of the table's fields for the
        IDENTITY property (the IDENTITY property is the MSSQL equivalent to an AutoField).

        When a field is found with an IDENTITY property, it is given a custom field number
        of SQL_AUTOFIELD, which maps to the 'AutoField' value in the DATA_TYPES_REVERSE dict.
        """
        cursor.execute("SELECT * FROM [%s] where 1=0" % (table_name))
        columns = cursor.description

        items = list()
        for column in columns:
            column = list(column) # Convert tuple to list
            #if identity_check and self._is_auto_field(cursor, table_name, column[0]):
            #    column[1] = ado_consts.AUTO_FIELD_MARKER
            items.append(column)
        return items
