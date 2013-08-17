:: using system-site-packages to get pywin32 package which is not installable via pip
%PYTHONHOME%\scripts\virtualenv env --system-site-packages
call env\scripts\activate.bat
if not exist pytds call git clone https://github.com/denisenkom/pytds.git
pushd pytds
call git pull
popd
env\scripts\pip install -e ./pytds
env\scripts\pip install django==%DJANGO_VER% --use-mirrors
set COMPUTERNAME=%HOST%
env\scripts\python tests\test_main\manage.py test --noinput
