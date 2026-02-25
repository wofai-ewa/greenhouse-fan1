import asyncio
from viam.module.module import Module
from models.greenhouse_fan1 import GreenhouseFan1


if __name__ == '__main__':
    asyncio.run(Module.run_from_registry())
