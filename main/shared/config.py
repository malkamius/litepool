import mysql.connector

class Config:
    SESSION_SECRET_KEY = 'feda5b49-1f4c-357f-a94f-e5afafdad43e'
    DEBUG = True
    INFO = True
    DB_HOST = 'localhost'
    DB_PORT = 3306
    DB_USER = 'chatsphere'
    DB_PASSWORD = 'ChatSphere!'
    DB_NAME = 'chat_sphere_data'
        
    def get_db_connection(self):
        return mysql.connector.connect(
            host=self.DB_HOST,
            port=self.DB_PORT,
            user=self.DB_USER,
            password=self.DB_PASSWORD,
            database=self.DB_NAME
        )

class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True
    
class TestingConfig(Config):
    TESTING = True
    