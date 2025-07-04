FROM --platform=$BUILDPLATFORM golang:1.24-alpine AS builder

WORKDIR /app


ENV CGO_ENABLED=0 GOOS=linux

COPY go.mod go.sum ./

RUN go mod download

COPY . .

RUN go build -a -installsuffix cgo -o profile-service main.go


FROM scratch

LABEL maintainer="Satyabrata <satyabrata.7059@gmail.com>"

WORKDIR /root/

COPY profile-service .


EXPOSE 8080

CMD ["./profile-service"]