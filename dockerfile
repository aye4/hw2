FROM python:3.10-alpine

COPY /hw2 .

cmd ["python", "bot.py"]
