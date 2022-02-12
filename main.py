from fastapi import FastAPI
from pymongo import MongoClient
import datetime

client = MongoClient('mongodb://localhost', 27017)
database = client['exceed_project']
collection = database['toilet']
app = FastAPI()


@app.get('/')
def hello_world():
    return 'Hello, world'
