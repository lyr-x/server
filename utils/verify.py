import requests
tid = input("track id > ")
def post_webhook(id, title, artist, author, album, webhook_url="https://discord.com/api/webhooks/1355123433582887013/o1Vmr8EPhOVT8iA0XMWlLFoofep-Cd8YJ-IUpmPuZf9S2PU43c9FIZhxhOX1tGaNr3oW"):
    embed = {
        
        "title": "Track Verified",
        "color": 0x0fff6b,
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

def parse_metadata(lines: list) -> dict: # parser v3
    data = {}
    for l in lines:
        ls = l.split(";")
        if not l[0].isdigit():
            try:
                key = ls[0].lower()
                value = ls[1] 
                if key == "artist" and len(value.split("|")) > 1:
                    value = value.split("|")[0]
                print(f"{key}: {value}")
                data[key] = value
            except IndexError:
                pass
    return data

with open(f"lyrics/{tid}.lyrx","r") as f:
    data = f.readlines()
    metadata = parse_metadata(data)
    data.insert(1, "VERIFIED;0\n")
with open(f"lyrics/{tid}.lyrx","w") as f:
    f.writelines(data)
    post_webhook(tid,metadata["title"],metadata["artist"],metadata["author"],metadata["album"])
