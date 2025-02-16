from pymongo import MongoClient
from config.mongodb_config import MONGO_HOST, MONGO_PORT, MONGO_DB_NAME

# Connect to the MongoDB database
client = MongoClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}/")
db = client[MONGO_DB_NAME]


# Ensure indexes
def ensure_index(collection, index_field):
    indexes = collection.index_information()
    index_name = f"{index_field}_1"
    if index_name not in indexes:
        collection.create_index(index_field)


ensure_index(db.publications, "keywords.name")
ensure_index(db.publications, "year")


def get_keyword_options():
    faculty_collection = db['faculty']
    keywords = faculty_collection.distinct('keywords.name')
    return [{'label': k, 'value': k} for k in keywords]


def get_keyword_trends_data(keywords):
    publications_collection = db['publications']
    trends_data = {}

    for keyword in keywords:
        keyword_counts = publications_collection.aggregate([
            {'$match': {'keywords.name': keyword}},
            {'$unwind': '$keywords'},
            {'$match': {'keywords.name': keyword}},
            {'$group': {'_id': '$year', 'count': {'$sum': 1}}},
            {'$sort': {'_id': 1}}
        ])
        years, counts = zip(*[(item['_id'], item['count']) for item in keyword_counts])
        trends_data[keyword] = {'years': years, 'counts': counts}

    return trends_data
