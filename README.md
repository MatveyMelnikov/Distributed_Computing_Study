# Distributed Computing Study

## About

Учебный проект по дисциплине "Построение распределенных систем и облачные вычисления"

## Start

* Установка зависимостей:
```pip install -r requirements.txt```
* Запуск и конфигурация БД:
```
mysql -u root -p \
CREATE DATABASE numbers; \
CREATE USER 'app_user'@'localhost' IDENTIFIED BY '1234'; \
GRANT ALL PRIVILEGES ON numbers.* TO 'app_user'@'localhost'; \
FLUSH PRIVILEGES; \
\q
```
* Запуск app server:
```
python3 app_server.py \
    --db-url mysql://app_user:1234@127.0.0.1:3306/numbers \
    --host 127.0.0.1 \
    --port 8001
```
* Запуск web server:
```
python web_server.py \
    --app-url http://127.0.0.1:8001/ \
    --host 127.0.0.1 --port 8000
```

Обращение к web server: ```curl -s -X POST http://127.0.0.1:8000/ -d '{"number": 5}'```
