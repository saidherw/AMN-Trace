FROM python:3.12-slim
WORKDIR /app
COPY amn_trace_mvp.py README_MVP.md ./
RUN mkdir -p /app/data/evidence
ENV WEB_MODE=true
ENV PYTHONUNBUFFERED=1
EXPOSE 10000
CMD ["python", "amn_trace_mvp.py"]
