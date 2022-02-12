import http

from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
import datetime

client = MongoClient('mongodb://localhost', 27017)
database = client['exceed_project']
collection = database['Toilet']
app = FastAPI()

# Example
toilets = {
    'room-1': {
        'room': 1,
        'isOccupied': False,
        'startTime': None,
        'endTime': None
    },
    'room-2': {
        'isOccupied': False,
        'startTime': None,
        'endTime': None
    },
    'room-3': {
        'isOccupied': False,
        'startTime': None,
        'endTime': None,
    }

}


@app.post('/occupy/{room_number}/')
def occupy(room_number: int):
    """
    Occupy the room
    :param room_number:  Room number to occupy
    :return: Status of success or failure
    """
    # We set this up.
    room = collection.find_one({'room_number': room_number})
    if room['is_occupied']:
        raise HTTPException(http.HTTPStatus.CONFLICT, {
            'status': 'conflict',
            'message': 'the room is occupied'
        })
    room_update = {
        # Note: MongoDB always use UTC time.
        "start_time": datetime.datetime.utcnow(),
        "is_occupied": True
    }
    collection.update_one({'room_number': room_number}, {'$set': room_update})
    return {
        'status': 'success',
    }


@app.post('/release/{room_number}')
def release(room_number: int):
    """
    Release the room so other people can use it.
    :param room_number: The room number to release
    :return: Status of success
    """
    room = collection.find_one({'room_number': room_number})
    if not room['is_occupied']:
        raise HTTPException(http.HTTPStatus.CONFLICT, {
            'status': 'conflict',
            'message': 'the room is already free'
        })
    current_time = datetime.datetime.utcnow()
    time_update = {
        'end_time': current_time,
        'is_occupied': False
    }
    total_time = round((current_time - room['start_time']).total_seconds())
    collection.update_one({'room_number': room_number}, {'$set': time_update, '$push': {'usage': total_time}})
    return {
        'status': 'success'
    }


@app.get('/')
def hello_world():
    return 'Hello, world'
