# Setup and Usage Guide

This guide provides step-by-step instructions for setting up and running the Service locally. The Service is managed using Docker Compose and includes PostgreSQL and, DjangoApp. Additionally, it covers how to create a virtual environment, install `pre-commit` for code quality checks, and run tests.

## Prerequisites

Before getting started, ensure you have the following prerequisites installed on your system:

- [Docker](https://www.docker.com/get-started) for containerization.
- [Docker Compose](https://docs.docker.com/compose/install/) for orchestrating the containers.
- [Python](https://www.python.org/downloads/) for managing Python packages and running tests.
- [pip](https://pip.pypa.io/en/stable/installing/) for Python package management.

## Setting Up a Virtual Environment

1. Create a virtual environment to isolate your Python packages. Open a terminal and run the following commands:

   ```bash
   # Create a new virtual environment (replace 'env_name' with your preferred name)
   python -m venv env_name

   # Activate the virtual environment
   source env_name/bin/activate  # On Windows, use 'env_name\Scripts\activate'
   ```

   Your terminal prompt should now indicate that the virtual environment is active.

## Running the Service Locally

The Broker Service relies on Docker Compose to manage containers and these additional steps for running it locally:

1. In the root directory of the project, create a `.env` file (if not provided) and set any necessary environment variables.

2. Make sure your virtual environment is active.

3. Once the containers are up and running, open a new terminal in the project directory. To apply database migrations, run:

   ```bash
   python manage.py migrate
   ```

   This command will create the necessary database tables and schema.

4. After the migrations are applied, you can start the development server:

   ```bash
   python manage.py runserver
   ```

   This command will start the Django development server. You can now access the Broker Service through `http://localhost:8000` or the URL specified in your Django project.

By following these steps, you will have the Broker Service up and running locally, with the database migrated and the development server running.

## Running Docker Compose

To start the Docker Compose environment, follow these steps:

1. Make sure Docker and Docker Compose are installed and running.

2. Navigate to the project directory containing your Docker Compose configuration file.

3. Open a terminal or command prompt.

4. Run the following command to start the containers:

   ```bash
   docker-compose up
   ```

   This will initiate the PostgreSQL, DjangoApp, and Redis containers as specified in the Docker Compose configuration.

## Installing Pre-commit

To maintain code quality and consistency, it's recommended to install and configure `pre-commit` for your project:

1. Make sure your virtual environment is active.

2. Run the following command to install `pre-commit` using pip:

   ```bash
   pip install pre-commit
   ```

## Running Tests

To run tests for the Broker Service, follow these steps:

1. Ensure your virtual environment is active.

2. Navigate to the project's root directory where your tests are located.

3. Run the following command to execute the tests:

   ```bash
   python manage.py test
   ```

   This will run the tests specified in your Django project.