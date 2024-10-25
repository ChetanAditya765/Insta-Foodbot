from pymongo import MongoClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import MONGODB_URI
def get_database():
    client = MongoClient(MONGODB_URI)
    return client.foodOrdersDB

def init_collections():
    db = get_database()
    
    # Create collections if they don't exist
    if 'menu' not in db.list_collection_names():
        db.create_collection('menu')
    if 'orders' not in db.list_collection_names():
        db.create_collection('orders')
    if 'users' not in db.list_collection_names():
        db.create_collection('users')
    if 'transactions' not in db.list_collection_names():
        db.create_collection('transactions')