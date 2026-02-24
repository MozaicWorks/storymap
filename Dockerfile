FROM python:3.12-slim

RUN pip install --no-cache-dir storymap

WORKDIR /data

ENTRYPOINT ["storymap"]
CMD ["--help"]
