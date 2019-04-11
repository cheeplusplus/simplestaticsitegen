FROM python:3.7-alpine

LABEL maintainer="Kauko <kauko@biosynth.link>" \
  org.label-schema.name="SSSG Drone Plugin" \
  org.label-schema.vendor="Kauko" \
  org.label-schema.schema-version="1.0"

# Add git for pipenv dep on sssg
RUN apk --update add git openssh && \
    rm -rf /var/lib/apt/lists/* && \
    rm /var/cache/apk/*

# Install SSSG
RUN pip install git+https://github.com/cheeplusplus/simplestaticsitegen.git#egg=sssg

# Handle buildscript
COPY build.py /usr/local
ENTRYPOINT ["python", "/usr/local/build.py"]
