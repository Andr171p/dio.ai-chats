from dataclasses import fields

from ddf.domain.models import Entity
from ddf.infra.database.mongo import MongoBaseModel

from src.domain.runs import McpToolCall, ModelCall, Run

from .models import McpToolCallModel, ModelCallModel, RunModel


def build_entity[EntityT: Entity](entity_type: type[EntityT], source: object) -> EntityT:
    """Собирает доменную сущность из объекта с одноимёнными атрибутами."""

    return entity_type(
        **{field.name: getattr(source, field.name) for field in fields(entity_type) if field.init}
    )


class DataclassMapper[EntityT: Entity, ModelT: MongoBaseModel]:
    """Mapper для документов, поля которых совпадают с полями доменной сущности."""

    def __init__(self, entity_type: type[EntityT], model_type: type[ModelT]) -> None:
        self._entity_type = entity_type
        self._model_type = model_type

    def to_model(self, entity: EntityT, /, **_: object) -> ModelT:
        return self._model_type.model_validate(entity, from_attributes=True)

    def from_model(self, model: ModelT, /, **_: object) -> EntityT:
        return build_entity(self._entity_type, model)


_STEP_ENTITIES: dict[type[MongoBaseModel], type[Entity]] = {
    ModelCallModel: ModelCall,
    McpToolCallModel: McpToolCall,
}


class RunMapper(DataclassMapper[Run, RunModel]):
    def __init__(self) -> None:
        super().__init__(Run, RunModel)

    def from_model(self, model: RunModel, /, **_: object) -> Run:
        run = build_entity(Run, model)
        run.steps = [build_entity(_STEP_ENTITIES[type(step)], step) for step in model.steps]
        return run
