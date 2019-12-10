import json
from glob import glob
import os

from microfaune.detection import RNNDetector



if __name__ == "__main__":
    track_dir = "../../data/citeU/"
    json_dump_file = "predictions.json"    

    tracks = sorted(glob(os.path.join(track_dir, "*.wav")))
    
    model = RNNDetector()

    data = []
    for audiofile in tracks:
        _, local_score = model.predict_on_wav(audiofile)
        ogg_file = os.path.basename(audiofile).replace("wav", "ogg")
        data.append({"file": ogg_file,
                     "prediction": [float(s) for s in local_score]})

    with open(json_dump_file, "w") as f:
        json.dump(data, f)

