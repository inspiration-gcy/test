import json
import sys
import threading
import time
from datetime import datetime
import time

from flask import Flask, Response, jsonify, render_template

import app.base.models
import cv2
import imutils
from app.mock.streams.mock_stream import MockStream
from app.streams.nxt.nxt_stream import NxtCameraStream
from imutils.video import VideoStream


class CamHandler:

    cam_obj_list = []

    def __init__(self):
        cameras = app.home.models.Cameras.get_all_cameras()
        for cam in cameras:
            self.cam_obj_list.append(
                {"cam_uuid": cam.cam_uuid, "stream_obj": CamStream(cam)})

    @classmethod
    def get_cam_stream_obj(cls, cam_uuid):
        return next((cam["stream_obj"] for cam in cls.cam_obj_list if cam["cam_uuid"] == cam_uuid), None)

    @classmethod
    def add_cam_stream_obj(cls, cam_uuid):
        print("Adding new cam to CamHandler: " + cam_uuid)
        cam = app.home.models.Cameras.get_camera(cam_uuid)
        cls.cam_obj_list.append(
            {"cam_uuid": cam_uuid, "stream_obj": CamStream(cam)})

    @classmethod
    def rm_cam_stream_obj(cls, cam_uuid):
        print("Removing cam from CamHandler: " + cam_uuid)
        cls.cam_obj_list[:] = [
            cam for cam in cls.cam_obj_list if cam["cam_uuid"] != cam_uuid]

    @classmethod
    def refresh_stream_obj(cls, cam_uuid):
        print("Refreshing CamHandler: " + cam_uuid)
        cls.rm_cam_stream_obj(cam_uuid)
        cls.add_cam_stream_obj(cam_uuid)


class CamStream:

    def __init__(self, camera):

        self.sleep_len = 0.1

        self.output_frame = None
        self.output_data = None
        self.lock = threading.Lock()
        self.camera = camera
        self.save_data = False
        self.is_stream_live = False
        self.ai_model = None
        self.job = None
        self.station = None

        if (camera.cam_type == "STUB"):
            self.cam_stream = MockStream()
        elif (camera.cam_type == "NXT"):
            try:
                self.cam_stream = NxtCameraStream(camera.ip)
            except:
                print("Camera IP not found")
                CamHandler.rm_cam_stream_obj(self.camera.cam_uuid)
                return
        else:
            print("Unidentified camera type")
            CamHandler.rm_cam_stream_obj(self.camera.camera_uuid)
            return

        self.update_stream_settings(camera)
        self.start_thread()

    def update_stream_settings(self, camera):
        if (camera.assoc_ai_model):
            self.ai_model = camera.assoc_ai_model

        if (camera.assoc_station):
            self.station = camera.assoc_station
            if (camera.assoc_station.assoc_job):
                self.job = camera.assoc_station.assoc_job

    def start_thread(self):
        self.t = threading.Thread(target=self.gen_stream)
        self.t.daemon = True
        self.t.start()
        print("Initialising cam: " + self.camera.name)

    def start_record(self, file_name):
        if (self.save_data == False):

            if not file_name:
                file_name = str(self.camera.name) + "_" + str(datetime.now().strftime("%Y%m%d-%H%M%S"))

            save_loc = "app/base/static/data/videos/" + file_name + ".mp4"
            
            print("Saving at: " + save_loc)

            self.video_out = cv2.VideoWriter(save_loc,
                                             cv2.VideoWriter_fourcc(
                                                 'a', 'v', 'c', '1'),
                                             10, (self.cam_stream.frame_width, self.cam_stream.frame_height))
            self.save_data = True

    def stop_record(self):
        if (self.save_data == True):
            print("Stop recording")
            self.save_data = False
        self.video_out.release()

    def gen_stream(self):

        if (self.ai_model and self.job):
            self.data_handler = CamData(
                self.ai_model, self.job, self.save_data, self.camera.cam_uuid)

        while True:
            time.sleep(self.sleep_len)

            # Get frame from video stream
            hasFrame, frame = self.cam_stream.get_frame()
            if not hasFrame:
                break

            if (self.save_data):
                self.video_out.write(frame)

            label = self.cam_stream.get_label()

            data = []
            if (self.ai_model and self.job):
                data = self.data_handler.process_data(label, self.sleep_len)

            # acquire the lock, set the output frame, and release the lock
            with self.lock:
                self.output_frame = frame.copy()
                self.output_data = json.dumps(data)

        else:
            # kill thread if not used
            print("Stream does not have AI model/job attached")

    def get_video(self):
        # loop over frames from the output stream
        while True:
            time.sleep(self.sleep_len)
            # wait until the lock is acquired
            with self.lock:
                # check if the output frame is available, otherwise skip
                # the iteration of the loop
                if self.output_frame is None:
                    continue

                # encode the frame in JPEG format
                flag, encodedImage = cv2.imencode(".jpg", self.output_frame)

                # ensure the frame was successfully encoded
                if not flag:
                    continue

                # yield the output frame in the byte format
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                       bytearray(encodedImage) + b'\r\n')

    def get_job_data(self):
        # loop over frames from the output stream
        while True:
            time.sleep(self.sleep_len)
            # wait until the lock is acquired
            with self.lock:
                # check if the output label is available, otherwise skip
                # the iteration of the loop
                if self.output_data is None:
                    continue

                yield ("data: %s\n\n" % (self.output_data))


class CamData:

    def __init__(self, ai_model, job, save_data, cam_uuid, ):

        self.cam_uuid = cam_uuid
        self.last_step_time = job.last_step_time
        self.target_step_time = 5
        self.save_data = False  # Do this at stream level

        self.required_assemblies = job.required_assemblies
        self.allotted_time = job.allotted_time

        self.steps = ai_model.labels.split(",")

        for idx, step in enumerate(self.steps):
            self.steps[idx] = {"num": idx,
                               "name": step,
                               "complete": False,
                               "takt": 0,
                               "on_target": True}

        self.num_steps = len(self.steps)
        self.tak_history = []
        self.tak = 0
        self.ave_tak = 0
        self.est_time_completion = 0
        self.line_rate = 0
        self.job_on_target = True
        self.num_assemblies_complete = 0

        self.reset_assembly()

    def reset_assembly(self):

        for i in range(len(self.steps)):
            self.steps[i]["complete"] = False
            # self.steps[i]["takt"] = 0

        self.step_history = []
        self.counter = 0
        self.assembly_timestamp = time.time()
        self.current_step = self.steps[0]
        self.step_iterator = 0

    def process_data(self, label, sleep_len):

        if label:
            check_step = next(
                (step for step in self.steps if step['name'] == label), None)

            if check_step:
                self.current_step = check_step
                self.current_step["takt"] += 1 * sleep_len * 2  # FIX This
                self.current_step["takt"] = round(self.current_step["takt"], 3)

                # if self.step_history[-self.completion_threshold:].count(self.step_iterator) == self.completion_threshold*self.step_iterator:
                self.current_step["complete"] = True
                self.step_iterator += 1

                # check if on target
                if self.current_step["takt"] > self.target_step_time:
                    self.current_step["on_target"] = False
                else:
                    self.current_step["on_target"] = True

                self.step_history.append(self.current_step["num"])

                frames_per_second = 1/sleep_len

                if sum(self.step_history[-int(self.last_step_time*frames_per_second):]) >= int(self.last_step_time*frames_per_second)*(self.num_steps-1):
                # if len(self.step_history) > 20:
                    self.num_assemblies_complete += 1
                    self.tak = time.time() - self.assembly_timestamp
                    self.tak_history.append(self.tak)
                    self.ave_tak = sum(self.tak_history) / \
                        len(self.tak_history)
                    self.est_time_completion = (
                        self.required_assemblies-self.num_assemblies_complete)*self.ave_tak
                    self.line_rate = 60/self.ave_tak

                    if self.est_time_completion > self.allotted_time:
                        self.job_on_target = False
                    else:
                        self.job_on_target = True

                    # if (self.save_data):
                    # 	with open("app/data/fingerprint/" + str(self.assembly_timestamp.strftime("%Y%m%d") + ".csv"), 'a') as f:
                    # 		writer = csv.writer(f)
                    # 		writer.writerow(self.step_history)

                    self.reset_assembly()
            # else:
            # 	print("Wrong Model")
                # print(label)
                # print(self.steps)

        self.counter += 1

        data = {
            "cam_uuid": self.cam_uuid,
            "steps": self.steps,
            "req_assemblies": self.required_assemblies,
            "assemblies_complete": self.num_assemblies_complete,
            "ave_takt": round(self.ave_tak, 2),
            "est_completion_time": round(self.est_time_completion, 2),
            "line_rate": round(self.line_rate, 2),
            "current_step": self.current_step["name"],
            "allotted_time": self.allotted_time,
            "on_target": self.job_on_target,
            "last_step_time": self.last_step_time
        }

        return data
