from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, List
import yaml
import os
from pathlib import Path

app = FastAPI()

# Подключение шаблонов
templates = Jinja2Templates(directory="templates")

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/covers", StaticFiles(directory="tracks/covers"), name="covers")

# Путь к YAML файлу с данными треков
TRACKS_YAML_PATH = Path("tracks/data.yaml")
COVERS_DIR = Path("tracks/covers")

# Поддерживаемые форматы изображений для обложек
COVER_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp", ".PNG", ".JPG", ".JPEG", ".WEBP"]

# Дефолтный исполнитель
DEFAULT_ARTIST = "meowthpxnk"


def load_tracks_data() -> Dict:
    """Загружает данные из YAML файла"""
    if not TRACKS_YAML_PATH.exists():
        return {"tracks": [], "global_platforms": {}}

    with open(TRACKS_YAML_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return {
            "tracks": data.get("tracks", []),
            "global_platforms": data.get("global_platforms", {})
        }


def load_tracks() -> List:
    """Загружает список треков из YAML файла"""
    data = load_tracks_data()
    return data.get("tracks", [])


def get_global_platforms() -> Dict:
    """Возвращает глобальные ссылки на платформы"""
    data = load_tracks_data()
    return data.get("global_platforms", {})


def find_cover_file(track_id: str) -> Optional[str]:
    """Ищет файл обложки по ID трека с разными расширениями"""
    for ext in COVER_EXTENSIONS:
        cover_path = COVERS_DIR / f"{track_id}{ext}"
        if cover_path.exists():
            return f"{track_id}{ext}"
    return None


def get_tracks_data() -> Dict[str, Dict]:
    """Возвращает словарь треков по ID"""
    tracks = load_tracks()
    tracks_dict = {}

    for track in tracks:
        track_id = track.get("id")
        cover_file = find_cover_file(track_id)

        # Формируем URL обложки
        if cover_file:
            cover_url = f"/covers/{cover_file}"
            has_cover = True
        else:
            cover_url = "https://via.placeholder.com/500x500"
            has_cover = False

        # Объединяем платформы трека с глобальными (приоритет у ссылок трека)
        global_platforms = get_global_platforms()
        track_platforms = track.get("platforms", {})
        merged_platforms = {}

        for platform_key in ["vk", "yandex_music", "spotify", "apple_music", "youtube_music"]:
            # Используем ссылку трека, если она есть, иначе глобальную
            merged_platforms[platform_key] = (
                track_platforms.get(platform_key, "") or
                global_platforms.get(platform_key, "")
            )

        tracks_dict[track_id] = {
            "title": track.get("title", ""),
            "artist": DEFAULT_ARTIST,
            "cover_url": cover_url,
            "has_cover": has_cover,
            "track_url": track.get("track_url", ""),
            "description": track.get("description", ""),
            "platforms": merged_platforms
        }

    return tracks_dict


def get_tracks_list() -> List[Dict]:
    """Возвращает список треков для главной страницы в обратном порядке"""
    tracks = load_tracks()
    tracks_list = []

    for track in tracks:
        track_id = track.get("id")
        cover_file = find_cover_file(track_id)

        # Формируем URL обложки
        if cover_file:
            cover_url = f"/covers/{cover_file}"
            has_cover = True
        else:
            cover_url = ""
            has_cover = False

        tracks_list.append({
            "id": track_id,
            "title": track.get("title", ""),
            "artist": DEFAULT_ARTIST,
            "cover_url": cover_url,
            "has_cover": has_cover
        })

    # Возвращаем список в обратном порядке
    return list(reversed(tracks_list))


class Track(BaseModel):
    title: str
    artist: str
    cover_url: str
    track_url: str
    description: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def tracks_list(request: Request):
    """Главная страница со списком треков"""
    tracks = get_tracks_list()
    return templates.TemplateResponse("tracks_list.html", {
        "request": request,
        "tracks": tracks
    })


@app.get("/{track_id}", response_class=HTMLResponse)
async def track_page(request: Request, track_id: str):
    """Страница конкретного трека"""
    tracks_data = get_tracks_data()
    track_data = tracks_data.get(track_id)
    global_platforms = get_global_platforms()

    if not track_data:
        return templates.TemplateResponse("404.html", {
            "request": request,
            "track_id": track_id
        }, status_code=404)

    return templates.TemplateResponse("track_page.html", {
        "request": request,
        "track": track_data,
        "global_platforms": global_platforms
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
