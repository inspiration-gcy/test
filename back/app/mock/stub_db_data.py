from app import db

from app.base.models import Users
from app.home.models import Jobs, Stations, Cameras, AiModels


def create_stub_data():
    db.create_all()

    # Login stubs
    username = "ANA"
    email = "ana@ana.com"
    password = "ana"

    user_exist = Users.query.filter_by(username=username).first()
    email_exist = Users.query.filter_by(email=email).first()

    if not user_exist and not email_exist:
        user = Users(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()

    # Station stubs
    station_uuid = ["STUB-STAT-0jodin", "STUB-STAT-asodin", "STUB-STAT-090jnjopn", "STUB-STAT-bogdoin"]
    station_id = [234215, 636334, 545375, 533214]
    operator = ["Jimmy", "Bob", "Alice", "Harry"]

    job_id = ["STUB-adfa24e12", "", "", ""]

    for idx, sid in enumerate(station_id):
        station_exist = Stations.query.filter_by(name=sid).first()
        if not station_exist:
            station = Stations(station_uuid=station_uuid[idx], name=sid, operator=operator[idx], job_uuid=job_id[idx])
            db.session.add(station)
            db.session.commit()

    # Job stubs
    job_uuid = "STUB-adfa24e12"
    job_name = "SMART Plugs"
    required_assemblies = 6000
    allotted_time = 30000

    job_exist = Jobs.query.filter_by(job_uuid=job_uuid).first()
    if not job_exist:
        job = Jobs(job_uuid=job_uuid, job_name=job_name, required_assemblies=required_assemblies,
                   allotted_time=allotted_time)
        db.session.add(job)
        db.session.commit()

    job_uuid = "STUB-asadf22112"
    job_name = "SMART Toast"
    required_assemblies = 200

    job_exist = Jobs.query.filter_by(job_uuid=job_uuid).first()
    if not job_exist:
        job = Jobs(job_uuid=job_uuid, job_name=job_name, required_assemblies=required_assemblies,
                   allotted_time=allotted_time)
        db.session.add(job)
        db.session.commit()

    # AI model stubs
    ai_uuid = "STUB-AIas09"
    ai_name = "STUB-AINAME"
    model_type = "classifier"
    location = "app/mock/ai_models/test.cnn"
    labels = "background, empty, top pin, left pin, right pin, clip, fuse, back, screw, paper, complete"

    ai_exist = AiModels.query.filter_by(ai_uuid=ai_uuid).first()
    if not ai_exist:
        ai = AiModels(ai_model_uuid=ai_uuid, name=ai_name, model_type=model_type, model_location=location,
                      model_labels=labels)
        db.session.add(ai)
        db.session.commit()

    # AI model stubss
    ai_uuid = "STUB-NXT-AIas09"
    ai_name = "STUB-NXT"
    model_type = "classifier"
    location = "app/mock/ai_models/PlugSimple.cnn"
    labels = "BackgroundActivity, Step_01, Step_02, Step_03, Step_04, Step_05, Step_06, Step_07, Step_08, Step_09, Step_10"

    ai_exist = AiModels.query.filter_by(ai_uuid=ai_uuid).first()
    if not ai_exist:
        ai = AiModels(ai_model_uuid=ai_uuid, name=ai_name, model_type=model_type, model_location=location,
                      model_labels=labels)
        db.session.add(ai)
        db.session.commit()

    # Camera stubs
    cam_uuid = "STUB-adfosnaoi809"
    cam_name = "STUB-camera0002"
    cam_ip = "STUB.434.214.345"
    cam_type = "STUB"
    station_uuid = "STUB-STAT-0jodin"
    ai_model = "STUB-AIas09"

    cam_exist = Cameras.query.filter_by(name=cam_name).first()
    if not cam_exist:
        cam = Cameras(cam_uuid=cam_uuid, cam_name=cam_name, cam_ip=cam_ip, cam_type=cam_type, station_uuid=234215,
                      ai_model_uuid=ai_model)
        db.session.add(cam)
        db.session.commit()


def db_has_entry(uuid):
    pass
    # check db for uuid and add entry is absent
