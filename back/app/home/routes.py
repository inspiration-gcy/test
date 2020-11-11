# -*- encoding: utf-8 -*-
"""
MIT License
Copyright (c) 2019 - present AppSeed.us
"""

import os
from os import listdir
from os.path import isfile, join

from flask import request

import app.ai.ai_functions as ai_func
from app.base.util import create_response
from app.home import blueprint
from app.home.models import Jobs, Stations, Cameras, AiModels
from app.streams.camstreaming import CamHandler
from app.streams.nxt.nxt_finder import Finder


######################
### JOB ROUTES #######
######################

@blueprint.route("/jobs")
def get_jobs():
    jobs_list = [job.toJson() for job in Jobs.get_all_jobs()]
    return create_response(message="Success", data=jobs_list, code=200)


@blueprint.route("/jobs/<job_uuid>")
def get_job(job_uuid):
    job = Jobs.get_job(job_uuid).toJson()
    return create_response(message="Success", data=job, code=200)


@blueprint.route("/jobs", methods=['POST'])
def post_jobs():
    job = Jobs.add_job(job_name=request.json['jobName'], required_assemblies=request.json['reqAssemblies'],
                       allotted_time=request.json['targetTime'], last_step_time=request.json['lastStep'])
    # Cameras.update_station(request.json['camData']['cam_uuid'], request.json['statData']['station_uuid'])
    # Cameras.update_ai_model(request.json['camData']['cam_uuid'], request.json['aiData']['ai_uuid'])
    return create_response(message="Success: add job", data=job.job_uuid, code=201)


@blueprint.route("/jobs/get_assoc_camera/<job_uuid>")
def job_get_assoc_camera(job_uuid):
    camera_list = [cam.toJson() for cam in Jobs.get_assoc_cameras(job_uuid)]
    return create_response(message="Success", data=camera_list, code=200)


######################
### STATION ROUTES ###
######################

@blueprint.route("/stations", methods=['GET'])
def get_stations():
    stations_list = [stat.toJson() for stat in Stations.get_all_stations()]
    return create_response(message="Success", data=stations_list, code=200)


@blueprint.route("/stations/<station_uuid>", methods=['GET'])
def get_station(station_uuid):
    station = Stations.get_station(station_uuid).toJson()
    return create_response(message="Success", data=station, code=200)


@blueprint.route("/stations", methods=['POST'])
def add_station():
    Stations.add_station(request.json['data'])
    return create_response(message="Success: added station", code=200)


@blueprint.route("/stations/<station_uuid>", methods=['DELETE'])
def delete_station(station_uuid):
    Stations.delete_station(station_uuid)
    return create_response(message="Success: deleted station", code=200)


@blueprint.route("/stations/page/<station_uuid>")
def station_page(station_uuid):
    return create_response(data={"station_uuid": station_uuid}, code=200)


@blueprint.route("/stations/get_assoc_camera/<station_uuid>")
def stat_get_assoc_camera(station_uuid):
    camera_list = [cam.toJson() for cam in Stations.get_assoc_cameras(station_uuid)]
    return create_response(message="Success", data=camera_list, code=200)


@blueprint.route("stations/update/job", methods=['PUT'])
def update_job():
    Stations.update_job(request.json['station_uuid'], request.json['job_uuid'])
    camera_list = [cam.toJson() for cam in Stations.get_assoc_cameras(request.json['station_uuid'])]

    for cam in camera_list:
        CamHandler.rm_cam_stream_obj(cam['cam_uuid'])
        CamHandler.add_cam_stream_obj(cam['cam_uuid'])

    return create_response(message="Success", code=200)


######################
### CAMERA ROUTES ####
######################

@blueprint.route("/cameras", methods=['GET'])
def get_all_cameras():
    cameras_list = [cam.toJson() for cam in Cameras.get_all_cameras()]
    return create_response(message="Success", data=cameras_list, code=200)


@blueprint.route("/cameras/<cam_uuid>", methods=['GET'])
def get_camera(cam_uuid):
    camera = Cameras.get_camera(cam_uuid).toJson()
    return create_response(message="Success", data=camera, code=200)


@blueprint.route("/cameras", methods=['POST'])
def add_camera():
    r = request.json['data']
    Cameras.add_camera(cam_name=r['cam_name'],
                       cam_ip=r['cam_ip'],
                       cam_type=r['cam_type'])
    return create_response(message="Success: add cameras", code=201)


@blueprint.route("/cameras/<cam_uuid>", methods=['DELETE'])
def delete_camera(cam_uuid):
    Cameras.delete_camera(cam_uuid)
    return create_response(message="Success: deleted camera", code=200)


@blueprint.route("/avail_cameras")
def get_avail_cameras():
    avail_cameras_list = []
    finder = Finder()
    mock = finder.get_mock_data()
    nxt_cameras = finder.detect()
    nxt_cameras.update(mock)

    for key in nxt_cameras:
        if Cameras.is_ip_unique(key):
            avail_cameras_list.append({"cam_name": nxt_cameras[key]["DeviceData"]["Serialnumber"],
                                       "cam_type": "NXT", "cam_ip": key
                                       })

    return create_response(message="Success: avail cameras", data=avail_cameras_list, code=200)


@blueprint.route("/cameras/update/station", methods=['PUT'])
def update_station():
    Cameras.update_station(request.json['cam_uuid'], request.json['station_uuid'])
    CamHandler.refresh_stream_obj(request.json['cam_uuid'])
    return create_response(message="Success: updated station", code=200)


@blueprint.route("/cameras/update/ai_model", methods=['PUT'])
def update_ai_model():
    Cameras.update_ai_model(request.json['cam_uuid'], request.json['ai_uuid'])
    CamHandler.refresh_stream_obj(request.json['cam_uuid'])
    return create_response(message="Success: updated station", code=200)


######################
### AI ROUTES ########
######################

@blueprint.route("/ai_models")
def get_ai_models():
    model_list = [mod.toJson() for mod in AiModels.get_all_ai_models()]
    for (idx, mod) in enumerate(model_list):
        model_list[idx]['model_labels'] = model_list[idx]['model_labels'].replace(",", ", ")

    return create_response(message="Success", data=model_list, code=200)


@blueprint.route("/ai_models", methods=['POST'])
def add_ai_model():
    r = request.json['data']
    AiModels.add_ai_model(name=r['name'], model_type=r['model_type'], model_location="app/ai/" + r["model_location"],
                          model_labels=r['model_labels'])
    return create_response(message="Success: add cameras", code=201)


@blueprint.route("/ai_models/<ai_uuid>", methods=['DELETE'])
def delete_ai_model(ai_uuid):
    AiModels.delete_ai_model(ai_uuid)
    return create_response(message="Success: deleted camera", code=200)


@blueprint.route("ai_models/train", methods=['POST'])
def train_model():
    r = request.json['data']
    ai_func.split_training_video(r)
    return create_response(message="Success: training model", code=200)


@blueprint.route("/ai_models/avail_models")
def get_avail_models():
    model_db_list = [mod.toJson()['model_location'] for mod in AiModels.get_all_ai_models()]

    path = str(os.getcwd()) + "/app/ai/ai_models"
    model_files = [f for f in listdir(path) if isfile(join(path, f))]

    model_list = [files for files in model_files if "app/ai/ai_models/" + files not in model_db_list]
    return create_response(message="Success", data=model_list, code=200)


@blueprint.route("/ai_models/avail_videos")
def get_avail_videos():
    path = str(os.getcwd()) + "/app/base/static/data/videos"
    videos = [f for f in listdir(path) if f[-3:] == "mp4" and isfile(join(path, f))]

    return create_response(message="Success", data=videos, code=200)


@blueprint.route("/ai_models/delete_video/<video_path>", methods=['DELETE'])
def delete_video(video_path):
    path = str(os.getcwd()) + "/app/base/static/data/videos/"

    if os.path.exists(path + video_path):
        os.remove(path + video_path)
        print("Deleting: " + video_path)
        return create_response(message="Success", code=200)
    else:
        return create_response(message="Not Found", code=404)
