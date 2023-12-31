# Что исправлено:
- Избранное, подписки-отписки, список покупок - Done!
- Создание рецепта работает (но вроде работало и до этого...) Главное нажимать "добавить ингредиент"
- вход в админку работает по логину и паролю. Нужно переделать на вход по почте? Не понимаю, как это реализовать


# Дипломный проект курса "Бекэнд-разработка на Django"

## Автор: Елена Смирнова

## Проект доступен по адресу: https://teachyou.ddnsking.com/subscriptions

## Данные от админки:
- username: admin
- email: admin@mail.ru
- password: admin123

### Описание проекта:
***foodgram*** - приложение для публикации рецептов. Зарегистрированные пользователи могут *публиковать* свои рецепты с фото, добавлять рецепты в *избранное* и *подписываться* на других авторов. Также есть возможность добавить понравившиеся рецепты в корзину и *выгрузить список продуктов* для их приготовления в формате pdf. Для незарегистрированных пользователей доступен просмотр опубликованных рецептов.

### Используемые технологии:
*Django, RestAPI, Djoser, Docker*

### Установка:
1. Склонируйте репозиторий:
```git clone https://github.com/SmirEV/foodgram-project-react.git

2. Перейдите в папку /infra/
```cd infra/   

3. Создайте файл .env, пример см. ниже
``` nano .env

```POSTGRES_USER=django_user
```POSTGRES_PASSWORD=mysecretpassword
```POSTGRES_DB=django
```DB_HOST=db
```DB_PORT=5432
```PAGE_SIZE=6
```PAGE_SIZE_QUERY_PARAM='page_size'
```MAX_PAGE_SIZE=100
```SECRET_KEY='mysecretkey'
```DEBUG=False
```ALLOWED_HOSTS=localhost,127.0.0.1

4. Запустите docker-compose.yml
```docker compose up --build

5. В отдельном терминале создайте и выполните миграции:
```docker compose exec backend python manage.py makemigrations recipes
```docker compose exec backend python manage.py migrate

6. Собираем статику для админки:
```docker compose exec backend python manage.py collectstatic
```docker compose exec backend cp -r /app/foodgram/collected_static/. /backend_static/static/ 

7. Также можно создать тестовых пользователей и подгрузить данные для просмотра рецептов:
```docker compose exec backend python manage.py loaddata

После этого можно зайти на сайт проекта по ссылке http://localhost:8000/recipes с учетными данными:

Пользователь 1:
Электронная почта: email0@test.ru
Пароль: testpassword0

Пользователь 2:
Электронная почта: email1@test.ru
Пароль: testpassword1

Пользователь 3:
Электронная почта: email2@test.ru
Пароль: testpassword2

8. Или создать суперпользователя:
```docker compose exec backend python manage.py createsuperuser
