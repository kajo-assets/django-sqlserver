from django.utils import six
from django.db.backends.schema import BaseDatabaseSchemaEditor

__author__ = 'denisenk'

class DatabaseSchemaEditor(BaseDatabaseSchemaEditor):
    sql_delete_table = "DROP TABLE %(table)s"
    sql_delete_column = "ALTER TABLE %(table)s DROP COLUMN %(column)s"
    sql_create_column = "ALTER TABLE %(table)s ADD %(column)s %(definition)s"
    sql_delete_index = "DROP INDEX %(name)s ON %(table)s"
    sql_rename_table = "sp_rename %(old_table)s, %(new_table)s"

    def prepare_default(self, value):
        # TODO: better handle different types like numbers and dates
        return "'{}'".format(six.text_type(value).replace("'", "''"))
