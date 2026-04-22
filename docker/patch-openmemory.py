from pathlib import Path

database = Path("/app/api/app/database.py")
database.write_text(
    database.read_text().replace(
        """# SQLAlchemy engine & session\nengine = create_engine(\n    DATABASE_URL,\n    connect_args={\"check_same_thread\": False}  # Needed for SQLite\n)\n""",
        """engine_kwargs = {}\nif DATABASE_URL.startswith(\"sqlite\"):\n    engine_kwargs[\"connect_args\"] = {\"check_same_thread\": False}\n\n# SQLAlchemy engine & session\nengine = create_engine(\n    DATABASE_URL,\n    **engine_kwargs,\n)\n""",
    )
)

schemas = Path("/app/api/app/schemas.py")
schemas.write_text(
    schemas.read_text()
    .replace(
        "from pydantic import BaseModel, ConfigDict, Field, validator",
        "from pydantic import BaseModel, ConfigDict, Field, field_validator",
    )
    .replace(
        "    @validator('created_at', pre=True)\n    def convert_to_epoch(cls, v):",
        "    @field_validator('created_at', mode='before')\n    @classmethod\n    def convert_to_epoch(cls, v):",
    )
)
