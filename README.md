# Video-to-MP3 Conversion Service

## Overview

This project is a microservice-based application that allows users to upload videos, convert them to MP3 format, and download the converted files. It uses **Flask**, **RabbitMQ**, **MongoDB**, and **JWT** authentication for secure user management and task processing.

The system is composed of several services:
- **Authentication Service**: Manages user login and JWT validation.
- **Conversion Service**: Converts video files to MP3 format and stores them in MongoDB.
- **Notification Service**: Sends an email notification when the MP3 file is ready for download.
- **API Service**: Manages file uploads and downloads, utilizing the other services for handling authentication, video storage, and conversion.

## Architecture

The system is designed using Kubernetes for orchestration, with the following components:
- **Auth Service**: Handles user authentication and authorization.
- **Converter Service**: Converts videos to MP3 format.
- **Storage Service**: Stores video and MP3 files using **GridFS** with MongoDB.
- **Message Queue (RabbitMQ)**: Handles communication between services for video processing and task management.
- **Notification Service**: Sends email notifications to users when their MP3 files are ready.
- **Persistent Storage**: Ensures data persists using persistent volume claims.

## Services

### Authentication Service (`auth`)

This service handles user login and JWT-based authentication:
- **Login Endpoint** (`POST /login`): Accepts username and password, validates credentials against the database, and returns a JWT.
- **Validate Endpoint** (`POST /validate`): Validates the JWT provided in the Authorization header.

It is deployed with the following Kubernetes resources:
- **Deployment** (`auth-deploy.yaml`): Configures the service with 2 replicas.
- **ConfigMap** (`auth-configmap.yaml`): Stores MySQL and JWT secret configuration.
- **Secret** (`auth-secret.yaml`): Stores sensitive information like MySQL password and JWT secret.
- **Service** (`auth-service.yaml`): Exposes the authentication service within the cluster.

### Conversion Service (`converter`)

This service listens to a RabbitMQ queue, processes video files, converts them to MP3, and stores the results in MongoDB:
- **Consumes Videos**: Videos are retrieved from the queue, converted to MP3, and saved to MongoDB.
- **Uploads and Downloads**: The service provides endpoints to upload videos and download converted MP3 files.

It is deployed with the following Kubernetes resources:
- **Deployment** (`converter-deploy.yaml`): Configures the service with 4 replicas.
- **ConfigMap** (`converter-configmap.yaml`): Stores video and MP3 queue configuration.
- **Secret** (`converter-secret.yaml`): Stores any sensitive information related to the converter.

### Notification Service (`notification`)

This service listens to a RabbitMQ queue and sends email notifications to users when their MP3 files are ready:
- **Consumes MP3 messages**: It retrieves messages with the MP3 file information and sends an email notification to the user.
- **Deployment**: Configured with 4 replicas for high availability.

It is deployed with the following Kubernetes resources:
- **Deployment** (`notification-deploy.yaml`): Configures the service with 4 replicas.
- **ConfigMap** (`notification-configmap.yaml`): Stores MP3 and video queue configuration.
- **Secret** (`notification-secret.yaml`): Stores email credentials for sending notifications.

### RabbitMQ and Persistence (`rabbitmq`)

RabbitMQ is used for message queuing between services:
- **StatefulSet** (`statefulset.yaml`): Ensures that RabbitMQ runs with persistent storage.
- **PersistentVolumeClaim** (`pvc.yaml`): Requests persistent storage for RabbitMQ.
- **Service** (`service.yaml`): Exposes RabbitMQ to the Kubernetes cluster.
- **Ingress** (`ingress.yaml`): Allows external access to RabbitMQ management interface.
- **ConfigMap** (`rabbitmq-configmap.yaml`): Configures RabbitMQ settings.
- **Secret** (`rabbitmq-secret.yaml`): Stores sensitive RabbitMQ configuration.

### API Service (`server.py`)

This service acts as the main API interface, handling requests from users to:
- **Login**: Calls the Auth Service to validate user credentials.
- **Upload Videos**: Receives videos, uploads them to GridFS, and triggers the conversion process.
- **Download MP3s**: Allows users to download converted MP3 files.

### Technologies Used
- **Python**: Backend development using Flask for API endpoints.
- **JWT**: Used for secure user authentication and authorization.
- **MongoDB**: Stores video and MP3 files using GridFS.
- **RabbitMQ**: Manages communication between services for video processing.
- **Kubernetes**: Used for orchestration and deployment of the microservices.
- **Persistent Volumes**: Ensures RabbitMQ has persistent storage.
- **Email**: Used for sending notifications to users via Gmail SMTP.

## Requirements

- **Python 3.x**
- **RabbitMQ**
- **MongoDB**
- **Flask**
- **PyMongo**
- **Pika**
- **GridFS**
- **JWT**
- **SMTP (Gmail)**

## Setup

### 1. Clone the repository

```bash
git clone <repository_url>
cd <project_directory>
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Set the following environment variables:
- `MYSQL_HOST`: The host of the MySQL database.
- `MYSQL_USER`: The MySQL user for authentication.
- `MYSQL_PASSWORD`: The MySQL user's password.
- `MYSQL_DB`: The name of the database.
- `MYSQL_PORT`: The port for MySQL.
- `JWT_SECRET`: The secret key used for signing JWT tokens.
- `VIDEO_QUEUE`: The RabbitMQ queue name for video files.
- `MP3_QUEUE`: The RabbitMQ queue name for MP3 conversion.
- `GMAIL_ADDRESS`: The Gmail address used to send email notifications.
- `GMAIL_PASSWORD`: The Gmail password for sending email notifications.

### 4. Run the Services

#### Authentication Service
```bash
docker-compose up auth
```

#### Conversion Service
```bash
docker-compose up converter
```

#### Notification Service
```bash
docker-compose up notification
```

#### API Service
```bash
python server.py
```

#### RabbitMQ (StatefulSet with Persistent Storage)
```bash
kubectl apply -f statefulset.yaml
kubectl apply -f pvc.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
```

## Endpoints

### 1. **Login** (`POST /login`)

Logs in a user with their credentials and returns a JWT for authentication.

### 2. **Upload Video** (`POST /upload`)

Uploads a video file for conversion. Only admins can upload videos.

### 3. **Download MP3** (`GET /download`)

Downloads a converted MP3 file. You must provide the `fid` (file ID) of the desired MP3.
