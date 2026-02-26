import asyncio
from typing import (Any, ClassVar, Dict, Mapping, Optional,
                    Sequence, Tuple)

from typing_extensions import Self
from viam.components.switch import Switch
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import Geometry, ResourceName
from viam.resource.base import ResourceBase
from viam.resource.easy_resource import EasyResource
from viam.resource.types import Model, ModelFamily
from viam.utils import ValueTypes

try:
    import RPi.GPIO as GPIO
except ImportError:
    class GPIO:
        BCM = OUT = HIGH = LOW = 0
        @staticmethod
        def setmode(_): pass
        @staticmethod
        def setup(*args, **kwargs): pass
        @staticmethod
        def output(*args): pass
        @staticmethod
        def cleanup(): pass

DEFAULT_FAN_PIN = 27


class GreenhouseFan1(Switch, EasyResource):
    MODEL: ClassVar[Model] = Model(
        ModelFamily("viam", "greenhouse-fan1"), "greenhouse-fan1"
    )

    _position: int = 0
    _fan_pin: int = DEFAULT_FAN_PIN

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        inst = super().new(config, dependencies)

        fields = config.attributes.fields
        if "fan_pin" in fields:
            inst._fan_pin = int(fields["fan_pin"].number_value)

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(inst._fan_pin, GPIO.OUT, initial=GPIO.LOW)

        return inst

    @classmethod
    def validate_config(
        cls, config: ComponentConfig
    ) -> Tuple[Sequence[str], Sequence[str]]:
        return [], []

    async def get_number_of_positions(
        self,
        *,
        extra: Optional[Mapping[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Tuple[int, Sequence[str]]:
        return 2, ["off", "on"]

    async def get_position(
        self,
        *,
        extra: Optional[Mapping[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs
    ) -> int:
        return self._position

    async def set_position(
        self,
        position: int,
        *,
        extra: Optional[Mapping[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs
    ) -> None:
        if position not in (0, 1):
            raise ValueError(f"Invalid position {position}: must be 0 (off) or 1 (on)")
        self._position = position
        GPIO.output(self._fan_pin, GPIO.HIGH if position == 1 else GPIO.LOW)
        self.logger.info(f"Fan set to {'ON' if position == 1 else 'OFF'}")

    async def do_command(
        self,
        command: Mapping[str, ValueTypes],
        *,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Mapping[str, ValueTypes]:
        if "set_position" in command:
            await self.set_position(int(command["set_position"]))
            return {"position": self._position}
        raise NotImplementedError(f"Unknown command: {command}")

    async def get_geometries(
        self, *, extra: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None
    ) -> Sequence[Geometry]:
        return []

    def __del__(self):
        GPIO.cleanup()