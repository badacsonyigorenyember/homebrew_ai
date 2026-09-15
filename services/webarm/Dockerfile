# Stdlib only — no pip, no requirements file, nothing to drift.
FROM python:3.12-slim
WORKDIR /app
COPY webarm.py /app/webarm.py
EXPOSE 5055
CMD ["python", "-u", "/app/webarm.py"]
