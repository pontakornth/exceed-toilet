import http

import pymongo
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
import datetime

client = MongoClient('mongodb://localhost', 27017)
database = client['exceed_project']
collection = database['Toilet']
app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RoomStatusChange(BaseModel):
    room1: int
    room2: int
    room3: int


@app.post('/change/')
def change_status(change: RoomStatusChange):
    """
    Change status of toilets.
    """
    # It's safe to assume there three toilets.
    rooms = collection.find({'room_number': {'$in': [1, 2, 3]}}).sort('room_number', pymongo.ASCENDING)
    rooms_changes = [change.room1, change.room2, change.room3]
    current_time = datetime.datetime.utcnow()
    for room, change in zip(rooms, map(lambda x: True if x else False, rooms_changes)):
        # If the status changed, then:
        is_occupied = room['is_occupied']
        if is_occupied != change:
            # If occupied then vacant
            if is_occupied:
                time_update = {
                    'is_occupied': False,
                    'end_time': current_time
                }
                total_time = round((current_time - room['start_time']).total_seconds())
                collection.update_one({'room_number': room['room_number']}, {'$set': time_update, '$push': {
                    'usage': total_time
                }})
            else:
                # If vacant then occupied
                time_update = {
                    'is_occupied': True,
                    'start_time': current_time
                }
                collection.update_one({'room_number': room['room_number']}, {'$set': time_update})
    return {
        'status': 'success'
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


@app.get('/status/')
def get_status():
    """
    Get status of all rooms.

    Information includes:

        - Status (Occupied, Vacant)
        - Start Time of each room
        - Average time
    """
    all_rooms = collection.find({'room_number': {'$in': [1, 2, 3]}}).sort('room_number', pymongo.ASCENDING)
    summation = 0
    average_count = 0
    room_info = []
    current_time = datetime.datetime.utcnow()
    for room in all_rooms:
        # If the room is used once, it calculates the average
        # Otherwise, it will return None.
        room_info.append({
            'roomNumber': room['room_number'],
            'averageTime': sum(room['usage']) / len(room['usage']) if room['usage'] else None,
            'status': room['is_occupied'],
            'startTime': room['start_time'],
            'lastTime': room['end_time'],
            # Diff time is time from current time to start
            'diffTime': round((current_time - room['start_time']).total_seconds())
        })
        if room['usage']:
            summation += sum(room['usage'])
            average_count += len(room['usage'])
    average_time = summation / average_count if average_count > 0 else None

    return {
        'rooms': room_info,
        'averageTime': average_time,
        'currentTime': current_time,
    }


@app.get('/')
def hello_world():
    return 'Hello, world'
