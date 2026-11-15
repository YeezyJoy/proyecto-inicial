
iniciar base de datos:
python manage.py makemigrations cuentas
python manage.py migrate

crear cuenta con
usuario: test
contraseña: test1988

cargar cargar_catalogo asociado a la cuenta
python manage.py cargar_catalogo test

iniciar servidor local
python manage.py runserver

Acceder desde el navegador a: `http://127.0.0.1:8000/`