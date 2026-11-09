"""Tests for loading optimizers without blocking the config entry setup."""

from unittest.mock import AsyncMock, MagicMock

from homeassistant.core import HomeAssistant
from huawei_solar.device import SUN2000Device
from huawei_solar.files import OptimizerOnlineStatus, OptimizerSystemInformation
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.huawei_solar import _setup_inverter_device_data
from custom_components.huawei_solar.const import DOMAIN
from custom_components.huawei_solar.optimizers import (
    async_load_optimizers,
    async_refresh_optimizers,
    async_save_optimizers,
)

SERIAL = "BT2321296707"


def _system_information(
    software_version: str = "V100R002C10SPC019",
) -> dict[int, OptimizerSystemInformation]:
    return {
        address: OptimizerSystemInformation(
            optimizer_address=address,
            online_status=OptimizerOnlineStatus.ONLINE,
            string_number=1,
            position_in_current_string=address,
            sn=f"JV22B94120{address:02d}",
            software_version=software_version,
            alias="",
            model="SUN2000-450W-P2",
        )
        for address in (1, 2)
    }


def _device() -> MagicMock:
    device = MagicMock(spec=SUN2000Device)
    device.serial_number = SERIAL
    device.model_name = "SUN2000-10KTL-M1"
    device.software_version = "V100R001C00SPC178"
    device.power_meter_type = None
    device.battery_type = device.battery_1_type = device.battery_2_type = None
    device.has_optimizers = True
    device.primary_device = None
    device.get_optimizer_system_information_data = AsyncMock(
        return_value=_system_information()
    )
    device.get_latest_optimizer_history_data = AsyncMock(return_value={})
    return device


def _entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    return entry


async def test_setup_uses_cached_optimizers_without_reading_files(
    hass: HomeAssistant,
) -> None:
    await async_save_optimizers(hass, SERIAL, _system_information())
    device = _device()

    data = await _setup_inverter_device_data(hass, _entry(hass), device)

    device.get_optimizer_system_information_data.assert_not_awaited()
    device.get_latest_optimizer_history_data.assert_not_awaited()
    assert data.optimizer_device_infos is not None
    assert sorted(data.optimizer_device_infos) == [1, 2]
    assert data.optimizer_update_coordinator is not None


async def test_first_setup_reads_system_information_and_caches_it(
    hass: HomeAssistant,
) -> None:
    device = _device()

    data = await _setup_inverter_device_data(hass, _entry(hass), device)

    device.get_optimizer_system_information_data.assert_awaited_once()
    device.get_latest_optimizer_history_data.assert_not_awaited()
    assert data.optimizer_device_infos is not None
    assert sorted(data.optimizer_device_infos) == [1, 2]
    assert await async_load_optimizers(hass, SERIAL) is not None


async def test_background_refresh_without_change_does_not_reload(
    hass: HomeAssistant,
) -> None:
    await async_save_optimizers(hass, SERIAL, _system_information())
    entry = _entry(hass)
    device = _device()
    coordinator = MagicMock(async_refresh=AsyncMock())
    hass.config_entries.async_schedule_reload = MagicMock()

    await async_refresh_optimizers(hass, entry, device, coordinator)

    coordinator.async_refresh.assert_awaited_once()
    hass.config_entries.async_schedule_reload.assert_not_called()


async def test_background_refresh_with_changed_optimizers_reloads(
    hass: HomeAssistant,
) -> None:
    await async_save_optimizers(hass, SERIAL, _system_information("V100R002C10SPC019"))
    entry = _entry(hass)
    device = _device()
    device.get_optimizer_system_information_data.return_value = _system_information(
        "V100R002C10SPC028"
    )
    coordinator = MagicMock(async_refresh=AsyncMock())
    hass.config_entries.async_schedule_reload = MagicMock()

    await async_refresh_optimizers(hass, entry, device, coordinator)

    hass.config_entries.async_schedule_reload.assert_called_once_with(entry.entry_id)
    cached = await async_load_optimizers(hass, SERIAL)
    assert cached is not None
    assert cached[1].software_version == "V100R002C10SPC028"
