# TODO: Testing of APIs

## Project Setup Guide

Follow the steps below to set up and run the project locally.

## 1. Clone / Pull the Repository

First, pull the latest code from the repository:

```bash
git pull
```

Or if you are cloning for the first time:

```bash
git clone <repository-url>
cd <project-folder>
```

---

## 2. Create a Python Virtual Environment

Create a virtual environment using `venv`:

```bash
python -m venv venv
```

Activate the environment:

**On macOS / Linux**

```bash
source venv/bin/activate
```

**On Windows**

```bash
venv\Scripts\activate
```

---

## 3. Install Backend Dependencies

Navigate to the backend directory and install the required packages:

```bash
cd backend
pip install -r requirements.txt
```

---

## 4. Setup Environment Variables

Create a `.env` file using the `.env.example` template:

```bash
cp .env.example .env
```

Open the `.env` file and update the values according to your environment and configuration.

---

## 5. Create Database Tables

Before running the application, initialize the database tables by running:

```bash
python app/config/create_tables.py
```

---

## 6. Run the Application

Start the FastAPI server using Uvicorn:

```bash
uvicorn main.app:app --reload
```

---

## 7. Access the Application

Once the server starts, the application will be available at:

```
http://localhost:8000
```

---

## Notes

* Ensure Python is installed on your system (Python 3.9+ recommended).
* Make sure the virtual environment is activated before installing dependencies or running the server.
