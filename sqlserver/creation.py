from __future__ import absolute_import

from django.conf import settings
from django.db.backends.creation import BaseDatabaseCreation, TEST_DATABASE_PREFIX
from django.db.utils import load_backend
from django.utils import six

class DatabaseCreation(BaseDatabaseCreation):
    # This dictionary maps Field objects to their associated Server Server column
    # types, as strings. Column-type strings can contain format strings; they'll
    # be interpolated against the values of Field.__dict__.
    data_types = {
        'AutoField':                    'int IDENTITY (1, 1)',
        'BigAutoField':                 'bigint IDENTITY (1, 1)',
        'BigIntegerField':              'bigint',
        'BooleanField':                 'bit',
        'CharField':                    'nvarchar(%(max_length)s)',
        'CommaSeparatedIntegerField':   'nvarchar(%(max_length)s)',
        'DateField':                    'date',
        'DateTimeField':                'datetime2',
        'DateTimeOffsetField':          'datetimeoffset',
        'DecimalField':                 'decimal(%(max_digits)s, %(decimal_places)s)',
        'FileField':                    'nvarchar(%(max_length)s)',
        'FilePathField':                'nvarchar(%(max_length)s)',
        'FloatField':                   'double precision',
        'GenericIPAddressField':        'nvarchar(39)',
        'IntegerField':                 'int',
        'IPAddressField':               'nvarchar(15)',
        'LegacyDateField':              'datetime',
        'LegacyDateTimeField':          'datetime',
        'LegacyTimeField':              'time',
        'NewDateField':                 'date',
        'NewDateTimeField':             'datetime2',
        'NewTimeField':                 'time',
        'NullBooleanField':             'bit',
        'OneToOneField':                'int',
        'PositiveIntegerField':         'int CHECK ([%(column)s] >= 0)',
        'PositiveSmallIntegerField':    'smallint CHECK ([%(column)s] >= 0)',
        'SlugField':                    'nvarchar(%(max_length)s)',
        'SmallIntegerField':            'smallint',
        'TextField':                    'nvarchar(max)',
        'TimeField':                    'time',
        'BinaryField':                  'varbinary(max)',
    }

    def __init__(self, *args, **kwargs):
        super(DatabaseCreation, self).__init__(*args, **kwargs)

        if self.connection.use_legacy_date_fields:
            self.data_types.update({
                'DateField': 'datetime',
                'DateTimeField': 'datetime',
                'TimeField': 'datetime',
            })

    def _create_master_connection(self):
        """
        Create a transactionless connection to 'master' database.
        """
        master_settings = self.connection.settings_dict.copy()
        if not master_settings['TEST_NAME']:
            master_settings['TEST_NAME'] = 'test_' + master_settings['NAME']
        master_settings['NAME'] = 'master'
        master_settings['OPTIONS'] = master_settings['OPTIONS'].copy()
        master_settings['OPTIONS']['autocommit'] = True
        backend = load_backend(master_settings['ENGINE'])
        return backend.DatabaseWrapper(master_settings)

    def _create_test_db(self, verbosity=1, autoclobber=False):
        """
        Create the test databases using a connection to database 'master'.
        """
        test_database_name = self._test_database_name(settings)

        if not self._test_database_create(settings):
            if verbosity >= 1:
                six.print_("Skipping Test DB creation")
            return test_database_name

        # clear any existing connections to the database
        old_wrapper = self.connection
        old_wrapper.close()

        # connect to master database
        self.connection = self._create_master_connection()

        try:
            super(DatabaseCreation, self)._create_test_db(verbosity, autoclobber)
            self.install_regex(test_database_name)
        except Exception as e:
            if 'Choose a different database name.' in str(e):
                six.print_('Database "%s" could not be created because it already exists.' % test_database_name)
            else:
                raise
        finally:
            # set thing back
            self.connection.close()
            self.connection = old_wrapper

        return test_database_name


    def install_regex(self, test_database_name):
        import os
        import binascii
        with open(os.path.join(os.path.dirname(__file__), 'regex_clr.dll'), 'rb') as f:
            assembly = binascii.hexlify(f.read()).decode('ascii')
        sql = 'CREATE ASSEMBLY regex_clr FROM 0x' + assembly
        cursor = self.connection.cursor()
        try:
            cursor.execute('USE [{0}]'.format(test_database_name))
            cursor.execute(sql)
            cursor.execute('''
            create function REGEXP_LIKE
            (
                @input nvarchar(4000),
                @pattern nvarchar(4000),
                @caseSensitive int
            ) 
            RETURNS INT  AS 
            EXTERNAL NAME regex_clr.UserDefinedFunctions.REGEXP_LIKE
            ''')
        finally:
            cursor.close()


    def _destroy_test_db(self, test_database_name, verbosity=1):
        """
        Drop the test databases using a connection to database 'master'.
        """

        if not self._test_database_create(settings):
            if verbosity >= 1:
                six.print_("Skipping Test DB destruction")
            return

        old_wrapper = self.connection
        old_wrapper.close()
        self.connection = self._create_master_connection()

        try:
            super(DatabaseCreation, self)._destroy_test_db(test_database_name, verbosity)
        except Exception as e:
            if 'it is currently in use' in str(e):
                six.print_('Cannot drop database %s because it is in use' % test_database_name)
            else:
                raise
        finally:
            self.connection = old_wrapper


    def _test_database_create(self, settings):
        """
        Check the settings to see if the test database should be created.
        """
        if 'TEST_CREATE' in self.connection.settings_dict:
            return self.connection.settings_dict.get('TEST_CREATE', True)
        if hasattr(settings, 'TEST_DATABASE_CREATE'):
            return settings.TEST_DATABASE_CREATE
        else:
            return True

    def _test_database_name(self, settings):
        """
        Get the test database name.
        """
        try:
            name = TEST_DATABASE_PREFIX + self.connection.settings_dict['NAME']
            if self.connection.settings_dict['TEST_NAME']:
                name = self.connection.settings_dict['TEST_NAME']
        except AttributeError:
            if hasattr(settings, 'TEST_DATABASE_NAME') and settings.TEST_DATABASE_NAME:
                name = settings.TEST_DATABASE_NAME
            else:
                name = TEST_DATABASE_PREFIX + settings.DATABASE_NAME
        return name

    def sql_create_model_sql2008(self, model, style, known_models=set()):
        opts = model._meta
        if not opts.managed or opts.proxy or getattr(opts, 'swapped', False):
            return [], {}
        qn = self.connection.ops.quote_name
        fix_fields = []
        queries = []
        for f in opts.local_fields:
            if not f.primary_key and f.unique and f.null:
                sql = style.SQL_KEYWORD('CREATE UNIQUE INDEX') +\
                    ' [idx_{table}_{column}] ' + style.SQL_KEYWORD('ON') +\
                    ' [{table}]([{column}]) ' + style.SQL_KEYWORD('WHERE') +\
                    ' [{column}] ' + style.SQL_KEYWORD('IS NOT NULL')
                queries.append(sql.format(table=opts.db_table,
                                          column=f.column))
                fix_fields.append(f)
                f._unique = False
        for field_constraints in opts.unique_together:
            predicate_parts = ['[{0}] '.format(opts.get_field(f).column) + style.SQL_KEYWORD('IS NOT NULL')
                               for f in field_constraints if opts.get_field(f).null]
            index_name = 'UX_{table}_{columns}'.format(
                table=opts.db_table,
                columns='_'.join(opts.get_field(f).column for f in field_constraints),
                )[:128]
            sql = style.SQL_KEYWORD('CREATE UNIQUE INDEX') +\
                ' {index_name} ' + style.SQL_KEYWORD('ON') +\
                ' {table}({columns_csep})'
            sql = sql.format(
                index_name=qn(index_name),
                table=style.SQL_TABLE(qn(opts.db_table)),
                columns_csep=','.join(qn(opts.get_field(f).column)
                                      for f in field_constraints),
                )
            if predicate_parts:
                sql += style.SQL_KEYWORD(' WHERE') + \
                    style.SQL_KEYWORD(' AND ').join(predicate_parts)
            queries.append(sql)
        unique_together = opts.unique_together
        opts.unique_together = []
        list_of_sql, pending_references_dict = super(DatabaseCreation, self).sql_create_model(model, style, known_models)
        opts.unique_together = unique_together
        for f in fix_fields:
            f._unique = True
        list_of_sql.extend(queries)
        return list_of_sql, pending_references_dict
