FROM node:20-alpine AS build

WORKDIR /app

COPY frontend/package.json frontend/yarn.lock* ./
RUN corepack enable && yarn install --frozen-lockfile

COPY frontend/ .

ARG REACT_APP_BACKEND_URL=http://localhost:8001
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

RUN yarn build

FROM node:20-alpine

WORKDIR /app

COPY frontend/static-server.js ./static-server.js
COPY --from=build /app/build ./build

EXPOSE 8080

# Zeabur routes to port 8080; PORT can still override this for other platforms.
CMD ["node", "static-server.js"]
