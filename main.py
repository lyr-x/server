import fastapi
import os
import aiohttp
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from parser import track, add_view, lyrx_to_json, stats, parse_metadata, get_viewmap
import parser
from urllib.parse import quote
from search import search, all_tracks
__import__("dotenv").load_dotenv()
app = FastAPI()
dev = True

def get_author_pfp(author_id: str):
    pfp_path = os.path.join("profiles", f"{author_id}.png")
    return pfp_path if os.path.isfile(pfp_path) else None
  

@app.get("/")
async def root():
    return {
        "runtime":f"running FastAPI {fastapi.__version__}",
        "documentation":"https://lyrx.tjf1.dev/developers"
    }

#TODO make the routes more clear
@app.get("/api/track/{track_id}/")
async def track_api(track_id: str):
    tr = track(track_id)
    if not tr:
        return "not found", 404
    else:
        return fastapi.Response(tr, media_type="text/plain")
    
@app.get("/api/track/{track_id}/json")
async def track_api_json(track_id: str):
    tr = track(track_id)
    add_view(track_id)
    if not tr:
        return "not found", 404
    else:
        json = lyrx_to_json(tr.splitlines())
        return json

@app.get("/api/statistics")
async def stats_api():
    stats = parser.stats()
    stats["dev"] = dev
    return stats


@app.get("/api/search")
async def search_api(q: str =  ""):
    res = search(q)
    return res

@app.get("/api/track/{track_id}/meta")
async def track_api_meta(track_id: str):
    tr = track(track_id)
    if not tr:
        return {"error":"track {track_id} not found"}
    else:
        meta = parse_metadata(tr.splitlines())
        meta["artists"] = meta["artist"].split("|")
        meta["views"] = get_viewmap().get(f"{track_id}", 0)
        return meta


@app.get("/api/track/{track_id}/lastfm/album")
async def album_lastfm_api(track_id: str):
    try:
        tr = track(track_id)
        if not tr:
            return "not found", 404

        data = parse_metadata(tr)
        artist = data["artist"].split("|")[0]
        album = data["album"]
        artist_encoded = quote(artist)
        album_encoded = quote(album)

        url = f"http://ws.audioscrobbler.com/2.0/?method=album.getInfo"
        f"&album={album_encoded}&artist={artist_encoded}"
        f"&api_key={os.getenv('LASTFM_API_KEY')}&format=json"
        

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                json_data = await resp.json()

        if "album" not in json_data:
            return {
                "error": f"Album '{album}' by '{artist}' not found on Last.fm",
                "lastfm": json_data,
            }

        images = json_data["album"].get("image", [])
        preferred_sizes = ["extralarge", "large", "medium", "small"]
        image_url = "unknown"

        for size in preferred_sizes:
            match = next(
                (img for img in images if img.get("size") == size and img.get("#text")),
                None,
            )
            if match:
                image_url = match["#text"]
                break

        resp = {
            "title": json_data["album"].get("name", "unknown"),
            "artist": json_data["album"].get("artist", "unknown"),
            "image": image_url,
            "tracks": json_data["album"].get("tracks", {}).get("track", []),
        }
        return resp

    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
    
@app.get("/api/author/{track_id}/avatar")
async def author_profile_api(track_id: str):
    if track_id == None:
        return "unknown author", 404
    pfp = get_author_pfp(track_id)
    if pfp:
        return fastapi.responses.FileResponse(pfp, media_type="image/png")
    else:
        return "no profile picture found", 404

@app.get("/favicon.ico")
def favicon():
    path = os.path.abspath("lyrX.png")
    if not os.path.exists(path):
        return "not found", 404
    return fastapi.responses.FileResponse(path, media_type="image/png")