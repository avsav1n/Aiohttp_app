FROM python:3.12-alpine as builder
COPY ./requirements.txt /app/requirements.txt
RUN python3 -m venv /app/venv
RUN /app/venv/bin/pip install -r /app/requirements.txt

FROM python:3.12-alpine
WORKDIR /app
COPY --from=builder /app/venv /app/venv
COPY . .
ENV PYHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH=/app/venv/bin:$PATH
EXPOSE 8000
ENTRYPOINT [ "/app/docker-entrypoint.sh" ]