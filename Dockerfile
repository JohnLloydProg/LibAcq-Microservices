FROM python:3.12-slim

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy files directly into WORKDIR
COPY . .

# Run uvicorn finding main.py in the current folder
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]