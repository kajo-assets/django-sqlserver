from django.utils import six
from django.db.backends.schema import BaseDatabaseSchemaEditor
from django.db.models.fields.related import ManyToManyField

__author__ = 'denisenk'

class DatabaseSchemaEditor(BaseDatabaseSchemaEditor):
    sql_delete_table = "DROP TABLE %(table)s"
    sql_delete_column = "ALTER TABLE %(table)s DROP COLUMN %(column)s"
    sql_create_column = "ALTER TABLE %(table)s ADD %(column)s %(definition)s"
    sql_delete_index = "DROP INDEX %(name)s ON %(table)s"
    sql_rename_table = "sp_rename %(old_table)s, %(new_table)s"
    sql_create_fk = "ALTER TABLE %(table)s ADD CONSTRAINT %(name)s FOREIGN KEY (%(column)s) REFERENCES %(to_table)s (%(to_column)s)"

    def prepare_default(self, value):
        # TODO: better handle different types like numbers and dates
        return "'{}'".format(six.text_type(value).replace("'", "''"))

    def remove_field(self, model, field):
        """
        Removes a field from a model. Usually involves deleting a column,
        but for M2Ms may involve deleting a table.
        """
        # Special-case implicit M2M tables
        if isinstance(field, ManyToManyField) and field.rel.through._meta.auto_created:
            return self.delete_model(field.rel.through)
            # It might not actually have a column behind it
        if field.db_parameters(connection=self.connection)['type'] is None:
            return
        # Delete the column
        sql = self.sql_delete_column % {
            "table": self.quote_name(model._meta.db_table),
            "column": self.quote_name(field.column),
            }
        self.execute(sql)
        # Reset connection if required
        if self.connection.features.connection_persists_old_columns:
            self.connection.close()
