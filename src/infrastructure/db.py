from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from dotenv import load_dotenv
import os
from src.logging_config import logger


logger = logger.getChild(__name__)


load_dotenv()
DATABASE_URL = f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"

if not DATABASE_URL:
    logger.critical("DATABASE_URL not found in environment! Exiting.")
    raise ValueError("DATABASE_URL is Not Found!")

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

logger.info("Database engine and session factory successfully created.")
