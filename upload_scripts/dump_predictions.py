import json
from glob import glob
import os

from microfaune.detection import RNNDetector


if __name__ == "__main__":
    track_dir = "../../data/citeU/"
    json_dump_file = "predictions_{ind}.json"

    tracks = sorted(glob(os.path.join(track_dir, "*.wav")))
    model = RNNDetector()

    data = []
    ind = 0
    for audiofile in tracks:
        _, local_score = model.predict_on_wav(audiofile)
        ogg_file = os.path.basename(audiofile).replace("wav", "ogg")
        data.append({"file": ogg_file,
                     "prediction": [float(s) for s in local_score]})
        if len(data) == 100:
            with open(json_dump_file.format(ind=ind), "w") as f:
                json.dump(data, f)
            data = []
            ind += 1

    with open(json_dump_file.format(ind=ind), "w") as f:
        json.dump(data, f)
