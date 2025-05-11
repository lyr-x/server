import os
import tkinter as tk
from tkinter import filedialog
import requests
def parse_lrc(lrc_path, title, artist, duration):
    lyrics = []
    with open(lrc_path, encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("[") and line[1].isdigit():
                ts = line.split("]")[0][1:].strip()
                parts = ts.replace(".", ":").split(":")
                if len(parts) == 3:
                    try:
                        minutes = float(parts[0])
                        seconds = float(parts[1])
                        ms = float(parts[2])
                    except:
                        continue
                    time_ms = int((minutes * 60 + seconds) * 1000 + ms)
                    lyric = line.split("]")[1].strip()
                    if lyric:
                        lyrics.append((time_ms, lyric))
    return lyrics

def parse_metadata_to_file(title, artist, duration, full, author, album):
    return f"TITLE;{title}\nARTIST;{artist}\nDURATION;{duration}\nFULL;{full}\nAUTHOR;{author}\nALBUM;{album}"

def convert_lrc_to_lyrx(lrc_file, title, artist, duration, author, full,album,output_folder="lyrics"):
    lyrics = parse_lrc(lrc_file, title, artist, duration)
    metadata = parse_metadata_to_file(title, artist, duration, full, author, album)
    lyrx_lyrics = ""
    for timestamp, lyric in lyrics:
        lyrx_lyrics += f"{timestamp};{lyric}\n"
    if lyrx_lyrics:
        lyrx_content = metadata + "\n" + lyrx_lyrics
        output_id = get_next_id(output_folder)
        output_path = os.path.join(output_folder, f"{output_id}.lyrx")
        os.makedirs(output_folder, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(lyrx_content)
        print(f"converted {lrc_file} to {output_path}")
        post_webhook(output_id,title,artist,author,album)
    else:
        print(f"no lyrics found in {lrc_file}")

def get_next_id(output_folder):
    existing_files = os.listdir(output_folder) if os.path.exists(output_folder) else []
    ids = []
    for f in existing_files:
        if f.endswith(".lyrx"):
            try:
                ids.append(int(f.split(".")[0]))
            except:
                pass
    next_id = max(ids, default=0) + 1
    return f"{next_id:05d}"

def open_file_picker():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askopenfilename(title="select an lrc file", filetypes=[("LRC Files", "*.lrc")])

def check_if_converted(lrc_file, output_folder="lyrics"):
    file_name = os.path.basename(lrc_file)
    converted_file = os.path.splitext(file_name)[0] + ".lyrx"
    return os.path.exists(os.path.join(output_folder, converted_file))
def post_about_all_tracks():
    output_folder = "lyrics"
    files = os.listdir(output_folder)
    lyrx_files = [f for f in files if f.endswith('.lyrx')]
    tracks = []

    for lyrx_file in lyrx_files:
        with open(os.path.join(output_folder, lyrx_file), 'r', encoding='utf-8') as f:
            lines = f.readlines()
            metadata = {}
            for line in lines[:5]:
                key, value = line.strip().split(';')
                metadata[key] = value
            try:
                tracks.append({
                    'id': lyrx_file.split('.')[0],
                    'title': metadata['title'],
                    'artist': metadata['artist'],
                    'author': metadata['author'],
                    'album': metadata.get('album', metadata['title'])
                })
            except Exception as e:
                print(f"in {lyrx_file}: {type(e)}: {e}")

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
        "content":"<@&1355123833014845440>",
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
    
    payload = {"embeds": [embed]}
    requests.post(webhook_url, json=payload)
def get_metadata_value(line):
    return line[line.find(":")+1:line.rfind("]")].strip()
def lyricsify_scraper():
    # step 1: get album's songs
    album_url = input("album > ").strip()
def main():
    lrc_file = open_file_picker()
    if not lrc_file:
        print("no file selected.")
        return
    output_folder = "lyrics"
    # lrc_file="../lrc/Kendrick Lamar & SZA - luther.lrc"
    if check_if_converted(lrc_file, output_folder):
        print(f"the song '{lrc_file}' has already been converted.")
        return
    with open(lrc_file, encoding="utf-8") as f:
        lines = f.readlines()
    existing_metadata = [line for line in lines if line.startswith("[ti:") or line.startswith("[ar:") or line.startswith("[length:")]
    title, artist, duration = "", "", 0
    if existing_metadata:
        print("found existing metadata:")
        for meta in existing_metadata:
            print(meta.strip())
        for line in existing_metadata:
            if line.startswith("[ti:"):
                current_title = get_metadata_value(line)
                title = input(f"title ({current_title}) > ").strip()
                title = current_title if title == "" else title
            elif line.startswith("[ar:"):
                current_artist = get_metadata_value(line)
                artist = input(f"artist ({current_artist}) > ").strip()
                artist = current_artist if artist == "" else artist
            elif line.startswith("[length:"):
                current_length = get_metadata_value(line)
                length = input(f"length ({current_length}) (mm:ss) > ").strip()
                length = current_length if length == "" else length
                if ":" in length:
                    try:
                        m, s = length.split(":")
                        m, s = int(m), int(s)
                        duration = (m * 60 + s) * 1000
                    except:
                        print("invalid length format, expected mm:ss")
                        return
                else:
                    print("invalid length format, expected mm:ss")
                    return
        author = input(f"author (tjf1) > ").strip()
        author = "tjf1" if author == "" else author
        full = input(f"full ({title}) > ").strip()
        full = title if full == "" else full
        album = input(f"album ({title}) > ").strip()
        album = title if album == "" else album
    if duration == 0:
        length = input(f"length (mm:ss) > ").strip()
        if ":" in length:
            try:
                m, s = length.split(":")
                m, s = int(m), int(s)
                duration = (m * 60 + s) * 1000
            except:
                print("invalid length format, expected mm:ss")
                return
    convert_lrc_to_lyrx(lrc_file, title, artist, duration, author, full, album)

if __name__ == "__main__":
    # main()
    post_about_all_tracks()