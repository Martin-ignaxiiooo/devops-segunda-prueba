FROM eclipse-temurin:21-jdk-alpine AS build
WORKDIR /app
COPY gradlew ./
COPY gradle ./gradle
COPY build.gradle settings.gradle gradle.properties ./
COPY src ./src
RUN chmod +x gradlew && ./gradlew bootJar -x test --no-daemon

FROM eclipse-temurin:21-jre-alpine AS runtime
WORKDIR /app
RUN apk --no-cache upgrade && apk --no-cache add curl \
    && addgroup -S -g 10001 appgroup && adduser -S -u 10001 -G appgroup appuser
COPY --from=build --chown=appuser:appgroup /app/build/libs/ep02-app-1.0.0.jar app.jar
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=5 \
  CMD curl --fail --silent http://127.0.0.1:8080/actuator/health || exit 1
ENTRYPOINT ["java", "-Xms64m", "-Xmx256m", "-XX:+UseSerialGC", "-XX:+ExitOnOutOfMemoryError", "-jar", "app.jar"]
