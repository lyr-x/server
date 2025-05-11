import flask, dotenv, os, requests, werkzeug
from parser import *
from search import search, all_tracks
app = flask.Flask("lyrX")
dotenv.load_dotenv()
print("SPOTIFY_CLIENT_ID:", os.getenv("SPOTIFY_CLIENT_ID"))
def get_author_pfp(author_id: str):
    pfp_path = os.path.join("profiles", f"{author_id}.png")
    return pfp_path if os.path.isfile(pfp_path) else None

@app.route("/admin")
def admin():
    code = flask.request.args.get('code')
    if code == os.getenv("ADMIN_KEY"):
        return "", 501
    else:
        return "unauthorized", 401

@app.route("/about")
def about():
    return flask.render_template("about.html")
@app.route("/discord")
def discord():
    return flask.redirect(os.getenv("DISCORD_URL"))

@app.route("/api/track/<string:id>")
def track_api(id):
    tr = track(id)
    if not tr:
        return "not found", 404
    else:
        return flask.Response(tr, 200, mimetype="text/plain")

@app.route("/api/track/<string:id>/json")
def track_api_json(id):
    tr = track(id)
    if not tr:
        return "not found", 404
    else:
        json = lyrx_to_json(tr.splitlines())
        return flask.jsonify(json), 200

@app.route("/api/track/<string:id>/meta")
def track_api_meta(id):
    tr = track(id)
    if not tr:
        return "not found", 404
    else:
        return flask.jsonify(parse_metadata(tr.splitlines()))

@app.route("/api/search")
def search_api():
    name = flask.request.args.get("q")
    if name == "*":
        res = all_tracks()
    else:
        res = search(name)
    return flask.jsonify(res)

@app.route("/")
def home():
    return flask.render_template("index.html")

@app.route("/api/statistics")
def stats_api():
    return flask.jsonify(stats())

@app.route("/assets/<string:filename>")
def cdn(filename):
    try:
        return flask.send_from_directory("assets", filename)
    except werkzeug.exceptions.NotFound:
        return "not found", 404

@app.route("/spotify/login")
def spotify_login():
    return flask.redirect(
        f"https://accounts.spotify.com/authorize?client_id={os.getenv('SPOTIFY_CLIENT_ID')}&response_type=code&redirect_uri={os.getenv('SPOTIFY_REDIRECT_URI')}&scope=user-read-currently-playing"
    )
@app.route("/api/track/<string:id>/lastfm/album")
def album_lastfm_api(id):
    tr = track(id)
    if not tr:
        return "not found", 404
    data = parse_metadata(tr)
    artist=data["artist"]
    album=data["album"]
    url = f"http://ws.audioscrobbler.com/2.0/?method=album.getInfo&album={album}&artist={artist}&api_key={os.getenv('LASTFM_API_KEY')}&format=json"
    req = requests.get(url)
    json = req.json()
    resp = {
        "title": json.get("album", {}).get("name", "unknown"),
        "artist": json.get("album", {}).get("artist", "unknown"),
        "image": json.get("album", {}).get("image", [{}])[2].get("#text", "unknown"),
        "tracks": json.get("album", {}).get("tracks", {}).get("track", [])
    }
    return flask.jsonify(resp)
@app.route("/app")
def app_web():
    return flask.render_template("app.html")
@app.route("/spotify/callback")
def spotify_callback():
    code = flask.request.args.get("code")
    if not code:
        return "authorization failed", 400

    token_url = "https://accounts.spotify.com/api/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": os.getenv("SPOTIFY_REDIRECT_URI"),
        "client_id": os.getenv("SPOTIFY_CLIENT_ID"),
        "client_secret": os.getenv("SPOTIFY_CLIENT_SECRET"),
    }

    response = requests.post(token_url, headers=headers, data=data)
    token_data = response.json()
    if "access_token" in token_data:
        return flask.redirect(f"/app?token={token_data['access_token']}")
    else:
        return "authorization failed", 400


@app.route("/spotify/now-playing")
def spotify_now_playing():
    access_token = os.getenv("SPOTIFY_ACCESS_TOKEN")
    if not access_token:
        return "no access token", 401
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
    return flask.jsonify(response.json())

@app.route("/track/<string:id>")
def track_web(id):
    tr = track(id)
    if not tr:
        return "not found", 404
    data = parse_metadata(tr)
    title=data["title"]
    artist=data["artist"]
    duration=data["duration"]
    try: verified=data["verified"]
    except KeyError: verified=None
    return flask.render_template("track.html", lyrx=tr, author=data["author"], id=id, title=title, artist=artist, duration=duration, verified=verified, author_avatar=f"/api/author/{data['author']}/avatar")

@app.route("/track/<string:id>/report")
def report_web(id):
    tr = track(id)
    if not tr:
        return "not found", 404
    data = parse_metadata(tr)
    title=data["title"]
    artist=data["artist"]
    duration=data["duration"]
    return flask.render_template("report.html", lyrx=tr, id=id, title=title, artist=artist, duration=duration)

@app.route("/api/track/<string:id>/report", methods=["POST"])
def report_api(id):
    webhook = "https://discord.com/api/webhooks/1354480670440689724/pV2wzAa5gAX9dwEkDXnAEAmaEB4qy6-cF-R68IYgUq6VaHh-yvLGZoBSeKJp_VelS6qe"
    data = flask.request.json
    try:
        desc = ""
        for l in data["lyrics"].keys():
            desc += f"- {str(l)}: {data['lyrics'][str(l)]}\n"
        try:
            context = data["context"]
        except Exception:
            pass
        webhook_data = {
            "content": "@everyone",
            "embeds": [
                {
                    "title": "New report submitted",
                    "color": int(0x0000ff)
                },
                {
                    "title": "User",
                    "color": int(0x0000ff),
                    "fields": [
                        {
                            "name": "IP",
                            "value": data["ip"]
                        },
                        {
                            "name": "User Agent",
                            "value": str(flask.request.user_agent)
                        }
                    ]
                },
                {
                    "title": "Track",
                    "color": int(0x0000ff),
                    "fields": [
                        {
                            "name": "ID",
                            "value": str(data["id"])
                        },
                        {
                            "name": "Title",
                            "value": str(data["title"])
                        },
                        {
                            "name": "Artist",
                            "value": str(data["artist"])
                        }
                    ]
                },
                {
                    "title": "Reported lyrics",
                    "color": int(0x0000ff),
                    "description": str(desc)
                },
                {
                    "title": "Additional context",
                    "color": int(0x0000ff),
                    "description": str(context)
                }
            ]
        }

        if data["lyrics"] and data["title"] and data["artist"] and data["id"] and data["ip"]:
            req = requests.post(webhook, json=webhook_data)
            return f"response: {req.status_code}: {req.json()}", 200
        else:
            return f"incomplete or bad request", 400
    except Exception as e:
        return f"incomplete or bad request: {e}", 400
@app.route("/author/<string:id>")
def author_profile_web(id):
    #TODO: make author page with all of their uploads etc
    return flask.render_template("author.html", id=id)
@app.route("/api/author/<string:id>/avatar")
def author_profile_api(id:str):
    if id == None:
        return "unknown author", 404
    pfp = get_author_pfp(id)
    if pfp:
        return flask.send_file(get_author_pfp(id), mimetype="image/png")
    else:
        return "no profile picture found", 404
@app.route("/search")
def search_web():
    return flask.render_template("search.html")

if __name__ == "__main__":
    app.run('127.0.0.1',port=5100,debug=True)
