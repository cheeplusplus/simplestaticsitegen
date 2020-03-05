FROM python:3.7-alpine

LABEL maintainer="Kauko <kauko@biosynth.link>" \
  org.label-schema.name="Simple Static Site Generator" \
  org.label-schema.vendor="Kauko" \
  org.label-schema.schema-version="1.0"

ENV VERSION 0.0.9

# Add git for pipenv dep on sssg
RUN apk --update add git openssh && \
    rm -rf /var/lib/apt/lists/* && \
    rm /var/cache/apk/*

# Install SSSG
WORKDIR /build/staging
RUN git clone -b $VERSION https://github.com/cheeplusplus/simplestaticsitegen.git sssg

RUN pip install /build/staging/sssg
RUN rm -rf /build/staging

# Handle buildscript
WORKDIR /build/run
COPY docker/build.py .
ENTRYPOINT ["python", "/build/run/build.py"]
