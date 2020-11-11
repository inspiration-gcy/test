FROM python:3.6

ENV FLASK_APP run.py

COPY run.py gunicorn-cfg.py requirements.txt config.py  ./
COPY app app

RUN apt update -y && apt install libgl1-mesa-glx -y
RUN pip install -r requirements.txt

EXPOSE 5005
CMD ["gunicorn", "--config", "gunicorn-cfg.py", "run:app"]
