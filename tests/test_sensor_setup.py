"""Tests for adding sensor entities without waiting for optimizer data."""

from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.huawei_solar import sensor
from custom_components.huawei_solar.const import DATA_DEVICE_DATAS
from custom_components.huawei_solar.types import HuaweiSolarInverterData


async def test_optimizer_entities_are_added_without_update_before_add(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    inverter_entity = MagicMock()
    optimizer_entity = sensor.HuaweiSolarOptimizerSensorEntity.__new__(
        sensor.HuaweiSolarOptimizerSensorEntity
    )

    async def create_sun2000_entities(*_args: object, **_kwargs: object) -> list:
        return [inverter_entity, optimizer_entity]

    monkeypatch.setattr(sensor, "create_sun2000_entities", create_sun2000_entities)
    inverter_data = MagicMock(spec=HuaweiSolarInverterData)
    inverter_data.device = MagicMock()
    entry = MagicMock(runtime_data={DATA_DEVICE_DATAS: [inverter_data]})
    add_entities = MagicMock()

    await sensor.async_setup_entry(hass, entry, add_entities)

    calls = [(list(c.args[0]), c.args[1:] == (True,)) for c in add_entities.call_args_list]
    assert calls == [([inverter_entity], True), ([optimizer_entity], False)]
