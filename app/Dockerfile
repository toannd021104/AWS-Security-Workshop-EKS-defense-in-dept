FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
ADD https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem /app/rds-ca.pem
RUN chmod 644 /app/rds-ca.pem
COPY main.py .
USER 10001:10001
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "main.py"]
