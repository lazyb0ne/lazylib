from pymongo import MongoClient


class MongoDB:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            client = MongoClient('mongodb://zhuoheng:Qweqwe123_@101.43.113.210:27017')
            database = client['illegal_web']
            cls._instance = database
            # cls._instance = database['web_src']
            # cls._instance = database['url_list']
        return cls._instance


collection = MongoDB()


def db_images():
    return collection['url_images']


def db_images_clear():
    collection['url_images'].delete_many({})


def db_urls():
    return collection['urls']


def db_urls96():
    return collection['urls_0705']


def db_urls_dbname(db_name):
    return collection[f'urls_{db_name}']


def db_full_dbname(db_name):
    return collection[f'{db_name}']

