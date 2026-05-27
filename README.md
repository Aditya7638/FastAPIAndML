# FastAPI Insurance Prediction API

A Machine Learning powered Insurance Premium Prediction system built using:

* FastAPI
* Random Forest Model
* Streamlit Frontend
* Docker
* Pydantic Validation
* Scikit-learn

The project predicts insurance premium categories based on user input such as:

* Age
* Height
* Weight
* Income
* Smoking Habit
* Occupation
* City

---

# Project Architecture

```text
FastAPIAndML/
│
├── model/
│   ├── model.pkl
│   ├── predict.py
│
├── schema/
│   ├── user_input.py
│   ├── prediction_response.py
│
├── app.py
├── frontend.py
├── requirements.txt
├── Dockerfile
├── .gitignore
├── city_tier_dataset.csv
│
└── README.md
```

---

# Features

* FastAPI based REST API
* Random Forest ML model
* Separate Pydantic schemas for request and response
* Dockerized application
* Streamlit frontend integration
* City tier dataset support
* Swagger API documentation
* JSON API responses
* Ready for deployment

---

# Machine Learning Model

The prediction system uses:

* Random Forest Classifier
* Trained using Scikit-learn
* Serialized using Pickle
* Model stored inside:

```text
model/model.pkl
```

---

# Pydantic Validation

Request and response schemas are separated for clean architecture.

### Request Schema

```text
schema/user_input.py
```

### Response Schema

```text
schema/prediction_response.py
```

---

# API Endpoint

## POST /predict

### Sample Request

```json
{
  "age": 28,
  "weight": 72,
  "height": 1.75,
  "income_lpa": 12,
  "smoker": false,
  "city": "Delhi",
  "occupation": "Engineer"
}
```

### Sample Response

```json
{
  "prediction": "Medium",
  "model_version": "1.0.0"
}
```

---

# Run Locally

## Clone Repository

```bash
git clone https://github.com/Aditya7638/FastAPIAndML.git
cd FastAPIAndML
```

---

# Create Virtual Environment

## Windows

```bash
python -m venv venv
venv\Scripts\activate
```

## Linux / Mac

```bash
python3 -m venv venv
source venv/bin/activate
```

---

# Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Run FastAPI Server

```bash
uvicorn app:app --reload
```

API will run on:

```text
http://127.0.0.1:8000
```

---

# Swagger Documentation

FastAPI automatically generates interactive API docs.

## Swagger UI

```text
http://127.0.0.1:8000/docs
```

## ReDoc

```text
http://127.0.0.1:8000/redoc
```

---

# Streamlit Frontend Demo

Create a file:

```text
frontend.py
```

Add the following code:

```python
import streamlit as st
import requests

st.title("Insurance Premium Predictor")

age = st.number_input("Age", min_value=1, max_value=100)
weight = st.number_input("Weight")
height = st.number_input("Height")
income = st.number_input("Income (LPA)")
smoker = st.selectbox("Smoker", [True, False])
city = st.text_input("City")
occupation = st.text_input("Occupation")

if st.button("Predict"):

    payload = {
        "age": age,
        "weight": weight,
        "height": height,
        "income_lpa": income,
        "smoker": smoker,
        "city": city,
        "occupation": occupation
    }

    response = requests.post(
        "http://127.0.0.1:8000/predict",
        json=payload
    )

    if response.status_code == 200:
        st.success(response.json())
    else:
        st.error("Prediction Failed")
```

---

# Run Streamlit Frontend

```bash
streamlit run frontend.py
```

Frontend URL:

```text
http://localhost:8501
```

---

# Docker Support

The project is fully Dockerized.

## Build Docker Image

```bash
docker build -t insurance-api .
```

## Run Docker Container

```bash
docker run -p 8000:8000 insurance-api
```

---

# Docker Hub

Docker image has been pushed to Docker Hub.

## Pull Docker Image

```bash
docker pull adityabhuria29/table
```

## Run Docker Image

```bash
docker run -p 8000:8000 adityabhuria29/table
```

---

# Example Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

# Tech Stack

* Python
* FastAPI
* Streamlit
* Scikit-learn
* Pandas
* Docker
* Pydantic
* Uvicorn

---

# Future Improvements

* Add JWT Authentication
* Add Database Support
* Deploy on AWS / Render
* Add CI/CD Pipeline
* Add Model Monitoring
* Add Logging and Analytics
* Improve UI Design

---

# Author

Aditya Bhuria

GitHub:

[https://github.com/Aditya7638](https://github.com/Aditya7638)

---

# License

This project is open-source and available under the MIT License.
