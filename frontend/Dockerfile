FROM node:18-alpine AS build

WORKDIR /app

COPY package.json yarn.lock* ./
RUN yarn install --frozen-lockfile || yarn install

COPY . .

ARG REACT_APP_BACKEND_URL=http://localhost:8001
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

RUN yarn build

FROM node:18-alpine

WORKDIR /app

RUN yarn global add serve

COPY --from=build /app/build ./build

EXPOSE 8080

# Zeabur routes to port 8080; PORT can still override this for other platforms.
CMD ["sh", "-c", "exec serve -s build -l ${PORT:-8080}"]
