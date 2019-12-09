from glob import glob
import json
import os


if __name__ == "__main__":
    json_dump_file = "dump_for_upload.json" 
    audio_ext = ".ogg"
    username = "annotator"
    annotation_dir = "../../data/labelled_json/"

    annotation_files = sorted(glob(os.path.join(annotation_dir, "*_labeled.json")))

    d = [] 
    for a_f in annotation_files: 
         
        json_filename = os.path.basename(a_f) 
        wav_name = json_filename[:-13] + audio_ext
        print(wav_name) 
        with open(a_f, "r") as f: 
            s = f.read() 
        if s: 
            tmp_data = json.loads(s) 
        else: 
            tmp_data = [] 
        d.append({"file": wav_name, "username": username, "value": tmp_data})

    with open(json_dump_file, "w") as f:
        json.dump(d, f, indent=2)

