#Base Image
FROM python:3.11-slim

#set the working directory 
WORKDIR /app

#copy the requirement and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#copy the rest of the application code
COPY . .

#expose the port
EXPOSE 8000

#run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]