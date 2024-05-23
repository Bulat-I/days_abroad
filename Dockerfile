FROM python:3.9-slim

WORKDIR /days_abroad

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT ["python", "app.py"]