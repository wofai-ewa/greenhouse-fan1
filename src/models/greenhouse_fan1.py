import asyncio
from typing import (Any, ClassVar, Dict, Final, List, Mapping, Optional,
                    Sequence, Tuple)

try:
    import RPi.GPIO as GPIO
except ImportError:
    # Mock GPIO for non-Pi environments (e.g. local build/test)
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
from typing_extensions import Self
from viam.components.component_base import ComponentBase
from viam.components.sensor import Sensor
from viam.components.switch import Switch
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import Geometry, ResourceName
from viam.resource.base import ResourceBase
from viam.resource.easy_resource import EasyResource
from viam.resource.types import Model, ModelFamily
from viam.utils import ValueTypes

# GPIO pin for the fan relay
FAN_PIN = 27

# Temperature thresholds in Celsius
TEMP_ON_C  = 23.9  # ~75°F — turn fan ON
TEMP_OFF_C = 21.1  # ~70°F — turn fan OFF

# How often to check temperature (seconds)
POLL_INTERVAL = 10


class GreenhouseFan1(Switch, EasyResource):
    MODEL: ClassVar[Model] = Model(
        ModelFamily("viam", "greenhouse-fan1"), "greenhouse-fan1"
    )

    _position: int = 0          # 0 = off, 1 = on
    _sensor: Optional[Sensor] = None
    _monitor_task: Optional[asyncio.Task] = None

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        inst = super().new(config, dependencies)

        # Set up GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(FAN_PIN, GPIO.OUT, initial=GPIO.LOW)

        # Grab the temp sensor dependency if configured
        sensor_name = config.attributes.fields.get("sensor_name")
        if sensor_name:
            for rn, dep in dependencies.items():
                if rn.name == sensor_name.string_value and isinstance(dep, Sensor):
                    inst._sensor = dep
                    break

        # Start background temperature monitor
        inst._monitor_task = asyncio.create_task(inst._temp_monitor())

        return inst

    @classmethod
    def validate_config(
        cls, config: ComponentConfig
    ) -> Tuple[Sequence[str], Sequence[str]]:
        # sensor_name is an optional dependency
        sensor_name = config.attributes.fields.get("sensor_name")
        if sensor_name:
            return [], [sensor_name.string_value]
        return [], []

    async def _temp_monitor(self):
        """Background loop: read temp sensor and auto-toggle fan."""
        while True:
            try:
                if self._sensor:
                    readings = await self._sensor.get_readings()
                    temp_c = readings.get("temperature")
                    if temp_c is not None:
                        if temp_c >= TEMP_ON_C and self._position == 0:
                            self.logger.info(f"Temp {temp_c:.1f}°C >= threshold, turning fan ON")
                            await self.set_position(1)
                        elif temp_c <= TEMP_OFF_C and self._position == 1:
                            self.logger.info(f"Temp {temp_c:.1f}°C <= threshold, turning fan OFF")
                            await self.set_position(0)
            except Exception as e:
                self.logger.warning(f"Temp monitor error: {e}")
            await asyncio.sleep(POLL_INTERVAL)

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
        GPIO.output(FAN_PIN, GPIO.HIGH if position == 1 else GPIO.LOW)
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
        if self._monitor_task:
            self._monitor_task.cancel()
        GPIO.cleanup()