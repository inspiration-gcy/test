import cv2
import math
import os 
from datetime import datetime


def split_training_video(data):
    video_path = "app/base/static/data/videos/" + data['selectedVideo']

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)

    os.mkdir("app/ai/training/" + data['name'])

    for step in data['model_labels']:
        print("Processing: " + step['step'])

        if step['start'] < step['end']:
            os.mkdir("app/ai/training/" + data['name'] + "/" + timestamp + "_" + step['step'])

            frame_start = math.ceil(step['start'] * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_start-1)

            for i in range(math.floor((step['end']-step['start'])*fps)):
                hasFrame, frame = cap.read()
                print(hasFrame)
                cv2.imwrite("app/ai/training/" + data['name'] + "/" + timestamp +  "_" + step['step'] + "/" + str(i)+'.jpg', frame)

        else:
            print("End time not after start time")
    
    cap.release()
