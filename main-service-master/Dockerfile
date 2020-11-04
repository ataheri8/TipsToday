FROM python:3.7-alpine

RUN apk --update add bash \
    supervisor \
    zip \
    openssl \
    openssh \
    python-dev \
    curl \
    curl-dev \
    libffi-dev \
    make \
    gcc \
    g++ \
    git \
    linux-headers \
    musl-dev \
    pcre-dev \
    libpq \
    postgresql-dev \
    postgresql-client \
    zlib-dev && \
    python -m ensurepip && \
rm -r /usr/lib/python*/ensurepip

COPY requirements.txt /requirements.txt
    
RUN pip install --upgrade pip setuptools && \
    pip install -r /requirements.txt && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    rm -r /root/.cache && \
    mkdir -p /srv/root && \
    mkdir -p /var/log/supervisor && \
    mkdir -p /srv/root/static && \
    apk del gcc linux-headers musl-dev make libffi-dev g++ git

ADD conf/supervisord.conf /etc/supervisord.conf

ADD conf/fis-certificate.pfx /fis-certificate.pfx

# Add Scripts
ADD scripts/ /scripts
RUN chmod 755 /scripts/*

# copy in code
ADD mount/ /srv/root/

EXPOSE 80

CMD ["/scripts/start.sh"]
