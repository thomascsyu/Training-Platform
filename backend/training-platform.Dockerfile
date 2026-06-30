FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

# Zeabur routes to port 8080; PORT can still override this for other platforms.
ENV PYTHONUNBUFFERED=1
CMD ["python", "-X", "faulthandler", "-u", "start.py"]
