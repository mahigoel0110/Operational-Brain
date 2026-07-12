from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    DEBUG: bool

    MONGO_URI: str
    DATABASE_NAME: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # OpenAI / Embedding configuration
    OPENAI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Qdrant / Vector configuration
    QDRANT_URL: str = ""  # If empty, runs in-memory/local storage mode
    QDRANT_COLLECTION_NAME: str = "documents_v2"

    # Chunking configuration
    CHUNK_SIZE: int = 200
    CHUNK_OVERLAP: int = 40

    # Neo4j configuration
    NEO4J_URI: str = ""
    NEO4J_USERNAME: str = ""
    NEO4J_PASSWORD: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()