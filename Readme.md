# GitHub Stats API

A FastAPI application that fetches, aggregates, and caches comprehensive GitHub user statistics, including total stars, commits, contributions, and contribution streaks. It also provides the functionality to generate dynamic SVG images of these statistics, perfect for embedding in GitHub profiles or project READMEs.

## ✨ Features

* **Comprehensive Stats**: Fetches detailed user statistics from the GitHub API (REST and GraphQL).
* **SVG Generation**: Dynamically generates customizable SVG images of GitHub stats for visual representation.
* **Caching**: Implements a robust caching mechanism for both JSON data and generated SVGs to minimize GitHub API calls and improve response times.
* **Dockerized**: Easily deployable using Docker for consistent environments.
* **Modular Design**: Structured with services and clear responsibilities for maintainability.
* **CORS Enabled**: Configured for Cross-Origin Resource Sharing, allowing access from various front-end applications.

## 🚀 Technologies Used

* **FastAPI**: A modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints.
* **Uvicorn**: An ASGI server, used to run the FastAPI application.
* **Pydantic**: For data validation and settings management using Python type hints.
* **Jinja2**: A modern and designer-friendly templating language for Python, used for SVG generation.
* **Requests**: An elegant and simple HTTP library for Python.
* **python-dotenv**: Loads environment variables from a `.env` file.
* **Docker**: For containerization and easy deployment.

## 🖥️ Preview
![svg](https://github-stats-generator.onrender.com/stats/shushantrishav/svg?v2)

## 🛠️ Setup and Installation

Follow these steps to get your project up and running locally.

### Prerequisites

* Python 3.10+
* `pip` (Python package installer)
* Docker (Optional, but recommended for deployment)
* A GitHub Personal Access Token (PAT). You can generate one [here](https://github.com/settings/tokens). It needs `public_repo` (if fetching private repo data) and `read:user` permissions.

### Steps
**fork this repo
1.  **Clone the repository:**
    ```bash

    git clone https://github.com/<your-username>/github-stats-api.git

    cd github-stats-api
    ```
    (Remember to replace `your-username` and `github-stats-api` if you rename your repository.)

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create a `.env` file:**
    In the root directory of your project, create a file named `.env` and add your GitHub Personal Access Token:
    ```dotenv
    GITHUB_TOKEN="YOUR_ACTUAL_GITHUB_TOKEN_HERE"
    ```
    **Replace `YOUR_ACTUAL_GITHUB_TOKEN_HERE` with your token.**

5.  **Run the application locally:**
    ```bash
    uvicorn app:app --host 0.0.0.0 --port 8000 --reload
    ```
    The `--reload` flag is for development purposes; it will automatically restart the server on code changes. Remove it for production.

    Your API will be accessible at `http://localhost:8000`.

## 🐳 Docker Setup

For a consistent and isolated environment, you can use Docker.

1.  **Build the Docker image:**
    Navigate to the root of your project where the `Dockerfile` is located.
    ```bash
    docker build -t github-stats-api .
    ```

2.  **Run the Docker container:**
    ```bash
    docker run -d -p 8000:8000 --name my-github-stats-app -e GITHUB_TOKEN="YOUR_ACTUAL_GITHUB_TOKEN_HERE" github-stats-api
    ```
    **Again, replace `YOUR_ACTUAL_GITHUB_TOKEN_HERE` with your GitHub PAT.**

    The application will be running in a Docker container, accessible at `http://localhost:8000`.

## 💡 API Endpoints

The API provides the following endpoints:

* **Root Endpoint**:
    * `GET /`
    * Provides a basic HTML welcome page with API instructions.

* **Get JSON Stats**:
    * `GET /stats/{username}`
    * Fetches comprehensive GitHub profile statistics for a given `{username}` in JSON format.
    * **Example**: `http://localhost:8000/stats/shushantrishav`

* **Get SVG Stats Image**:
    * `GET /stats/{username}/svg`
    * Generates a dynamic SVG image displaying the GitHub statistics for a given `{username}`.
    * **Example**: `http://localhost:8000/stats/shushantrishav/svg`

## 📊 SVG Usage (Embedding in READMEs)

You can easily embed the generated SVG into your GitHub profile README, repository READMEs, or any webpage using Markdown's image syntax or HTML `<img>` tag:

```markdown
![GitHub Stats](http://localhost:8000/stats/your-github-username/svg)
```
