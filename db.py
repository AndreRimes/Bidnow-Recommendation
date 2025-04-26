import os
from databases import Database

DATABASE_URL = os.getenv("DB_URL")

database = Database(DATABASE_URL)
