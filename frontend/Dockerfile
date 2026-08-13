# Development image for the Conduit frontend (CRA dev server).
#
# Application code is bind-mounted by docker-compose.yml so edits on the
# host trigger CRA's hot reload without rebuilding the image; node_modules
# stays inside the image/named volume so the container's own install
# (Linux binaries) is never shadowed by a host bind mount.
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# The CRA dev server defaults to binding "localhost", which is unreachable
# from outside the container network namespace.
ENV HOST=0.0.0.0
# File-watch events from bind mounts aren't always delivered on Windows/macOS
# Docker hosts; polling makes hot reload reliable everywhere.
ENV CHOKIDAR_USEPOLLING=true
ENV WATCHPACK_POLLING=true

EXPOSE 4100

CMD ["npm", "start"]
