# config.py
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# MongoDB connection URI
uri = "mongodb+srv://haywardmrob:anJwDvc9fxBpZRZg@tagbotai.57zxm.mongodb.net/?retryWrites=true&w=majority&appName=TagBotAI"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["TagBotAI"]  # database name

# Check the connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
