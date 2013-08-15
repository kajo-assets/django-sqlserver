#!/bin/bash
set -e
$PYTHONHOME/bin/virtualenv --no-site-packages env
. env/bin/activate
python env/bin/pip install django==$DJANGO_VER --use-mirrors

if [ $BACKEND = sqlserver.pytds ]; then
    python env/bin/pip install -e git+git://github.com/denisenkom/pytds.git#egg=pytds
fi
if [ $BACKEND = sqlserver.pymssql ]; then
    python env/bin/pip install cython hg+https://denisenkom@code.google.com/r/denisenkom-pymssql/ --use-mirrors
fi
export COMPUTERNAME=$HOST
python tests/test_main/manage.py test --noinput
#python tests/test_regex_compare/manage.py test --noinput
#python tests/test_inspectdb/manage.py test --noinput
#python tests/test_stardardapps/manage.py test --noinput
