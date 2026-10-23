# Развёртывание через Docker Compose

Команды выполняются из корня репозитория в ветке `production`. На сервере нужны
Docker Engine с Linux-контейнерами, Docker Compose v2.24+ и Git. Node.js, Python
и uv на хост устанавливать не нужно.

## Первый запуск

```bash
git clone --branch production YOUR_REPOSITORY_URL dio.ai-chats
cd dio.ai-chats
cp .env.example .env
chmod 600 .env
nano .env
```

При работе с локальной веткой сначала отправьте её в свой Git-репозиторий.
Не копируйте поверх существующего `.env` при обновлении сервера.

Все production-настройки находятся в **корневом `.env`**. Локальные файлы
`.backend.env`, `.frontend.env` и `.env` внутри каталогов приложений этот Compose
не читает; необходимые значения из них перенесите вручную. Эти файлы не попадают
в Git или Docker-образы. Пример backend `.env` внутри `ai-chats.backend` относится
к запуску backend непосредственно на хосте.

Обязательно заполните:

| Переменная | Что указать |
| --- | --- |
| `MONGO_PASSWORD` | Случайный пароль MongoDB |
| `REDIS_PASSWORD` | Другой случайный пароль Redis |
| `IAM_BASE_URL` | Адрес существующего IAM, например `https://iam.example.com`, без пути и завершающего `/` |
| `IAM_DEFAULT_ORGANIZATION_ID` | Постоянный UUID организации |
| `SECRETS_MASTER_KEY` | Base64 от 32 случайных байт |

Генерация для **новой** установки:

```bash
openssl rand -hex 32       # MONGO_PASSWORD
openssl rand -hex 32       # REDIS_PASSWORD
openssl rand -base64 32    # SECRETS_MASTER_KEY
cat /proc/sys/kernel/random/uuid  # IAM_DEFAULT_ORGANIZATION_ID, если UUID ещё нет
```

При переносе данных сохраните прежние master key и UUID организации. Без прежнего
ключа невозможно расшифровать сохранённые API-ключи. Используйте прежнее имя базы
в `MONGO_DB`, если восстанавливаете существующие данные.

Одна команда собирает и запускает весь стек:

```bash
docker compose up -d --build --wait
```

По умолчанию приложение доступно на сервере по `http://127.0.0.1:8080`.
Для просмотра с компьютера без публикации HTTP наружу можно открыть SSH-туннель:

```bash
ssh -L 8080:127.0.0.1:8080 USER@SERVER
```

После этого откройте `http://localhost:8080`. Для прямого HTTP-доступа из сети
можно задать `HTTP_BIND=0.0.0.0` и нужный `HTTP_PORT`. Для публичного рабочего
сервиса настройте HTTPS, как описано ниже.

## Что запускается

- `frontend`: React собирается в Node.js, результат обслуживает Nginx.
- `backend`: Python 3.14, зависимости из `uv.lock`, Uvicorn под непривилегированным пользователем.
- `mongo`: постоянное хранилище в именованном томе `mongo-data`.
- `redis`: постоянный том `redis-data`; текущий runtime backend пока использует кэш в памяти.

MongoDB, Redis и backend не публикуют порты хоста. Backend подключается к
`mongo:27017`, а не к `localhost`. Compose ждёт готовности MongoDB перед стартом
backend и готовности backend перед стартом frontend. Healthcheck backend
подтверждает запуск HTTP-приложения, но не проверяет доступность IAM или моделей.

Имена томов имеют префикс проекта `dio-ai-chats`. Это новые тома: данные из
старого Compose в `ai-chats.backend` автоматически не переносятся.

## IAM и модели

IAM DIO desk — внешний сервис, в этом репозитории его нет. Он должен обслуживать
`/api/v1/auth/login`, `/refresh`, `/logout` и `/userinfo` под общим префиксом
`/api/v1/auth`. Backend ожидает в userinfo поля `id`, `email`, `roles`.
Для управления подключениями моделей нужна роль `admin`.

`IAM_BASE_URL` используется одновременно backend и Nginx. `127.0.0.1` внутри
контейнера означает сам контейнер. Для IAM на хосте можно использовать:

```dotenv
IAM_BASE_URL=http://host.docker.internal:8001
```

На Linux IAM должен слушать интерфейс, доступный из Docker bridge, а firewall
должен пропускать соединения с этой сети. IAM, слушающий только host loopback
`127.0.0.1`, через host-gateway недоступен. Если IAM находится в другом Compose,
используйте его доступный адрес или подключите сервисы к общей Docker-сети.

Для HTTPS IAM Nginx проверяет сертификат по системным CA. Для корпоративного CA
потребуется добавить доверенный сертификат в образы обоих приложений. После
изменения IP IAM при неизменном DNS-имени перезапустите frontend для обновления
адреса в Nginx: `docker compose restart frontend`.

API-ключи моделей добавляются через интерфейс подключений приложения, а не
через `VITE_*`. Создание `.env` само по себе не добавляет модели.

## Frontend и Nginx

В браузере используются относительные пути `/auth-api` и `/chats-api`.
Nginx удаляет соответствующий префикс и пересылает запрос в IAM или backend.
Буферизация ответов отключена для потоковой генерации. Docker DNS используется
для повторного поиска backend при замене его контейнера.

`VITE_TRUSTED_ORIGINS` — необязательный список доверенных origin через запятую,
например `https://desk.example.com,https://docs.example.com`. Он влияет на
предупреждения при переходе по ссылкам в ответах модели. Значение публичное и
встраивается в сборку; после изменения нужна пересборка frontend.

Внутренняя конфигурация: `ai-chats.frontend/nginx/default.conf.template`.
Официальный entrypoint Nginx подставляет только `IAM_BASE_URL`; переменные
Nginx вроде `$host` и `$uri` сохраняются.

## HTTPS на сервере

По умолчанию Compose публикует HTTP только на `127.0.0.1:8080`, чтобы его можно
было поставить за существующий TLS reverse proxy. Все приложения при этом
по-прежнему запускаются одной командой Compose. Сертификат и внешний proxy
настраиваются отдельно для вашего домена.

Пример конфигурации внешнего Nginx: `deploy/nginx/https.conf.example`.
Замените домен и пути к **уже выпущенным** сертификатам, установите конфигурацию
в ваш host Nginx, выполните `sudo nginx -t` и `sudo systemctl reload nginx`.
Откройте порты 80/443 и настройте DNS. Если меняете `HTTP_PORT`, измените также
порт upstream во внешней конфигурации. Она тоже отключает буферизацию SSE.

## Проверка и диагностика

```bash
docker compose config --quiet
docker compose ps
docker compose logs --tail=100 backend frontend
curl -fsS http://127.0.0.1:8080/healthz
curl -fsS http://127.0.0.1:8080/chats-api/openapi.json
curl -i http://127.0.0.1:8080/auth-api/api/v1/auth/userinfo
```

Последний запрос без токена обычно возвращает `401`. `502` означает проблему
с upstream, `404` — возможную ошибку адреса/маршрута IAM. Проверка `/healthz`
проверяет только Nginx; отдельно проверьте вход, создание подключения и
потоковый ответ модели. Вход и генерация требуют работающих внешних сервисов.

Не публикуйте вывод `docker compose config` без `--quiet`: он содержит секреты.

Сборка требует сетевого доступа к npm, PyPI, Docker registry и GitHub.
`py-ddd-framework` устанавливается по Git revision из `uv.lock`. Если репозиторий
закрыт, настройте доступ через BuildKit SSH/secret mount; не записывайте токены
в Dockerfile, build args или URL в lock-файле.

В production-ветке зафиксирована ревизия `e2948543` этой библиотеки: прежняя
ревизия `8aa2fea6` падала при импорте отсутствующего `ddf.application.dsl.sorting`.
Dockerfile дополнительно проверяет импорт приложения во время сборки.

## Обновление и данные

Перед обновлением сделайте резервную копию MongoDB и сохраните master key
отдельно от сервера. Пример резервной копии из Bash, из корня проекта:

```bash
mkdir -p backups
chmod 700 backups
docker compose exec -T mongo sh -c 'exec mongodump --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --archive --gzip' > "backups/mongo-$(date +%Y%m%d-%H%M%S).archive.gz"
```

Проверяйте код завершения команды и периодически проверяйте восстановление
резервной копии в отдельную базу.

Обновление:

```bash
git pull --ff-only origin production
docker compose up -d --build --wait
docker compose ps
```

Изменения `.env` применяются через `up`, простой `restart` не обновляет окружение.
Смена `MONGO_PASSWORD` в `.env` не меняет пароль в уже созданном томе MongoDB —
его нужно менять согласованно в самой базе. При смене master key потребуется
отдельная процедура перешифрования, которой в этом проекте пока нет.

```bash
docker compose logs -f backend frontend  # логи
docker compose stop                     # остановка с сохранением контейнеров
docker compose down                     # удаление контейнеров, тома сохраняются
```

**Не используйте `docker compose down -v` для обновления:** флаг `-v` удаляет
тома с данными. Не меняйте имя Compose-проекта без плана переноса томов.

## Результат проверки этой конфигурации

Оба образа собраны, все четыре сервиса прошли healthcheck. Проверены отдача
frontend, оба префикса reverse proxy, `401` без access token и `404` для
отсутствующего asset. В тесте upstream IAM был заменён тестовым HTTP-сервисом
(самим backend); вход в реальный IAM и генерация модели не проверялись.

При проверке 23.10.2026 `npm audit --omit=dev` сообщил об одной критической
уязвимости в транзитивной зависимости `dompurify` и семи низкой серьёзности.
Это существующий frontend lock-файл; в рамках настройки Docker зависимости
frontend не обновлялись. Перед публичным развёртыванием требуется отдельное
обновление и проверка зависимостей frontend.
