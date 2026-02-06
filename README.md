# MusicLink - FastAPI музыкальное приложение

Простое FastAPI приложение для отображения музыкальных треков с HTML шаблонами.

## Структура проекта

```
musiclink/
├── main.py              # FastAPI приложение
├── requirements.txt     # Зависимости Python
├── Dockerfile          # Docker конфигурация
├── templates/          # HTML шаблоны
│   ├── tracks_list.html
│   ├── track_page.html
│   └── 404.html
└── static/            # Статические файлы (CSS, JS, изображения)
```

## Запуск локально

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Запустите приложение:
```bash
python main.py
```

Или через uvicorn:
```bash
uvicorn main:app --reload
```

Приложение будет доступно по адресу: http://localhost:8000

## Запуск в Docker (рекомендуется)

### Использование docker-compose

1. Поместите ваши треки в папку `tracks/`:
   - `tracks/data.yaml` - файл с данными о треках
   - `tracks/covers/` - папка с обложками (название файла = id трека, например `holodno.png`)

2. Запустите сервис:
```bash
docker-compose up -d
```

3. Остановите сервис:
```bash
docker-compose down
```

4. Просмотр логов:
```bash
docker-compose logs -f
```

Приложение будет доступно по адресу: http://localhost:8000

**Важно:** Папка `tracks` монтируется как volume, поэтому вы можете добавлять/изменять треки без пересборки образа. Просто перезапустите контейнер:
```bash
docker-compose restart
```

### Запуск без docker-compose

1. Соберите образ:
```bash
docker build -t musiclink .
```

2. Запустите контейнер с монтированием папки tracks:
```bash
docker run -p 8000:8000 -v ./tracks:/app/tracks musiclink
```

## Маршруты

- `/` - Список всех треков
- `/posledniy_tanec` - Страница конкретного трека
- `/{track_id}` - Страница любого трека по ID

## Настройка данных

Данные о треках находятся в файле `main.py` в словарях `TRACKS_DATA` и `TRACKS_LIST`. Вы можете изменить их или подключить базу данных.
