FROM python:3.9

WORKDIR /app

COPY requirements.txt /app
COPY app.py /app
COPY templates/ /app/templates/
COPY images/ /app/images/
COPY style.css /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["python3", "app.py"]