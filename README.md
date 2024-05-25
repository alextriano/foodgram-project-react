# Foodgram

![yamdb_workflow.yml](https://github.com/alextriano/foodgram-project-react/actions/workflows/main.yml/badge.svg) - в настоящее время у меня нет сервера для деплоя проекта, поэтому workflow не выполняется до конца.

## О проекте

В данном сервисе реализована возможность размещения пользователями рецептов различных блюд, подписки на публикации других пользователей, добавления понравившиеся рецепты в список «Избранное», скачивания списка ингредиентов, необходимых для приготовления выбранных блюд.

## Технологии

Python 3.9, Django 3.2, Django REST Framework 3.12, Djoser 2.2, Gunicorn 20.1, React, Docker, Nginx.

## Запуск проекта на локальном компьютере

Клонировать репозиторий и перейти в него в командной строке:
```bash
git clone https://github.com/alextriano/foodgram-project-react.git
cd foodgram-project-react
```
Cоздать и активировать виртуальное окружение:
* Если у вас Linux/MacOS:
    
    ```
    python3 -m venv env
    source env/bin/activate
    ```
* Если у вас Windows:
    
    ```
    python -m venv env
    source env/scripts/activate
    ```
Установить/обновить pip:
```
python3 -m pip install --upgrade pip
```
Установить зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```
Перейти в каталог infra:
```
cd foodgram-project-react/infra
```
Создать файл .evn для хранения ключей:
```bash
SECRET_KEY='указать секретный ключ'
ALLOWED_HOSTS='указать имя или IP хоста'
POSTGRES_DB=kittygram
POSTGRES_USER=kittygram_user
POSTGRES_PASSWORD=kittygram_password
DB_NAME=kittygram
DB_HOST=db
DB_PORT=5432
DEBUG=False
```
Запустить docker-compose.production:
```bash
sudo docker compose -f docker-compose.production.yml up
```
Создать/выполнить миграции, собрать статику, загрузить ингредиенты:
```bash
sudo docker compose -f docker-compose.production.yml exec backend python manage.py makemigrations
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /static/static/
sudo docker compose -f docker-compose.production.yml exec backend python manage.py import
```
Создать суперпользователя, ввести почту, логин, пароль:
```bash
sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
```
# Автор проекта
[Александр Волков](https://github.com/alextriano)
