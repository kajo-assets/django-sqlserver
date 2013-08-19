from ..introspection import BaseSqlDatabaseIntrospection
import ado_consts

class DatabaseIntrospection(BaseSqlDatabaseIntrospection):
    data_types_reverse = {
        #ado_consts.AUTO_FIELD_MARKER: 'AutoField',
        ado_consts.adBoolean: 'BooleanField',
        ado_consts.adChar: 'CharField',
        ado_consts.adWChar: 'CharField',
        ado_consts.adDecimal: 'DecimalField',
        ado_consts.adNumeric: 'DecimalField',
        ado_consts.adDBTimeStamp: 'DateTimeField',
        ado_consts.adDouble: 'FloatField',
        ado_consts.adSingle: 'FloatField',
        ado_consts.adInteger: 'IntegerField',
        ado_consts.adBigInt: 'IntegerField',
        #ado_consts.adBigInt: 'BigIntegerField',
        ado_consts.adSmallInt: 'IntegerField',
        ado_consts.adTinyInt: 'IntegerField',
        ado_consts.adVarChar: 'CharField',
        ado_consts.adVarWChar: 'CharField',
        ado_consts.adLongVarWChar: 'TextField',
        ado_consts.adLongVarChar: 'TextField',
        }
