# FOODGRAM
## Foodgram - это проект «Продуктовый помощник»
## Описание:
На этом сервисе пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.
### Авторы:
- Ilya Rogozin https://github.com/ilyarogozin
### Технологии:
- Python 3
- Django 2
- DRF
- Docker

# Как запустить проект:
- Установите Docker, инструкция:
https://docs.docker.com/get-docker/

- Установите docker-compose, инструкция:
https://docs.docker.com/compose/install/

- Клонируйте репозиторий:
```
git clone git@github.com:ilyarogozin/foodgram-project-react.git
```

- Создайте в папках backend/ и infra/ файл окружения .env, который будет содержать:
```
SECRET_KEY="7%=jb(^ul=4cz=vfz(z-!z#zq7jq4s0ek++se9%tsyd(=@ye+_"
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
ALLOWED_HOSTS="127.0.0.1 localhost"
```

- Соберите контейнеры и запустите их из папки foodgram-project-react/infra:
```
docker-compose up -d --build
```

#### Установите подсветку синтаксиса терминала bash:
- Откройте конфигурационный файл:
```
nano /etc/skel/.bashrc
```
- Раскомментите строку __force_color_prompt=yes__
- Примените изменения:
```
source /etc/skel/.bashrc
```
-----------------------------------------------------

#### Далее все команды выполняйте из папки infra/
- Выполните миграции:
```
docker-compose exec backend python manage.py migrate
```

- Создайте суперпользователя:
```
docker-compose exec backend python manage.py createsuperuser
```

- Соберите статику:
```
docker-compose exec backend python manage.py collectstatic --no-input
```

- Заполните БД начальными данными:
```
docker-compose exec backend python data_to_db.py
```

## Примеры запросов к API можно посмотреть по запросу:
http://51.250.70.25/api/docs/

## Главная страница:
http://51.250.70.25/
