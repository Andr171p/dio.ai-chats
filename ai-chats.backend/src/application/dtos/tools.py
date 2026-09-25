from pydantic import BaseModel, ConfigDict, Field, JsonValue


class ModelTool(BaseModel):
    """Tool, доступный модели во время inference (вспомогательный DTO)."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(description="Название инструмента")
    description: str | None = Field(default=None, description="Описание для модели")
    input_schema: dict[str, JsonValue] = Field(description="Схема передаваемых аргументов")
