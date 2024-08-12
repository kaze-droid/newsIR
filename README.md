# Semantic Search System using SENAN

## Description

This project implements a semantic search system for multilingual news articles across Southeast Asian languages.
It leverages a [bi-encoder](https://huggingface.co/Kaze-droid/SENAN-Raw) finetuned for multilingual semantic embeddings and Elasticsearch to enable efficient retrieval of news content with event-based and date-based filtering capabilities.

## Prerequisites

Ensure that Docker and Docker compose is installed

## Getting Started

First, initialize the Elasticsearch users and groups by executing the command:
```sh
docker-compose up setup
```

If the setup completed without error, startup the other stack components together with the frontend and backend:
```sh
docker-compose up
```

> [!NOTE]
> By default, Elasticsearch users are initialized with the values of the passwords defined in the .env file ("changeme" by default). For more details on changing users' passwords and other configuration, head to [docker-elk](https://github.com/deviantony/docker-elk/blob/main/README.md)

## Usage

Once the stack is up and running, the frontend can be accessed at http://localhost:3000 and the backend documentation at http://localhost:8000/docs


## Project Structure

- docker-elk/: Contains configuration for Elasticsearch, Logstash and Kibana
- frontend/: Contains the frontend application built in Next.js
- backend/: Contains the backend application code




