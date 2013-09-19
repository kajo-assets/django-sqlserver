:: using system-site-packages to get pywin32 package which is not installable via pip
%PYTHONHOME%\scripts\virtualenv env --system-site-packages
call env\scripts\activate.bat

set django_branch=stable/%DJANGO_VER%.x

if not exist env\src\django call git clone https://github.com/denisenkom/django.git -b %django_branch% env/src/django
pushd env\src\django
call git pull
popd
env\scripts\pip install -e env/src/django

if not exist pytds call git clone https://github.com/denisenkom/pytds.git
pushd pytds
call git pull
popd
env\scripts\pip install -e ./pytds

env\bin\pip install pytz==2013d --use-mirrors

set COMPUTERNAME=%HOST%
python tests\test_main\manage.py test --noinput

set PYTHONPATH=.
python env\src\django\tests\runtests.py --noinput --settings=django_settings --liveserver=localhost:8200-8300
