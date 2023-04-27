from typing import List, Dict

import jsonschema
from jsonschema import validate
from pydantic.dataclasses import dataclass

from models.types import NestedDict


@dataclass
class DBCredentialsSchema:
    user: str
    password: str
    host: str
    port: int
    database: str


@dataclass
class ConnectionSchema:
    engine: str
    credentials: DBCredentialsSchema


@dataclass
class AppSchema:
    models: List[str]
    default_connection: str


@dataclass
class DBConfigSchema:
    connections: Dict[str, ConnectionSchema]
    apps: Dict[str, AppSchema]
    default_connection: str

    @staticmethod
    def validate_schema(obj: NestedDict):
        schema = DBConfigSchema.__pydantic_model__.schema()
        try:
            validate(obj, schema)
        except jsonschema.exceptions.ValidationError as e:
            raise e


DB_CONFIG_SCHEMA = DBConfigSchema
