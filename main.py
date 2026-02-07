from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, List
import yaml
import os
import shutil
from pathlib import Path

# Определяем базовую директорию в самом начале
BASE_DIR = Path(__file__).parent

app = FastAPI()

# Подключение шаблонов
templates = Jinja2Templates(directory="templates")

# Путь к YAML файлу с данными треков
TRACKS_YAML_PATH = BASE_DIR / "tracks" / "data.yaml"
COVERS_DIR = BASE_DIR / "tracks" / "covers"

# Подключение статических файлов
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/covers", StaticFiles(directory=str(COVERS_DIR)), name="covers")

# Поддерживаемые форматы изображений для обложек
COVER_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp", ".PNG", ".JPG", ".JPEG", ".WEBP"]

# Дефолтный исполнитель
DEFAULT_ARTIST = "meowthpxnk"

# Создаем папку для обложек если её нет
COVERS_DIR.mkdir(parents=True, exist_ok=True)


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
    if not COVERS_DIR.exists():
        return None

    for ext in COVER_EXTENSIONS:
        cover_path = COVERS_DIR / f"{track_id}{ext}"
        if cover_path.exists() and cover_path.is_file():
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

        # Используем только ссылки трека, без глобальных
        track_platforms = track.get("platforms", {})
        merged_platforms = {}

        for platform_key in ["vk", "yandex_music", "spotify", "apple_music", "youtube_music"]:
            # Используем только ссылку трека, если она есть
            track_link = track_platforms.get(platform_key, "")
            if track_link and track_link.strip():
                merged_platforms[platform_key] = track_link.strip()

        # Пропускаем отключенные треки
        if not track.get("enabled", True):
            continue

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
    """Возвращает список треков для главной страницы в обратном порядке (только включенные)"""
    tracks = load_tracks()
    tracks_list = []

    for track in tracks:
        # Пропускаем отключенные треки
        if not track.get("enabled", True):
            continue

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


def save_tracks_data(data: Dict):
    """Сохраняет данные треков в YAML файл"""
    with open(TRACKS_YAML_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


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


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Админ панель для управления треками"""
    tracks = load_tracks()
    # Добавляем информацию об обложках для каждого трека
    tracks_with_covers = []
    for track in tracks:
        track_id = track.get("id")
        if not track_id:
            continue

        cover_file = find_cover_file(track_id)
        if cover_file:
            cover_url = f"/covers/{cover_file}"
            has_cover = True
        else:
            cover_url = None
            has_cover = False

        track_data = {
            **track,
            "cover_url": cover_url,
            "has_cover": has_cover
        }
        tracks_with_covers.append(track_data)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "tracks": tracks_with_covers
    })


@app.get("/api/tracks", response_class=JSONResponse)
async def api_get_tracks(request: Request):
    """API: Получить список всех треков"""
    tracks = load_tracks()
    return {"tracks": tracks}


@app.get("/api/tracks/{track_id}", response_class=JSONResponse)
async def api_get_track(request: Request, track_id: str):
    """API: Получить конкретный трек"""
    tracks = load_tracks()
    track = next((t for t in tracks if t.get("id") == track_id), None)

    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    return {"track": track}


@app.post("/api/tracks", response_class=JSONResponse)
async def api_create_track(
    request: Request,
    track_id: str = Form(...),
    title: str = Form(...),
    vk: str = Form(""),
    yandex_music: str = Form(""),
    spotify: str = Form(""),
    apple_music: str = Form(""),
    youtube_music: str = Form(""),
    cover_file: Optional[UploadFile] = File(None)
):
    """API: Создать новый трек"""
    data = load_tracks_data()
    tracks = data.get("tracks", [])

    # Проверяем, не существует ли уже трек с таким ID
    if any(t.get("id") == track_id for t in tracks):
        raise HTTPException(status_code=400, detail="Track with this ID already exists")

    # Сохраняем обложку если загружена
    if cover_file and cover_file.filename:
        file_ext = Path(cover_file.filename).suffix
        if file_ext.lower() in [ext.lower() for ext in COVER_EXTENSIONS]:
            cover_path = COVERS_DIR / f"{track_id}{file_ext}"
            with open(cover_path, "wb") as buffer:
                shutil.copyfileobj(cover_file.file, buffer)

    # Создаем новый трек
    new_track = {
        "id": track_id,
        "title": title,
        "enabled": False,
        "platforms": {
            "vk": vk,
            "yandex_music": yandex_music,
            "spotify": spotify,
            "apple_music": apple_music,
            "youtube_music": youtube_music
        }
    }

    tracks.append(new_track)
    data["tracks"] = tracks
    save_tracks_data(data)

    return {"success": True, "track": new_track}


@app.put("/api/tracks/{track_id}", response_class=JSONResponse)
async def api_update_track(
    request: Request,
    track_id: str,
    title: str = Form(...),
    vk: str = Form(""),
    yandex_music: str = Form(""),
    spotify: str = Form(""),
    apple_music: str = Form(""),
    youtube_music: str = Form(""),
    track_id_new: Optional[str] = Form(None),
    cover_file: Optional[UploadFile] = File(None)
):
    """API: Обновить трек"""
    data = load_tracks_data()
    tracks = data.get("tracks", [])

    # Ищем трек
    track_index = next((i for i, t in enumerate(tracks) if t.get("id") == track_id), None)
    if track_index is None:
        raise HTTPException(status_code=404, detail="Track not found")

    # Если ID изменился, проверяем что новый ID не занят
    track_id_new = track_id_new.strip() if track_id_new else track_id

    # Если track_id_new не передан, используем старый
    if not track_id_new:
        track_id_new = track_id

    if track_id_new != track_id:
        # Проверяем, что новый ID не занят другим треком
        existing_track = next((t for t in tracks if t.get("id") == track_id_new and t.get("id") != track_id), None)
        if existing_track:
            raise HTTPException(status_code=400, detail="Track with this ID already exists")

        # Переименовываем файл обложки если он существует
        old_cover = find_cover_file(track_id)
        if old_cover:
            old_cover_path = COVERS_DIR / old_cover
            if old_cover_path.exists():
                # Определяем расширение старого файла
                old_ext = Path(old_cover).suffix
                new_cover_path = COVERS_DIR / f"{track_id_new}{old_ext}"
                old_cover_path.rename(new_cover_path)

    # Сохраняем новую обложку если загружена
    if cover_file and cover_file.filename:
        file_ext = Path(cover_file.filename).suffix
        if file_ext.lower() in [ext.lower() for ext in COVER_EXTENSIONS]:
            # Удаляем старые обложки с разными расширениями
            for ext_check in COVER_EXTENSIONS:
                old_cover_path = COVERS_DIR / f"{track_id_new}{ext_check}"
                if old_cover_path.exists():
                    old_cover_path.unlink()

            cover_path = COVERS_DIR / f"{track_id_new}{file_ext}"
            with open(cover_path, "wb") as buffer:
                shutil.copyfileobj(cover_file.file, buffer)

    # Обновляем трек с новым ID (сохраняем enabled статус)
    old_enabled = tracks[track_index].get("enabled", True)
    tracks[track_index] = {
        "id": track_id_new,
        "title": title,
        "enabled": old_enabled,
        "platforms": {
            "vk": vk,
            "yandex_music": yandex_music,
            "spotify": spotify,
            "apple_music": apple_music,
            "youtube_music": youtube_music
        }
    }

    data["tracks"] = tracks
    save_tracks_data(data)

    return {"success": True, "track": tracks[track_index]}


@app.patch("/api/tracks/{track_id}/toggle", response_class=JSONResponse)
async def api_toggle_track(request: Request, track_id: str, enabled: bool = Form(...)):
    """API: Включить/выключить трек"""
    data = load_tracks_data()
    tracks = data.get("tracks", [])

    # Ищем трек
    track_index = next((i for i, t in enumerate(tracks) if t.get("id") == track_id), None)
    if track_index is None:
        raise HTTPException(status_code=404, detail="Track not found")

    # Обновляем статус трека
    tracks[track_index]["enabled"] = enabled
    data["tracks"] = tracks
    save_tracks_data(data)

    return {"success": True, "enabled": enabled}


@app.delete("/api/tracks/{track_id}", response_class=JSONResponse)
async def api_delete_track(request: Request, track_id: str):
    """API: Удалить трек"""
    data = load_tracks_data()
    tracks = data.get("tracks", [])

    # Ищем и удаляем трек
    tracks = [t for t in tracks if t.get("id") != track_id]
    data["tracks"] = tracks
    save_tracks_data(data)

    # Удаляем обложку если есть
    for ext in COVER_EXTENSIONS:
        cover_path = COVERS_DIR / f"{track_id}{ext}"
        if cover_path.exists():
            cover_path.unlink()
            break

    return {"success": True}


@app.get("/{track_id}", response_class=HTMLResponse)
async def track_page(request: Request, track_id: str):
    """Страница конкретного трека"""
    # Проверяем, не пытаются ли зайти на dashboard через этот роут
    if track_id == "dashboard":
        return await dashboard(request)

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
