FROM python:3.10
COPY requirements.txt /usr/src/bot/requirements.txt
WORKDIR /usr/src/bot

RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
