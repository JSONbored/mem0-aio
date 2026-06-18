# checkov:skip=CKV_DOCKER_3: s6 init coordinates multiple bundled services before they drop privileges, so this image does not use a single final USER instruction
# checkov:skip=CKV_DOCKER_7: the qdrant helper stage is pinned by immutable digest instead of a mutable tag
# checkov:skip=CKV_DOCKER_9: package versions are resolved with apt-cache madison before apt-get install
FROM jsonbored/aio-base:s6-3.2.1.0 AS aio-base

FROM node:24-slim@sha256:879b21aec4a1ad820c27ccd565e7c7ed955f24b92e6694556154f251e4bdb240 AS ui-builder

# Enable corepack for pnpm
RUN corepack enable

WORKDIR /build/ui
# Copy package files first to cache dependencies
COPY openmemory/openmemory/ui/package.json openmemory/openmemory/ui/pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile || npm install

# Copy source and build
COPY openmemory/openmemory/ui/ ./
# Route browser traffic back through the single published UI port.
COPY docker/next.config.mjs /build/ui/next.config.mjs
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=/openmemory-api
ENV NEXT_PUBLIC_USER_ID=default_user
RUN pnpm build || npm run build

ARG UPSTREAM_VERSION=v2.0.6
FROM qdrant/qdrant@sha256:94728574965d17c6485dd361aa3c0818b325b9016dac5ea6afec7b4b2700865f AS qdrant-bin

FROM ubuntu:26.04@sha256:5e275723f82c67e387ba9e3c24baa0abdcb268917f276a0561c97bef9450d0b4 AS runtime-base
ARG TARGETARCH

COPY --from=qdrant-bin /etc/ssl/certs /etc/ssl/certs
COPY --from=qdrant-bin /etc/ca-certificates.conf /etc/ca-certificates.conf
COPY --from=qdrant-bin /usr/share/ca-certificates /usr/share/ca-certificates
COPY docker/normalize-apt-sources.sh /usr/local/bin/normalize-apt-sources

# Install system dependencies, python, nodejs
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
# Normalize only official Ubuntu archive URIs to HTTPS and fail closed before
# package metadata is fetched.
# hadolint ignore=DL3008
RUN printf 'Acquire::Retries "3";\nAcquire::Queue-Mode "host";\nAcquire::ForceIPv4 "true";\nAcquire::http::Pipeline-Depth "0";\nAcquire::https::Pipeline-Depth "0";\nAcquire::http::Timeout "20";\nAcquire::https::Timeout "20";\nAcquire::https::CaInfo "/etc/ssl/certs/ca-certificates.crt";\nAcquire::https::Verify-Peer "true";\nAcquire::https::Verify-Host "true";\nAcquire::Check-Valid-Until "true";\nAcquire::AllowInsecureRepositories "false";\nAcquire::AllowDowngradeToInsecureRepositories "false";\nAPT::Update::Error-Mode "any";\n' > /etc/apt/apt.conf.d/80-retries && \
    chmod +x /usr/local/bin/normalize-apt-sources && \
    grep -Rqs '^Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg' /etc/apt && \
    /usr/local/bin/normalize-apt-sources && \
    apt_update_ok=0 && \
    for attempt in 1 2 3; do \
        if apt-get update; then apt_update_ok=1; break; fi; \
        rm -rf /var/lib/apt/lists/*; \
        sleep "$((attempt * 3))"; \
    done && \
    test "${apt_update_ok}" = "1" && \
    required_packages=( \
        ca-certificates \
        curl \
        xz-utils \
        tzdata \
        python3 \
        python3-pip \
        python3-venv \
        patch \
        libunwind8 \
    ) && \
    install_packages=() && \
    for package in "${required_packages[@]}"; do \
        version="$(apt-cache madison "${package}" | awk 'NR==1 {print $3}')"; \
        if [[ -z "${version}" ]]; then \
            echo "unable to resolve apt package version: ${package}" >&2; \
            exit 1; \
        fi; \
        install_packages+=("${package}=${version}"); \
    done && \
    apt-get install -y --no-install-recommends "${install_packages[@]}" \
    && rm -rf /var/lib/apt/lists/*

FROM runtime-base AS runtime
ARG TARGETARCH
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install Node.js 24 to match the UI builder runtime.
RUN curl -fsSL https://deb.nodesource.com/setup_24.x -o /tmp/nodesource_setup.sh && \
    bash /tmp/nodesource_setup.sh && \
    rm -f /tmp/nodesource_setup.sh && \
    apt-get install -y --no-install-recommends nodejs="$(apt-cache madison nodejs | awk 'NR==1 {print $3}')" && \
    rm -rf /var/lib/apt/lists/*

# Setup python virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY --from=qdrant-bin /qdrant/qdrant /usr/local/bin/qdrant
COPY --from=qdrant-bin /qdrant/config /qdrant/config
COPY --from=qdrant-bin /qdrant/static /qdrant/static

# Install S6 Overlay
# Shared, pinned s6-overlay from the fleet aio-base overlay.
COPY --from=aio-base /aio-overlay/ /

# Setup App Directory
WORKDIR /app

# Copy API files
COPY openmemory/openmemory/api/ /app/api/
COPY docker/patches/ /tmp/patches/
WORKDIR /app/api
RUN patch -l -p2 < /tmp/patches/openmemory-api.patch && \
    pip install -r requirements.txt && \
    rm -rf /tmp/patches
WORKDIR /app

# Copy standalone UI runtime from Stage 1
COPY --from=ui-builder /build/ui/public /app/ui/public
COPY --from=ui-builder /build/ui/.next/standalone /app/ui/
COPY --from=ui-builder /build/ui/.next/static /app/ui/.next/static
COPY --from=ui-builder /build/ui/entrypoint.sh /app/ui/entrypoint.sh
RUN sed -i 's|cd /app|cd /app/ui|' /app/ui/entrypoint.sh
COPY openmemory/openmemory/backup-scripts/ /app/backup-scripts/

# Setup S6 configuration
COPY rootfs/ /
RUN rm -rf \
    /etc/s6-overlay/s6-rc.d/fastapi \
    /etc/s6-overlay/s6-rc.d/nextjs \
    /etc/s6-overlay/s6-rc.d/qdrant && \
    rm -f \
    /etc/s6-overlay/s6-rc.d/user/contents.d/fastapi \
    /etc/s6-overlay/s6-rc.d/user/contents.d/nextjs \
    /etc/s6-overlay/s6-rc.d/user/contents.d/qdrant && \
    chmod +x /app/ui/entrypoint.sh && \
    find /app/backup-scripts -type f -name "*.sh" -exec chmod +x {} \; && \
    find /etc/cont-init.d -type f -exec chmod +x {} \; && \
    find /etc/services.d -type f -name "run" -exec chmod +x {} \;

# Set environment variables for services
ENV QDRANT__STORAGE__STORAGE_PATH=/mem0/storage
ENV QDRANT__TELEMETRY_DISABLED=true
ENV RUN_MODE=production
ENV QDRANT_HOST=127.0.0.1
ENV QDRANT_PORT=6333
ENV DATABASE_URL=sqlite:////mem0/storage/openmemory.db
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=/openmemory-api
ENV NEXT_PUBLIC_USER_ID=default_user
ENV USER=default_user
ENV MEM0_API_HOST=127.0.0.1
ENV HOST="0.0.0.0"
ENV PORT="3000"

# Volumes
VOLUME ["/mem0/storage"]

# Expose ports: UI (3000), Qdrant (6333). The MCP/API service binds to localhost by default.
EXPOSE 3000 6333

ENV S6_CMD_WAIT_FOR_SERVICES_MAXTIME=300000
ENV S6_BEHAVIOUR_IF_STAGE2_FAILS=2

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=5 \
  CMD sh -lc 'IP=$(hostname -i | awk "{print \$1}"); curl -fsS "http://${IP}:3000/" >/dev/null || exit 1'

# Start s6 init
ENTRYPOINT ["/init"]
