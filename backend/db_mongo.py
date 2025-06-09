"-------------------------------------------------------------"

from pymongo import MongoClient

client = MongoClient("your-mongodb-atlas-uri")
db = client["netmind"]
collection = db["latency"]

collection.insert_one(
    {"target": "8.8.8.8", "latency": 56.3, "timestamp": "2025-05-25T11:30:00Z"}
)

"--------------------------------------------------------------"
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://petermekhail01:<password>@netmindcluster.ecihb0u.mongodb.net/?retryWrites=true&w=majority&appName=netMindCluster"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi("1"))

# Send a ping to confirm a successful connection
try:
    client.admin.command("ping")
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
