# Инструкция по запуску через Docker Compose

## Быстрый старт

1. **Подготовьте папку tracks:**
   ```
   tracks/
   ├── data.yaml          # Файл с данными о треках
   └── covers/            # Папка с обложками
       ├── holodno.png
       ├── posledniy_tanec.png
       └── ...
   ```

2. **Запустите сервис:**
   ```bash
   docker-compose up -d
   ```

3. **Откройте в браузере:**
   http://localhost:8000

## Управление сервисом

- **Запуск:** `docker-compose up -d`
- **Остановка:** `docker-compose down`
- **Перезапуск:** `docker-compose restart`
- **Просмотр логов:** `docker-compose logs -f`
- **Остановка и удаление:** `docker-compose down -v`

## Добавление новых треков

1. Добавьте трек в `tracks/data.yaml`
2. Поместите обложку в `tracks/covers/` с именем `{id_трека}.png` (или .jpg, .jpeg, .webp)
3. Перезапустите контейнер:
   ```bash
   docker-compose restart
   ```

## Структура data.yaml

```yaml
global_platforms:
  telegram_channel: https://t.me/...
  vk: https://vk.com/...
  twitch: https://www.twitch.tv/...
  youtube: https://www.youtube.com/...

tracks:
  - id: название_трека
    title: Название трека
    platforms:
      vk: https://...
      yandex_music: https://...
      spotify: https://...
      apple_music: https://...
      youtube_music: https://...
```

## Важно

- Папка `tracks` монтируется как volume, поэтому изменения применяются без пересборки образа
- Файл обложки должен называться по `id` трека (например, `holodno.png` для трека с `id: holodno`)
- Поддерживаемые форматы обложек: `.png`, `.jpg`, `.jpeg`, `.webp` (включая заглавные варианты)
