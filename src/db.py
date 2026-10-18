import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/guitar_ml")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)