import parser, os


def id_in_meta(id: str):
    with open(f"lyrics/{id}.lyrx", "r") as f:
        meta = parser.parse_metadata(f.readlines())
        lyr = parser.lyrics_lyrx_to_list(f"lyrics/{id}.lyrx")
    meta["id"] = id
    final = meta | lyr
    parser.lyrx_dict_to_lyrx(final)


for f in os.listdir("lyrics"):
    if not f.endswith(".lyrx"):
        continue
    id_in_meta(f.replace(".lyrx", ""))
