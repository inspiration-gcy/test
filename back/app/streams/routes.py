from flask import request, Response

from app.base.util import create_response
from app.streams import blueprint
from app.streams.camstreaming import CamHandler


######################
### STREAM ROUTES ####
######################

@blueprint.route("/video_feed/<cam_uuid>")
def video_feed(cam_uuid):
    cam_streamer = CamHandler.get_cam_stream_obj(cam_uuid)
    if cam_streamer:
        return Response(cam_streamer.get_video(), status=200, mimetype="multipart/x-mixed-replace; boundary=frame")
    else:
        return create_response(message="Fail: Cannot find camera", code=404)


@blueprint.route("/video_feed/start_record", methods=['PUT'])
def video_start_record():
    for cam in request.json['data']:
        cam_streamer = CamHandler.get_cam_stream_obj(cam['cam_uuid'])
        cam_streamer.start_record(cam['fileName'])
    return create_response(message="Success", code=200)


@blueprint.route("/video_feed/stop_record", methods=['PUT'])
def video_stop_record():
    for cam in request.json['data']:
        cam_streamer = CamHandler.get_cam_stream_obj(cam['cam_uuid'])
        cam_streamer.stop_record()
    return create_response(message="Success", code=200)


@blueprint.route("/job_data/<cam_uuid>")
def job_data(cam_uuid):
    cam_streamer = CamHandler.get_cam_stream_obj(cam_uuid)
    if cam_streamer:
        return Response(cam_streamer.get_job_data(), status=200, content_type='text/event-stream')
    else:
        return create_response(message="Fail: Cannot find camera", code=404)


@blueprint.route("/cam_handler/refresh/", methods=['PUT'])
def refresh_camhandler():
    CamHandler.rm_cam_stream_obj(request.json['cam_uuid'])
    CamHandler.add_cam_stream_obj(request.json['cam_uuid'])
    return create_response(message="Success", code=200)
