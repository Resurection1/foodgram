[![Main Foodgram workflow](https://github.com/Resurection1/foodgram/actions/workflows/main.yaml/badge.svg)](https://github.com/Resurection1/foodgram/actions/workflows/main.yaml)

`Python` `Django` `Django Rest Framework` `Docker` `Gunicorn` `NGINX` `PostgreSQL` `Yandex Cloud` `Continuous Integration` `Continuous Deployment`

# **Foodgram**
Foodgram, «Продуктовый помощник». Онлайн-сервис и API для него. На этом сервисе пользователи публикуют свои рецепты, подписываются на публикации других пользователей, добавляют понравившиеся рецепты в список «Избранное», а перед походом в магазин могут скачать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

**_Ссылка на [проект](https://foodgramm.sytes.net/admin/ "Гиперссылка к проекту.")_**

**_Ссылка на [админ-зону](https://foodgramm.sytes.net/admin/ "Гиперссылка к админке.")_**

### Развернуть проект на удаленном сервере:

**Клонировать репозиторий:**
```
git@github.com:Resurection1/foodgram.git
```
**_Установить на сервере Docker, Docker Compose:_**
```
sudo apt install curl                                   - установка утилиты для скачивания файлов
curl -fsSL https://get.docker.com -o get-docker.sh      - скачать скрипт для установки
sh get-docker.sh                                        - запуск скрипта
sudo apt-get install docker-compose-plugin              - последняя версия docker compose
```
**_Скопировать на сервер файлы docker-compose.yml, nginx.conf из папки infra (команды выполнять находясь в папке infra):_**
```
scp docker-compose.yml nginx.conf username@IP:/home/username/

# username - имя пользователя на сервере
# IP - публичный IP сервера
```

**_Для работы с GitHub Actions необходимо в репозитории в разделе Secrets > Actions создать переменные окружения:_**
```
    DOCKER_USERNAME                # имя пользователя в DockerHub
    DOCKER_PASSWORD                # пароль пользователя в DockerHub
    DOCKER_NAME_REPO               # Первичное имя репозитория
    HOST                           # IP-адрес сервера
    USER                           # имя пользователя от сервера
    SSH_KEY                        # содержимое приватного SSH-ключа (cat ~/.ssh/id_rsa)
    SSH_PASSPHRASE                 # пароль для SSH-ключа

    TELEGRAM_TO                    # ID вашего телеграм-аккаунта (можно узнать у @userinfobot, команда /start)
    TELEGRAM_TOKEN                 # токен вашего бота (получить токен можно у @BotFather, команда /token, имя бота)
```

**_Создать и запустить контейнеры Docker, выполнить команду на сервере (версии команд "docker compose" или "docker-compose" отличаются в зависимости от установленной версии Docker Compose):**_
```
sudo docker compose up -d
```
**_Выполнить миграции:_**
```
sudo docker compose exec backend python manage.py migrate
```
**_Собрать статику:_**
```
sudo docker compose exec backend python manage.py collectstatic --noinput
```
**_Наполнить базу данных содержимым из файла ingredients.json:_**
```
sudo docker compose exec backend python manage.py loaddata ingredients.json
```
**_Создать суперпользователя:_**
```
sudo docker compose exec backend python manage.py createsuperuser
```
**_Для остановки контейнеров Docker:_**
```
sudo docker compose down -v      - с их удалением
sudo docker compose stop         - без удаления
```
### После каждого обновления репозитория (push в ветку master) будет происходить:

1. Проверка кода на соответствие стандарту PEP8 (с помощью пакета flake8)
2. Сборка и доставка докер-образов frontend и backend на Docker Hub
3. Разворачивание проекта на удаленном сервере
4. Отправка сообщения в Telegram в случае успеха

### Локальный запуск проекта:

**_Склонировать репозиторий к себе_**
```
git@github.com:Resurection1/foodgram.git
```

**_В общей директории файл .env.example переименовать в .env и заполнить своими данными:_**
```
POSTGRES_DB='postgres'
POSTGRES_USER='postgres'
POSTGRES_PASSWORD='postgres'
DB_NAME='postgres'
DB_HOST=db
DB_PORT=5432
DEBUG=False
SECRET_KEY= # django secret key
ALLOWED_HOSTS='localhost,127.0.0.1,domain,ip'
DATABASES=postgresql
DOMAIN = ''
```

**_Создать и запустить контейнеры Docker, как указано выше._**

**После запуска проект будут доступен по адресу: http://localhost/**

**Документация будет доступна по адресу: http://localhost/api/docs/**


### Автор
[Podzorov Mihail] - https://github.com/Resurection1