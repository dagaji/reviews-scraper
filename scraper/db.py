import pymongo
import pdb
import datetime
from copy import deepcopy
import json
import locale; locale.setlocale(locale.LC_ALL, 'es_ES.utf8')
import calendar; month_name = [month for month in calendar.month_name]


def get_db(settings, drop):
    connection = pymongo.MongoClient(settings.get('MONGODB_SERVER'), settings.get('MONGODB_PORT'))
    db_name = settings.get('MONGODB_DB')
    if drop:
        connection.drop_database(db_name)
    return connection[db_name]


def get_collection(db, collection_name):
    if collection_name in db.list_collection_names():
        return db[collection_name]

    collection = db[collection_name]
    collection.create_index([("reviewer", pymongo.DESCENDING),
                             ("game_name", pymongo.DESCENDING),
                             ("release_date", pymongo.DESCENDING)], unique=True)

    collection.create_index([("release_date", pymongo.DESCENDING)])

    collection.create_index([("score", pymongo.DESCENDING)])

    collection.create_index([("genre", pymongo.DESCENDING),
                             ("release_date", pymongo.DESCENDING),
                             ("score", pymongo.DESCENDING)])

    collection.create_index([("genre", pymongo.DESCENDING),
                             ("score", pymongo.DESCENDING),
                             ("release_date", pymongo.DESCENDING)])


    return collection


def insert_many(collection, items_list):
    try:
        collection.insert_many(items_list)
    except pymongo.errors.DuplicateKeyError:
        return False
    return True

def insert_one(collection, item):
    try:
        collection.insert_one(item)
    except pymongo.errors.DuplicateKeyError:
        return False
    return True