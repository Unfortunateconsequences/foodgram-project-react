# Проект Foodgram

[Foodgram](https://theamazingfoodgram.sytes.net/) - сервис публикации рецептов.

Доступные функции:

* Регистрация и авторизация новых пользователей
* Создание, редактирование и удаление рецептов
* Добавление и удаление рецептов в/из избранного
* Подписка/отписка на/от понравившихся авторов
* Добавление ингредиентов рецепта в/из корзины
* Скачивание списка покупок из корзины


## Подготовка и запуск проекта
### Склонировать репозиторий на локальную машину:

```
git clone https://github.com/unf0rtunate/foodgram-project-react
```

## Для работы с удаленным сервером (на ubuntu):
* Выполните вход на свой удаленный сервер

* Установите docker на сервер:

```
sudo apt install docker.io 
```

* Установите docker-compose на сервер:

```
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

* Локально отредактируйте файл infra/nginx.conf, в строке server_name впишите свой IP
* Скопируйте файлы docker-compose.yml и nginx.conf из директории infra на сервер:

```
scp docker-compose.yml <username>@<host>:/home/<username>/docker-compose.yml
scp nginx.conf <username>@<host>:/home/<username>/nginx.conf
```

* Cоздайте и заполните .env файл (замените все, что закрыто <>):

    ```
    FOODGRAM_SECRET = <Ваш Django SECRET_KEY>
    FOODGRAM_DEBUG = <True/False>
    FOODGRAM_HOSTS = <Ваши IP - адрес и ссылка на хостинг>
    FOODGRAM_CSRF = <https://*<ваша-ссылка (обязательно со звездочкой после //)>
    POSTGRES_USER = <Пользователь БД>
    POSTGRES_PASSWORD = <Пароль пользователя БД>
    POSTGRES_DB = <Название БД>
    DB_HOST = db
    DB_PORT = 5432
    ```  
  
* На сервере соберите docker-compose:

```
sudo docker-compose up -d --build
```

* После успешной сборки на сервере выполните команды (только после первого деплоя):
    - Соберите статические файлы:

    ```
    sudo docker-compose exec backend python manage.py collectstatic --noinput
    ```
    
    - Примените миграции:
    
    ```
    sudo docker-compose exec backend python manage.py migrate --noinput
    ```
    
    - Загрузите ингридиенты  в базу данных (кнопка 'импорт' доступна через админ-панель):  
    
    - Создать суперпользователя Django:
    
    ```
    sudo docker-compose exec backend python manage.py createsuperuser
    ```
    
    - Проект будет доступен по вашему IP

## Проект в интернете

Проект запущен и доступен по указанному адресу.