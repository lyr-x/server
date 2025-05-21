import os, difflib
from parser import parse_metadata


def search(name: str):
    lyr = os.listdir("lyrics")
    results = []
    query = name.lower()
    exact_mode = query.startswith("!")
    all_mode = query.strip() == "*"

    if exact_mode:
        query = query[1:].strip()

    for l in lyr:
        if not l.endswith(".lyrx"):
            continue
        file_id = os.path.splitext(l)[0]
        with open(os.path.join("lyrics", l), encoding="utf-8") as file:
            metadata = parse_metadata(file.readlines())

            if all_mode:
                results.append(
                    {"id": file_id, "data": metadata, "match": 0, "match_field": "all"}
                )
                continue

            if exact_mode:
                full_value = metadata.get("full", "").lower()
                if full_value == query:
                    return [
                        {
                            "id": file_id,
                            "data": metadata,
                            "match": 100,
                            "match_field": "full",
                        }
                    ]
            else:
                candidate = None
                for field in ["title", "album", "artist", "full"]:
                    value = metadata.get(field, "").lower()

                    if field == "artist":
                        artists = [a.strip() for a in value.split("|")]
                        for artist in artists:
                            ratio = difflib.SequenceMatcher(None, query, artist).ratio()
                            if ratio >= 0.7:
                                candidate = {
                                    "field": field,
                                    "value": artist,
                                    "ratio": ratio,
                                }
                                break
                    else:
                        ratio = difflib.SequenceMatcher(None, query, value).ratio()
                        if ratio >= 0.7:
                            candidate = {"field": field, "value": value, "ratio": ratio}
                            break

                if candidate is not None:
                    results.append(
                        {
                            "id": file_id,
                            "data": metadata,
                            "match": candidate["ratio"] * 100,
                            "match_field": candidate["field"],
                        }
                    )

    if not exact_mode and not all_mode:
        results.sort(key=lambda r: (0 if r["match_field"] == "title" else 1))
    return results


def all_tracks():
    lyr = os.listdir("lyrics")
    matches = []
    for l in lyr:
        if not l.endswith(".lyrx"):
            continue
        file_id = os.path.splitext(l)[0]
        with open(os.path.join("lyrics", l), encoding="utf-8") as file:
            metadata = parse_metadata(file.read())
            matches.append({"id": file_id, "data": metadata})
    return matches
