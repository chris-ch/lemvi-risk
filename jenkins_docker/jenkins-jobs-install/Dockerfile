FROM openjdk:8-jdk-alpine

RUN apk --update add bash wget dpkg-dev
RUN adduser -D -g '' cli

USER cli
WORKDIR /home/cli

