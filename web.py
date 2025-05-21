#!/usr/bin/env python3
import flask, dotenv, os, requests, werkzeug, json
from parser import *
import parser
from urllib.parse import quote
from search import search, all_tracks
from flask import *
from flask_cors import CORS
from flask_limiter import Limiter
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_limiter.util import get_remote_address
from authlib.integrations.flask_client import OAuth

dotenv.load_dotenv()
app = flask.Flask("lyrX", static_url_path="")
app.secret_key = os.urandom(24)
CORS(app, supports_credentials=True)
oauth = OAuth(app)
discord = oauth.register(
    name="discord",
    client_id=os.getenv("DISCORD_CLIENT_ID"),
    client_secret=os.getenv("DISCORD_CLIENT_SECRET"),
    access_token_url="https://discord.com/api/oauth2/token",
    authorize_url="https://discord.com/api/oauth2/authorize",
    api_base_url="https://discord.com/api/",
    client_kwargs={"scope": "identify email guilds"},
)


@app.route("/auth/discord/login")
def login():
    return discord.authorize_redirect(os.getenv("DISCORD_REDIRECT_URI"))


@app.route("/auth/discord/callback")
def callback():
    token = discord.authorize_access_token()
    if not token:
        return "Failed to get token", 400
    print("Token:", token)

    resp = discord.get("/users/@me")
    print("User fetch status:", resp.status_code)
    print("User fetch body:", resp.text)

    try:
        user = resp.json()
    except Exception as e:
        print("Error parsing JSON:", e)
        return "Discord user info fetch failed", 500

    session["user"] = user
    return redirect("/auth/discord/me")


@app.route("/auth/discord/me")
def me():
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401
    resp = discord.get("/users/@me")
    print("Discord /@me status:", resp.status_code)
    print("Discord /@me text:", resp.text)
    user = resp.json()
    return jsonify(session["user"])


@app.route("/auth/discord/logout")
def logout():
    session.clear()
    return redirect("/")


dev = False
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=2)


def should_bypass():
    return request.args.get("ratelimit_bypass") == "147858397258723"


def is_whitelisted():
    return get_remote_address() in {}


limiter = Limiter(get_remote_address, app=app, default_limits=["60 per minute"])


def get_author_pfp(author_id: str):
    pfp_path = os.path.join("profiles", f"{author_id}.png")
    return pfp_path if os.path.isfile(pfp_path) else None


@app.before_request
def log_request():
    print(f"Request to: {flask.request.path}")


@app.route("/ip")
def debug_ip():
    return {
        "remote_addr": request.remote_addr,
        "x_forwarded_for": request.headers.get("X-Forwarded-For"),
        "get_remote_address": get_remote_address(),
    }


@app.errorhandler(404)
def not_found(e):
    return flask.render_template("404.html", type=0), 404


@app.route("/admin")
def admin():
    code = flask.request.args.get("code")
    if code == os.getenv("ADMIN_KEY"):
        return "success", 501
    else:
        return "unauthorized", 401


@app.route("/about")
def about():
    return flask.render_template("about.html")


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
    add_view(id)
    if not tr:
        return "not found", 404
    else:
        json = lyrx_to_json(tr.splitlines())
        return flask.jsonify(json), 200


def error(e):
    return {"error": e}


@app.route("/api/track/<string:id>/meta")
def track_api_meta(id):
    tr = track(id)
    if not tr:
        return error(f"track {id} not found")
    else:
        meta = parse_metadata(tr.splitlines())
        meta["views"] = get_viewmap().get(f"{id}", 0)
        return flask.jsonify(meta)


@app.route("/api/me")
def get_user():
    user = session.get("discord_user")
    if not user:
        return jsonify({"error": "Not logged in"}), 401
    return jsonify(user)


@app.route("/api/search")
def search_api():
    name = flask.request.args.get("q")
    res = search(name)
    return flask.jsonify(res)


@app.route("/")
def home():
    return flask.render_template("index.html")


@app.route("/api/statistics")
def stats_api():

    stats = parser.stats()
    stats["dev"] = dev
    return flask.jsonify(stats)


@app.route("/assets/<string:filename>")
def cdn(filename):
    try:
        return flask.send_from_directory("assets", filename)
    except werkzeug.exceptions.NotFound:
        return "not found", 404


@app.route("/spotify/login")
def spotify_login():
    redirect = flask.request.args.get("redirect")
    if not redirect:
        redirect = "/app"
    return flask.redirect(
        f"https://accounts.spotify.com/authorize?client_id={os.getenv('SPOTIFY_CLIENT_ID')}&response_type=code&redirect_uri={os.getenv('SPOTIFY_REDIRECT_URI')}&scope=user-read-currently-playing&redirect={redirect}"
    )


@app.route("/api/track/<string:id>/lastfm/album")
def album_lastfm_api(id):
    try:

        tr = track(id)
        if not tr:
            return "not found", 404

        data = parse_metadata(tr)
        artist = data["artist"].split("|")[0]
        album = data["album"]
        artist_encoded = quote(artist)
        album_encoded = quote(album)

        url = f"http://ws.audioscrobbler.com/2.0/?method=album.getInfo&album={album_encoded}&artist={artist_encoded}&api_key={os.getenv('LASTFM_API_KEY')}&format=json"

        req = requests.get(url)
        json_data = req.json()

        if "album" not in json_data:
            return (
                flask.jsonify(
                    {
                        "error": f"Album '{album}' by '' not found on Last.fm",
                        "lastfm": json_data,
                    }
                ),
                404,
            )

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
        return flask.jsonify(resp)

    except Exception as e:
        return flask.jsonify({"error": f"{type(e).__name__}: {e}"})


@app.route("/app")
def app_web():
    return flask.render_template("app.html")


@app.route("/favicon.ico")
def favicon():
    path = os.path.abspath("lyrX.png")
    if not os.path.exists(path):
        print("File does not exist:", path)
        return "not found", 404
    return flask.send_file(path, mimetype="image/png")


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
        return flask.render_template("callback.html", code=token_data["access_token"])
        return flask.redirect(f"/app?token={token_data['access_token']}")
    else:
        return "authorization failed: no access token", 400


@app.route("/auth/callback/spotify")
def auth_callback_spotify():
    code = flask.request.args.get("code")
    if not code:
        return "authorization failed", 400

    token_url = "https://accounts.spotify.com/api/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "https://lyrx.projectxyz.dev/auth/callback/spotify",
        "client_id": os.getenv("SPOTIFY_CLIENT_ID"),
        "client_secret": os.getenv("SPOTIFY_CLIENT_SECRET"),
    }

    response = requests.post(token_url, headers=headers, data=data)
    token_data = response.json()
    print(token_data)
    if "access_token" in token_data:
        # return flask.render_template("callback.html", code=token_data['access_token'])
        return flask.redirect(
            f"http://localhost:5173/spotify/callback?token={token_data['access_token']}"
        )
    else:
        return "authorization failed: no access token", 400


@app.route("/spotify/token")
def spotify_token():
    code = flask.request.args.get("code")
    redirect = flask.request.args.get("redirect_uri")
    if not code:
        return flask.jsonify({"error": "No authorization code provided"}), 400

    token_url = "https://accounts.spotify.com/api/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect,
        "client_id": os.getenv("SPOTIFY_CLIENT_ID"),
        "client_secret": os.getenv("SPOTIFY_CLIENT_SECRET"),
    }

    response = requests.post(token_url, headers=headers, data=data)
    print(f"send request for token, code: {response.status_code}")
    if response.status_code != 200:
        return flask.jsonify({"error": "Failed to get token"}), 400

    token_data = response.json()
    return flask.jsonify(
        {
            "access_token": token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token"),
            "expires_in": token_data.get("expires_in"),
        }
    )


@app.route("/spotify/now-playing")
def spotify_now_playing():
    access_token = os.getenv("SPOTIFY_ACCESS_TOKEN")
    if not access_token:
        return "no access token", 401
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        "https://api.spotify.com/v1/me/player/currently-playing", headers=headers
    )
    return flask.jsonify(response.json())


@app.route("/track/<string:id>")
def track_web(id):
    tr = track(id)
    if not tr:
        return flask.render_template("404.html", type=1), 404
    data = parse_metadata(tr)
    title = data["title"]
    artist = data["artist"]
    duration = data["duration"]
    try:
        verified = data["verified"]
    except KeyError:
        verified = None
    return flask.render_template(
        "track.html",
        lyrx=tr,
        author=data["author"],
        id=id,
        title=title,
        artist=", ".join(split_artists(artist)),
        duration=duration,
        verified=verified,
        author_avatar=f"/api/author/{data['author']}/avatar",
    )


@app.route("/track/<string:id>/report")
def report_web(id):
    tr = track(id)
    if not tr:
        return "not found", 404
    data = parse_metadata(tr)
    title = data["title"]
    artist = data["artist"]
    duration = data["duration"]
    return flask.render_template(
        "report.html", lyrx=tr, id=id, title=title, artist=artist, duration=duration
    )


@app.route("/api/track/<string:id>/report", methods=["POST"])
@limiter.limit("2 per hour")
def report_api(id):
    webhook = os.getenv("WEBHOOK_REPORT")
    rawdata = flask.request.data
    data = json.loads(rawdata)
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
                {"title": "New report submitted", "color": int(0x0000FF)},
                {
                    "title": "User",
                    "color": int(0x0000FF),
                    "fields": [
                        {"name": "IP", "value": data["ip"]},
                        {"name": "User Agent", "value": str(flask.request.user_agent)},
                    ],
                },
                {
                    "title": "Track",
                    "color": int(0x0000FF),
                    "fields": [
                        {"name": "ID", "value": str(data["id"])},
                        {"name": "Title", "value": str(data["title"])},
                        {"name": "Artist", "value": str(data["artist"])},
                    ],
                },
                {
                    "title": "Reported lyrics",
                    "color": int(0x0000FF),
                    "description": str(desc),
                },
                {
                    "title": "Additional context",
                    "color": int(0x0000FF),
                    "description": str(context),
                },
            ],
        }

        if (
            data["lyrics"]
            and data["title"]
            and data["artist"]
            and data["id"]
            and data["ip"]
        ):
            req = requests.post(webhook, json=webhook_data)
            return f"response: {req.status_code}", 200
        else:
            return f"incomplete or bad request", 400
    except Exception as e:
        print(f"error while report: {data}")
        return f"incomplete or bad request - {type(e).__name__} {e}", 400


@app.route("/author/<string:id>")
def author_profile_web(id):
    # TODO: make author page with all of their uploads etc
    # TODO: make authors discord accounts and allow people to upload
    return flask.render_template("author.html", id=id)


@app.route("/api/author/<string:id>/avatar")
def author_profile_api(id: str):
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
    dev = True
    app.run("0.0.0.0", port=5100, debug=True)
