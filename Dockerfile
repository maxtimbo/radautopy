FROM rclone/rclone:1.75.1 AS rclone

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*
# Debian's rclone is too old for `rclone gui`; keep app and GUI on the same version
COPY --from=rclone /usr/local/bin/rclone /usr/local/bin/rclone
# Drop the UTC symlink so a mounted host /etc/localtime is read as a real file
RUN rm -f /etc/localtime

RUN groupadd --gid 1000 radautopy \
    && useradd --uid 1000 --gid radautopy --create-home --shell /usr/sbin/nologin radautopy

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src/ src/
RUN pip install --no-cache-dir .

ENV RADAUTOPY_ROOT=/data
ENV RCLONE_CONFIG=/data/rclone.conf
RUN mkdir -p /data && chown -R radautopy:radautopy /data
VOLUME /data

USER radautopy

EXPOSE 8000
CMD ["radautopy-scheduler"]
