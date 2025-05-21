import parser, os


def id_in_meta(id: str):
    with open(f"lyrics/{id}.lyrx", "r") as f:
        meta = parser.parse_metadata(f.readlines())
        lyr = parser.lyrics_lines_to_dict(open(f"lyrics/{id}.lyrx", "r").readlines())
        meta["id"] = id
    print(f"added id to track {id}")
    final = meta | lyr
    parser.lyrx_dict_to_lyrx(final, f"lyrics/{id}.lyrx")


for f in sorted(os.listdir("lyrics")):
    if not f.endswith(".lyrx"):
        continue
    print(f"file: {f}")
    id_in_meta(f.replace(".lyrx", ""))
