## FastAPI Application

This FastAPI application provides endpoints for user authentication, adding post, retrieving posts, and deleting posts. It uses Pydantic for data validation and SQLAlchemy for interacting with the database. Additionally, it implements response caching for improved performance.

Installation
Clone the repository:

      git clone https://github.com/your-repo.git
Navigate to the project directory:

      pip install -r requirements.txt
Usage
Start the FastAPI server:

      uvicorn main:app --reload
Access the Swagger documentation at http://127.0.0.1:8000/docs to interact with the endpoints.
