FROM python:3.12-alpine

LABEL maintainer="Kauko <kauko@biosynth.link>" \
  org.label-schema.name="Simple Static Site Generator" \
  org.label-schema.vendor="Kauko" \
  org.label-schema.schema-version="1.0"

# Install SSSG
RUN mkdir -p /build/staging
COPY . /build/staging/

RUN pip install /build/staging
RUN rm -rf /build/staging

# Handle buildscript
RUN mkdir -p /build/run
COPY docker/build.py /build/run/
ENTRYPOINT ["python", "/build/run/build.py"]
