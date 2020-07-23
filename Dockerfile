FROM alpine:3.12

WORKDIR /usr/src

RUN apk update; \
    apk add --no-cache python3 py3-pip zfs; \
    python3 -m pip install prometheus_client; \
    #
    # create user
    addgroup -S zfs;\
    adduser -S zfs -G zfs;

ADD zfsprom.py .

USER zfs
EXPOSE 9901
ENTRYPOINT "./zfsprom.py"

