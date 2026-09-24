from typing import Annotated

from dataclasses import dataclass
from enum import StrEnum

from typing_extensions import Doc


class ThreadOrigin(StrEnum):
    DEFAULT = "default"
    REGENERATE = "regenerate"
    EDIT = "edit"
    FORK = "fork"


class TitleSource(StrEnum):
    AUTO = "auto"
    MANUAL = "manual"


@dataclass(frozen=True, slots=True)
class ConversationTitle:
    """Заголовок чата, по дефолту будет создаваться автоматически."""

    label: Annotated[str, Doc("Человекочитаемый заголовок")]
    source: TitleSource
