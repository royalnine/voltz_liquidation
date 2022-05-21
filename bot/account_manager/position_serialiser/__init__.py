import dataclasses
import dataclasses_json
from typing import List


@dataclasses_json.dataclass_json(undefined=dataclasses_json.Undefined.RAISE)
@dataclasses.dataclass()
class Position:
    id: str
    tickLower: int
    tickUpper: int
    margin: int
    owner: str
    liquidations: List[str]
    marginEngine: str
