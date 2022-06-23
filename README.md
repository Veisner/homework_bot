# homework_bot
python telegram bot


Установите зависимости из файла requirements.txt
pip install -r requirements.txt
В папке с файлом manage.py выполните команду:
source venv/Scripts/activate 
python manage.py runserver

python manage.py makemigrations
python manage.py migrate 

coverage run --source='posts,users' manage.py test -v2
coverage report
coverage html

Автор
Василий