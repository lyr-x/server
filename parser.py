import os, difflib, time, readchar, requests
def parse_metadata(file:str) -> dict: # parser v3
    data = {}
    lines = file.splitlines()
    for l in lines:
        ls = l.split(";")
        if not l[0].isdigit():
            try:
                data[ls[0].lower()] = ls[1] 
            except IndexError:
                pass

    return data
def post_about_all_tracks():
    output_folder = "lyrics"
    files = os.listdir("lyrics")
    lyrx_files = []
    for f in files:
        if f.endswith(".lyrx"):
            lyrx_files.append(f)
    tracks = []

    for lyrx_file in lyrx_files:
        with open(f"lyrics/{lyrx_file}", 'r') as f:
            content = f.read()
            lines = content.splitlines()
            print(content)
            metadata = parse_metadata(content)
            
            try:
                print(metadata)
                tracks.append({
                    'id': lyrx_file.split('.')[0],
                    
                    'title': metadata['title'],
                    'artist': metadata['artist'],
                    'author': metadata['author'],
                    'album': metadata.get('album', metadata['title'])
                })
            except Exception as e:
                print(f"in {lyrx_file}: {type(e)}: {e}")
    tracks.sort(key=lambda x: x['id'])
    for track in tracks:
        post_webhook(
            track['id'],
            track['title'],
            track['artist'],
            track['author'],
            track['album']
        )
def post_webhook(id, title, artist, author, album, webhook_url="https://discord.com/api/webhooks/1355123433582887013/o1Vmr8EPhOVT8iA0XMWlLFoofep-Cd8YJ-IUpmPuZf9S2PU43c9FIZhxhOX1tGaNr3oW"):
    embed = {
        
        "title": "New Track Added",
        "color": 0xd175ff,
        "fields": [
            {"name": "ID", "value": id, "inline": False},
            {"name": "Title", "value": title, "inline": True},
            {"name": "Artist", "value": artist, "inline": True},
            {"name": "Album", "value": album, "inline": True},
            {"name": "Author", "value": author, "inline": False}
        ]
    }
    
    payload = {"content":"<@&1355123833014845440>","embeds": [embed]}
    requests.post(webhook_url, json=payload)
def parse_metadata_v2(file:str) -> dict:
    data = {}
    lines = file.splitlines()
    for l in lines:
        if l.startswith("["):
            tagl = l.strip("[]")
            tagl = tagl.replace("]","")
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
    data = {
        "tracks":len(os.listdir("lyrics")),
    }
    return data
def parse_lyrics(file_path):
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
    if not os.path.exists(file_path):
        return None
    else:
        with open(file_path, encoding="utf-8") as file:
            return file.read().replace('\n', '\r\n')



def track(id: str):
    file_path = os.path.join("lyrics", id + ".lyrx")
    if not os.path.exists(file_path):
        return None
    else:
        return open(file_path, encoding="utf-8").read()
if __name__ == "__main__":
    post_about_all_tracks()