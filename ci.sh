#!/bin/bash
set -e
virtualenv --no-site-packages env
. env/bin/activate
pip install django==$DJANGO_VER --use-mirrors

if [ $BACKEND = sqlserver.pytds ]; then
    pip install -e git+git://github.com/denisenkom/pytds.git#egg=pytds
fi
if [ $BACKEND = sqlserver.pymssql ]; then
    pip install cython hg+https://denisenkom@code.google.com/r/denisenkom-pymssql/ --use-mirrors
fi
cat > tests/local_settings.py << EOF
DATABASE_USER = '$SQLUSER'
DATABASE_PASSWORD = '$SQLPASSWORD'
EOF
export COMPUTERNAME=$HOST
python tests/test_main/manage.py test --noinput
#python tests/test_regex_compare/manage.py test --noinput
#python tests/test_inspectdb/manage.py test --noinput
#python tests/test_stardardapps/manage.py test --noinput
