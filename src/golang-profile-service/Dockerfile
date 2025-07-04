FROM golang:1.24-alpine AS builder

LABEL maintainer="Satyabrata <satyabrata.7059@gmail.com>"

WORKDIR /app

COPY go.mod go.sum* ./

RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

# multi stage build

FROM scratch

WORKDIR /root/

COPY --from=builder /app/main .


EXPOSE 8080

CMD ["./main"]