from parser import *
from search import search
def play(id):
    file_path = os.path.join("lyrics", id + ".lyrx")
    lyrics = parse_lyrics(file_path)
    start_time = time.time()
    print(f"Playing {id} now...\n")
    
    for i, (ms, lyric) in enumerate(lyrics):
        if i == 0:
            delay = ms / 1000
        else:
            delay = (ms - lyrics[i-1][0]) / 1000
        
        time.sleep(delay)
        print(lyric)

def main():
    search_results = search(input("What song do you want to check the lyrics for?\n> "))
    print(f"\n{len(search_results)} match{'es' if len(search_results) > 1 else ''}:\n")
    i = 1
    for m in search_results:
        print(f"[{i}] [{round(m['match'])}%]: {m['data']['title']} by {m['data']['artist']}")
        i += 1
    print("\n")
    
    if len(search_results) > 1:
        selected = search_results[int(input("Now, select a track > ")) - 1]["id"]
    else:
        selected = search_results[0]["id"]
    print("READY TO PLAY: press any key")
    readchar.readkey()
    countdown = 3 
    for i in range(countdown):
        if countdown == 0:
            break
        print(f"starting in {countdown}")
        countdown -= 1
        time.sleep(1)
    play(selected)

if __name__ == "__main__":
    main()