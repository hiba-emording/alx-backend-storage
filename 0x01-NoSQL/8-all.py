#!/usr/bin/env python3
"""function that lists all documents in a collection"""


def list_all(mongo_collection):
    """Lists all documents in a collection"""
    return [doc for doc in mongo_collection.find()]
