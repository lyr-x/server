import os
from typing import Tuple, Dict, List

required_tags = ["title", "id", "author", "artist", "duration", "album"]

def convert_to_new_format(file_path: str):
    with open(file_path, 'r') as rf:
        lines = rf.read().splitlines()
    
    with open(file_path, 'w') as wf:
        for line in lines:
            if line.startswith("["):  # Convert old format to new format
                tag = line.strip("[]").split(" ")[0]
                if tag in required_tags:
                    wf.write(f"{tag};\n")
            elif ";" in line:  # Keep lyrics lines as is
                wf.write(f"{line}\n")

def validate_all() -> Tuple[bool, Dict[str, List[str]], List[str]]:
    files = os.listdir("lyrics")
    miss = {}
    
    for f in files:
        file_path = os.path.join("lyrics", f)
        with open(file_path) as rf:
            lines = rf.read().splitlines()
            tags = []
            tag_format_valid = True
            for l in lines:
                if l.startswith("["):  
                    tag = l.strip("[]").split(" ")[0]
                    if tag not in required_tags:
                        tag_format_valid = False
                    tags.append(tag)
                elif ";" in l:  
                    continue  
            
            missing_tags = [tag for tag in required_tags if tag not in tags]
            
            if not tag_format_valid:
                miss[f] = ["invalid tag format"]
            if missing_tags:
                miss[f] = miss.get(f, []) + missing_tags
            if not any(l.strip() and not l.startswith("[") for l in lines):  
                miss[f] = miss.get(f, []) + ["no lyrics found"]

    if miss:
        return False, miss, required_tags
    else:
        return True, miss, required_tags

def validate_file(track_id: str) -> Tuple[bool, str, List[str]] | bool:
    file_path = os.path.join("lyrics", f"{track_id}.lyrx")
    
    if not os.path.exists(file_path):
        return (False, f"{track_id}.lyrx does not exist", required_tags)
    
    with open(file_path) as rf:
        lines = rf.read().splitlines()
        tags = []
        tag_format_valid = True
        for l in lines:
            if l.startswith("["):  
                tag = l.strip("[]").split(" ")[0]
                if tag not in required_tags:
                    tag_format_valid = False
                tags.append(tag)
            elif ";" in l:  
                continue  

        missing_tags = [tag for tag in required_tags if tag not in tags]

        if not tag_format_valid:
            return (False, f"{track_id}.lyrx has invalid tag format", required_tags)
        elif missing_tags:
            return (False, f"{track_id}.lyrx is missing the following tags: {', '.join(missing_tags)}", required_tags)
        elif not any(l.strip() and not l.startswith("[") for l in lines):  
            return (False, f"{track_id}.lyrx has no lyrics", required_tags)
    
    return True

def validate():
    mode = input("validation mode (SINGLE/ALL) (s/A) > ")
    if mode.lower() == "s":
        tid = input("enter track id > ")
        result = validate_file(tid)
        if result == True:
            print("validation passed")
        else:
            print(f"validation failed: {result[1]}")
    else:
        print("starting, this may take a while")
        v = validate_all()
        if v[0]:
            print("validation results: pass")
        else:
            miss = v[1]
            print("validation results: fail")
            print(f"{len(miss)}/{len(os.listdir('lyrics'))} files are invalid:")
            for f in sorted(miss.keys()):
                print(f"{f}: {', '.join(miss[f])}")
                if "invalid tag format" in miss[f]:
                    modify = input(f"Do you want to convert {f} to the new format? (y/n) > ")
                    if modify.lower() == "y":
                        convert_to_new_format(os.path.join("lyrics", f))
                        print(f"{f} has been converted to the new format.")
                
                if "no lyrics found" in miss[f]:
                    print(f"No lyrics found for {f}. Please add lyrics.")
                
                if "missing" in ', '.join(miss[f]):
                    for tag in required_tags:
                        if tag not in miss[f]:
                            fill_tag = input(f"Enter {tag} for {f}: ")
                            with open(os.path.join("lyrics", f), 'a') as wf:
                                wf.write(f"[{tag}] {fill_tag}\n")
                                print(f"{tag} added to {f}")

if __name__ == "__main__":
    validate()
