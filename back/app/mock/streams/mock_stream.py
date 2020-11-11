import csv

import cv2
import numpy as np


class MockStream:

    def __init__(self):
        self.cap = cv2.VideoCapture("app/mock/streams/plug.mov")
        self.frame_width = int(self.cap.get(3))
        self.frame_height = int(self.cap.get(4))

        self.num_frames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        self.frame_counter = 0

        with open("app/mock/streams/00fingerprint.csv") as f:
            self.fingerprint = list(csv.reader(f))

    def get_frame(self):

        hasFrame, frame = self.cap.read()
        self.frame_counter += 1

        # reset video to beginning if at end
        if self.frame_counter == self.num_frames:
            self.frame_counter = 0
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        return hasFrame, frame

    def get_label(self):

        row_num = int(self.frame_counter)
        step_num = int(np.argmax(self.fingerprint[row_num][1:]))

        if step_num == 0:
            return "background"
        elif step_num == 1:
            return "empty"
        elif step_num == 2:
            return "top pin"
        elif step_num == 3:
            return "left pin"
        elif step_num == 4:
            return "right pin"
        elif step_num == 5:
            return "clip"
        elif step_num == 6:
            return "fuse"
        elif step_num == 7:
            return "back"
        elif step_num == 8:
            return "screw"
        elif step_num == 9:
            return "paper"
        else:
            return "complete"
