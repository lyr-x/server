import os, difflib, time, readchar, requests, json


def split_artists(artists: str) -> list:
    return artists.split("|")


def parse_metadata(lines: list | str, single_artist: bool = False) -> dict:
    if isinstance(lines, str):
        lines = lines.splitlines()
    data = {}
    for l in lines:
        ls = l.split(";")
        if not l[0].isdigit():
            try:
                key = ls[0].lower()
                value = ls[1]
                if single_artist and key == "artist" and len(value.split("|")) > 1:
                    value = value.split("|")[0]
                data[key] = value.strip("\n")
            except (IndexError, KeyError):
                continue
        else:
            continue
    try:
        data["views"] = get_viewmap()[data["id"]]
    except Exception:
        data["views"] = 0
    return data


def get_viewmap() -> dict:
    if not os.path.exists("viewmap.json"):
        return {}
    try:
        with open("viewmap.json", "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def set_viewmap(map: dict) -> None:
    with open("viewmap.json", "w") as f:
        return json.dump(map, f, indent=4)
    print(f"writted viewmap: {map}")


def add_view(id: str) -> int:
    """
    Adds a view to a track, returns the view count.
    """
    meta = get_viewmap()
    cur = meta.get(f"{id}", 0)
    meta[f"{id}"] = cur + 1
    print(f"{id} has {cur+1} views now.")
    print(f"viewmap path: {os.path.abspath('viewmap.json')}")
    set_viewmap(meta)
    return cur + 1


def post_about_all_tracks():
    output_folder = "lyrics"
    files = os.listdir("lyrics")
    lyrx_files = []
    for f in files:
        if f.endswith(".lyrx"):
            lyrx_files.append(f)
    tracks = []

    for lyrx_file in lyrx_files:
        with open(f"lyrics/{lyrx_file}", "r") as f:
            content = f.read()
            lines = content.splitlines()
            print(content)
            metadata = parse_metadata(content)

            try:
                print(metadata)
                tracks.append(
                    {
                        "id": lyrx_file.split(".")[0],
                        "title": metadata["title"],
                        "artist": metadata["artist"],
                        "author": metadata["author"],
                        "album": metadata.get("album", metadata["title"]),
                    }
                )
            except Exception as e:
                print(f"in {lyrx_file}: {type(e)}: {e}")
    tracks.sort(key=lambda x: x["id"])
    for track in tracks:
        post_webhook(
            track["id"],
            track["title"],
            track["artist"],
            track["author"],
            track["album"],
        )


def post_webhook(
    id, title, artist, author, album, webhook_url=os.getenv("WEBHOOK_NEW_TRACK")
):
    embed = {
        "title": "New Track Added",
        "color": 0xD175FF,
        "fields": [
            {"name": "ID", "value": id, "inline": False},
            {"name": "Title", "value": title, "inline": True},
            {"name": "Artist", "value": artist, "inline": True},
            {"name": "Album", "value": album, "inline": True},
            {"name": "Author", "value": author, "inline": False},
        ],
    }

    payload = {"content": "<@&1355123833014845440>", "embeds": [embed]}
    requests.post(webhook_url, json=payload)


def parse_metadata_v2(file: str) -> dict:
    data = {}
    lines = file.splitlines()
    for l in lines:
        if l.startswith("["):
            tagl = l.strip("[]")
            tagl = tagl.replace("]", "")
            ls = tagl.split(" ")
            data[ls[0].lower()] = ls[1:]
    return data


def parse_metadata_v1(lines) -> dict:
    metadata = {}
    for line in lines:
        line = line.strip()
        if line.startswith("[TITLE]"):
            metadata["title"] = line.replace("[TITLE]", "").strip()
        elif line.startswith("[ARTIST]"):
            metadata["artist"] = line.replace("[ARTIST]", "").strip()
        elif line.startswith("[AUTHOR]"):
            metadata["author"] = line.replace("[AUTHOR]", "").strip()
        elif line.startswith("[ARTIST_ID]"):
            metadata["artist_id"] = line.replace("[ARTIST_ID]", "").strip()
        elif line.startswith("[ALBUM]"):
            metadata["album"] = line.replace("[ALBUM]", "").strip()
        elif line.startswith("[DURATION]"):
            metadata["duration"] = line.replace("[DURATION]", "").strip()
    return metadata


def lyrx_to_json(lines):
    lyrics = {}
    for line in lines:
        if line.split(";")[0].isdigit():
            timestamp, lyric = line.split(";", 1)
            lyrics[int(timestamp)] = lyric.strip()
    return lyrics


def stats():
    data = {"tracks": len(os.listdir("lyrics")), "version": os.getenv("VERSION")}
    return data


def parse_lyrics(file_path: str) -> list:
    return lyrics_lyrx_to_list(file_path)


def lines_to_list(lines: list) -> list:
    lyrics = []
    for line in lines:
        if line and line[0].isdigit():
            time_ms, lyric = line.split(";")
            lyrics.append((int(time_ms), lyric.strip()))
    return lyrics


def lyrics_lines_to_dict(lines: list) -> dict:
    lyrics = {}
    for line in lines:
        if line and line[0].isdigit():
            time_ms = line.split(";")[0]
            lyric = "".join(line.split(";")[1:])
            lyrics[int(time_ms)] = lyric.strip()
    return lyrics


def lyrics_lyrx_to_list(file_path: str):
    lyrics = []
    with open(file_path, encoding="utf-8") as file:
        lines = file.read().splitlines()
        for line in lines:
            if line and line[0].isdigit():
                time_ms, lyric = line.split(";")
                lyrics.append((int(time_ms), lyric.strip()))
    return lyrics


def track(id: str):
    file_path = os.path.join("lyrics", id + ".lyrx")
    if not file_path.endswith(".lyrx"):
        return
    if not os.path.exists(file_path):
        return None
    else:
        with open(file_path, encoding="utf-8") as file:
            return file.read().replace("\n", "\r\n")


def lyrx_dict_to_lyrx(data: dict, path: str) -> None:
    with open(path, "w") as f:
        for k, v in data.items():
            if isinstance(k, str):
                f.write(f"{k.upper()};{v}\n")
            else:
                f.write(f"{k};{v}\n")
    print(f"overwriten {path}.")


def shift_lines_to_dict(lines: list, ms: int) -> dict:
    """
    Shifts the lyrics in a file by X miliseconds, and return the patched dict with lyrics.
    """
    lyr = lyrics_lines_to_dict(lines)
    new_lyr = {}
    for k in lyr:
        new_key = k + ms
        new_lyr[new_key] = lyr[k]
    print(new_lyr)
    return new_lyr


def shift(file_path: str, ms) -> None:
    """
    Shifts the lyrics from a file by ms.
    """
    lines = open(file_path, "r").readlines()
    shift = shift_lines_to_dict(lines, ms)
    meta = parse_metadata(lines)
    final = meta | shift
    lyrx_dict_to_lyrx(final, file_path)


# shift("lyrics/00031.lyrx", 200)
