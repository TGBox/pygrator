from ..font import CTkFont as CTkFont
from .scaling_tracker import ScalingTracker as ScalingTracker
from typing_extensions import Literal

class CTkScalingBaseClass:
    def __init__(self, scaling_type: Literal['widget', 'window'] = 'widget') -> None: ...
    def destroy(self) -> None: ...
