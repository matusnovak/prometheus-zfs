FROM ubuntu:latest

WORKDIR /usr/src

RUN apt-get update && \
    apt-get install --yes --no-install-recommends build-essential git python3 python3-dev python3-pip libzfslinux-dev

RUN python3 -m pip install setuptools prometheus_client Cython

RUN git clone https://github.com/truenas/py-libzfs.git /tmp/py-libzfs

RUN cd /tmp/py-libzfs && \
    ./configure --prefix=/usr && \
    make build && \
    python3 setup.py install

RUN apt-get remove --yes build-essential git python3-dev python3-pip libzfslinux-dev && rm -rf /var/lib/apt/lists/*

ADD zfsprom.py .

EXPOSE 9901
ENTRYPOINT "./zfsprom.py"
