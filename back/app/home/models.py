from app import db

from sqlalchemy import Binary, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.streams.camstreaming import CamHandler
from app.streams.nxt.nxt_stream import NxtCameraStream

import json
import uuid

class Jobs(db.Model):

    __tablename__ = 'jobs'

    job_uuid = Column(String, primary_key=True, unique=True, nullable=False)
    name = Column(String)
    required_assemblies = Column(Integer)
    allotted_time = Column(Integer)
    last_step_time = Column(Integer)

    assoc_station = relationship("Stations", back_populates="assoc_job")

    def __init__(self, job_name, required_assemblies, allotted_time, job_uuid=None, last_step_time=10):

        if (job_uuid):
            self.job_uuid = job_uuid
        else: 
            self.job_uuid = str(uuid.uuid4())

        self.name = job_name
        self.required_assemblies = required_assemblies
        self.allotted_time = allotted_time
        self.last_step_time = last_step_time


    @classmethod
    def add_job(cls, job_name, required_assemblies, allotted_time, last_step_time):
        new_job= cls(job_name=job_name,required_assemblies=required_assemblies, allotted_time=allotted_time, last_step_time=last_step_time)

        db.session.add(new_job)
        db.session.commit()

        print("###### Added new job to db: ")
        print(new_job)
        return new_job

    @staticmethod
    def get_all_jobs():
        return Jobs.query.all()

    @staticmethod
    def get_job(job_uuid):
        return Jobs.query.filter_by(job_uuid=job_uuid).one()

    @staticmethod
    def get_assoc_cameras(job_uuid):
        cam_list = []
        job = Jobs.query.filter_by(job_uuid=job_uuid).one()
        
        if (job.assoc_station):
            for stat in job.assoc_station:
                cam_list.append(Stations.get_assoc_cameras(stat.station_uuid))    
        flattened_list = [y for x in cam_list for y in x]
        return flattened_list
    
    @staticmethod
    def get_assoc_ai_models(job_uuid):
        return [cam.assoc_ai_model for cam in Jobs.get_assoc_cameras(job_uuid)]
    
    @staticmethod
    def delete_job(job_uuid):
        job = Jobs.query.filter_by(job_uuid=job_uuid).one()
        db.session.delete(job)
        db.session.commit()

        print("###### Deleted job from db: ")
        print(job)

    def toJson(self):
        return {"job_uuid": self.job_uuid,
                "job_name": self.name,
                "assoc_stations": [stat.toJson() if (stat) else None for stat in self.assoc_station],
                "assoc_cameras": [cam.toJson() if (cam) else None for cam in self.get_assoc_cameras(self.job_uuid)],
                "assoc_ai_models": [ai.toJson() if (ai) else None for ai in self.get_assoc_ai_models(self.job_uuid)]}

    def __repr__(self):
        return str({"job_uuid": self.job_uuid,
                    "job_name": self.name})


class Stations(db.Model):

    __tablename__ = 'stations'

    station_uuid = Column(String, primary_key=True, unique=True, nullable=False)
    name = Column(String, unique=True)
    operator = Column(String)
    job_uuid = Column(Integer, ForeignKey('jobs.job_uuid'))

    assoc_job = relationship("Jobs", back_populates="assoc_station")
    assoc_cameras = relationship("Cameras", back_populates="assoc_station")

    def __init__(self, name, station_uuid=None, operator=None, job_uuid=None):

        if (station_uuid):
            self.station_uuid = station_uuid
        else: 
            self.station_uuid = str(uuid.uuid4())

        self.name = name
        self.operator = operator
        self.job_uuid = job_uuid

    @staticmethod
    def get_all_stations():
        return Stations.query.all()

    @staticmethod
    def get_station(station_uuid):
        return Stations.query.filter_by(station_uuid=station_uuid).one()

    @staticmethod
    def get_assoc_cameras(station_uuid):
        station = Stations.query.filter_by(station_uuid=station_uuid).one()
        if (station):
            return [cam for cam in station.assoc_cameras]
        else:
            return []

    @classmethod
    def add_station(cls, station_name):
        new_station = cls(name=station_name)
        db.session.add(new_station)
        db.session.commit()

        print("###### Added new station to db: ")
        print(new_station)
        return new_station

    @staticmethod
    def delete_station(station_uuid):
        station = Stations.query.filter_by(station_uuid=station_uuid).one()
        cam = station.assoc_cameras
        db.session.delete(station)
        db.session.commit()

        print("###### Deleted station from db: ")
        print(station)
        for c in cam:
            CamHandler.refresh_stream_obj(c.cam_uuid)

    @classmethod
    def update_job(cls, station_uuid, job_uuid):
        station = cls.get_station(station_uuid)
        if (station.assoc_job):
            print("Old job on station: " + station.assoc_job.job_uuid)
            Jobs.delete_job(station.assoc_job.job_uuid)

        station.assoc_job = Jobs.get_job(job_uuid)
        print("Add new job to station: " + station.assoc_job.job_uuid)
        db.session.commit()
        return True

    def toJson(self):
        return {"station_uuid": self.station_uuid,
                "station_name": self.name,
                "station_cams": [cam.cam_uuid for cam in self.assoc_cameras]}
    
    def __repr__(self):
        return str({"station_uuid": self.station_uuid,
                "station_name": self.name})



class Cameras(db.Model):

    __tablename__ = "cameras"

    cam_uuid = Column(String, primary_key=True, unique=True, nullable=False)
    name = Column(String)
    ip = Column(String)
    cam_type = Column(String)
    station_uuid = Column(Integer, ForeignKey('stations.name'))
    ai_model_uuid = Column(String, ForeignKey('ai_model.ai_uuid'))
    
    assoc_station = relationship("Stations", back_populates="assoc_cameras")
    assoc_ai_model = relationship("AiModels", back_populates="assoc_cameras")

    def __init__(self, cam_name, cam_ip, cam_type, cam_uuid=None, station_uuid="", ai_model_uuid=""):

        if (cam_uuid):
            self.cam_uuid = cam_uuid
        else: 
            self.cam_uuid = str(uuid.uuid4())
 
        self.name = cam_name
        self.ip = cam_ip
        self.cam_type = cam_type
        self.station_uuid = station_uuid
        self.ai_model_uuid = ai_model_uuid

    @staticmethod
    def get_all_cameras():
        return Cameras.query.all()
    
    @staticmethod
    def get_camera(cam_uuid):
        return Cameras.query.filter_by(cam_uuid=cam_uuid).one()

    @staticmethod
    def get_ip_address(cam_uuid):
        return Cameras.query.filter_by(cam_uuid=cam_uuid).one().ip
        
    @staticmethod
    def is_ip_unique(cam_ip):
        return Cameras.query.filter_by(ip=cam_ip).scalar() is None


    def get_assoc_ai_models(self):
        if (self.assoc_ai_model):
            return self.assoc_ai_model.toJson()
        else:
            return None
    
    def get_assoc_stations(self):
        if (self.assoc_station):
            return self.assoc_station.toJson()
        else:
            return None
    
    @classmethod
    def add_camera(cls, cam_name, cam_ip, cam_type):
        new_cam = cls(cam_name=cam_name, cam_ip=cam_ip, cam_type=cam_type)
        db.session.add(new_cam)
        db.session.commit()
        CamHandler.add_cam_stream_obj(new_cam.cam_uuid)

        print("###### Added new camera to db: ")
        print(new_cam)
        return new_cam

    @classmethod
    def update_station(cls, cam_uuid, station_uuid):
        camera = cls.get_camera(cam_uuid)
        camera.assoc_station = Stations.get_station(station_uuid)
        db.session.commit()

    @classmethod
    def update_ai_model(cls, cam_uuid, ai_uuid):
        ai_model = AiModels.get_ai_model(ai_uuid)
        camera = cls.get_camera(cam_uuid)
        camera.assoc_ai_model = ai_model
        db.session.commit()

        print("updating ai")
        
        if (camera.cam_type == "NXT"):
            CamHandler.rm_cam_stream_obj(cam_uuid)
            nxt_cam = NxtCameraStream(camera.ip)
            nxt_cam.upload_cnn_model(ai_model.location)
            nxt_cam.switch_cnn_model(ai_model.name)

    @staticmethod
    def delete_camera(cam_uuid):
        cam = Cameras.query.filter_by(cam_uuid=cam_uuid).one()
        CamHandler.rm_cam_stream_obj(cam_uuid)
        db.session.delete(cam)
        db.session.commit()
    

    def toJson(self):
        return {"cam_uuid": self.cam_uuid, 
                "cam_name": self.name,
                "cam_ip": self.ip, 
                "cam_type": self.cam_type,
                "cam_assoc_ai_model": self.get_assoc_ai_models(),
                "cam_station": self.get_assoc_stations()}

    def __repr__(self):
        return str({"cam_name": self.name,
                    "cam_ip": self.ip})


class AiModels(db.Model):

    __tablename__ = "ai_model"

    ai_uuid = Column(String, primary_key=True, unique=True, nullable=False)
    name = Column(String)
    model_type = Column(String)
    location = Column(String)
    labels = Column(String)
    
    assoc_cameras = relationship("Cameras", back_populates="assoc_ai_model")

    def __init__(self, name, model_type, model_location, model_labels, ai_model_uuid=None):

        if (ai_model_uuid):
            self.ai_uuid = ai_model_uuid
        else: 
            self.ai_uuid = str(uuid.uuid4())

        self.name = name
        self.model_type = model_type
        self.location = model_location

        labels = model_labels.split(",")
        labels = [l.strip() for l in labels]
        self.labels = ",".join(labels)

    @staticmethod
    def get_all_ai_models():
        return AiModels.query.all()

    @staticmethod
    def get_ai_model(ai_uuid):
        return AiModels.query.filter_by(ai_uuid=ai_uuid).one()

    @classmethod
    def add_ai_model(cls, name, model_type, model_location, model_labels):
        new_ai = cls(name=name, model_type=model_type, model_location=model_location, model_labels=model_labels)
        db.session.add(new_ai)
        db.session.commit()

        print("###### Added new AI model to db: ")
        print(new_ai)
        return new_ai

    @staticmethod
    def delete_ai_model(ai_uuid):
        ai = AiModels.query.filter_by(ai_uuid=ai_uuid).one()
        cams = ai.assoc_cameras
        db.session.delete(ai)
        db.session.commit()

        print("###### Deleted ai from db: ")
        print(ai)
        for c in cams:
            CamHandler.refresh_stream_obj(c.cam_uuid)

    def toJson(self):
        return {"ai_uuid": self.ai_uuid,
                "name": self.name,
                "model_type": self.model_type,
                "model_labels": self.labels,
                "model_location":self.location}

    def __repr__(self):
        return str({"ai_uuid": self.ai_uuid,
                    "name": self.name})