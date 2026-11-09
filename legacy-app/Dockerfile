# The jar, in a container, so "it starts" answers a question instead of making a claim.
FROM maven:3.9-eclipse-temurin-8 AS build
WORKDIR /src
COPY pom.xml .
RUN mvn -B -q dependency:go-offline
COPY src ./src
RUN mvn -B -q -DskipTests package

FROM eclipse-temurin:8-jre
WORKDIR /app
COPY --from=build /src/target/legacy-svc-0.0.1-SNAPSHOT.jar app.jar
RUN mkdir -p /app/target
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
