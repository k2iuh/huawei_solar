"""Optimizer device information cache and background refresh.

Reading the optimizer files from an inverter takes tens of seconds. The device information
(serial number, model, software version) rarely changes, so it is cached in Home Assistant's
storage and the config entry setup uses the cache. The current values and a fresh copy of the
device information are read in the background after setup.
"""

from dataclasses import asdict, dataclass
import logging

from huawei_solar import HuaweiSolarException, SUN2000Device
from huawei_solar.files import OptimizerSystemInformation

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .update_coordinator import HuaweiSolarOptimizerUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1


@dataclass(frozen=True)
class CachedOptimizer:
    """The optimizer device information that the integration needs."""

    sn: str
    model: str
    software_version: str


def _store(
    hass: HomeAssistant, inverter_serial: str
) -> Store[dict[str, dict[str, str]]]:
    return Store(hass, STORAGE_VERSION, f"{DOMAIN}.optimizers.{inverter_serial}")


def _to_cached(
    infos: dict[int, OptimizerSystemInformation],
) -> dict[int, CachedOptimizer]:
    return {
        address: CachedOptimizer(info.sn, info.model, info.software_version)
        for address, info in infos.items()
    }


async def async_load_optimizers(
    hass: HomeAssistant, inverter_serial: str
) -> dict[int, CachedOptimizer] | None:
    """Return the cached optimizers of an inverter, or None if nothing is cached."""
    data = await _store(hass, inverter_serial).async_load()
    if data is None:
        return None
    return {int(address): CachedOptimizer(**info) for address, info in data.items()}


async def async_save_optimizers(
    hass: HomeAssistant,
    inverter_serial: str,
    infos: dict[int, OptimizerSystemInformation],
) -> dict[int, CachedOptimizer]:
    """Cache the optimizers of an inverter and return the cached form."""
    cached = _to_cached(infos)
    await _store(hass, inverter_serial).async_save(
        {str(address): asdict(info) for address, info in cached.items()}
    )
    return cached


async def async_refresh_optimizers(
    hass: HomeAssistant,
    entry: ConfigEntry,
    device: SUN2000Device,
    coordinator: HuaweiSolarOptimizerUpdateCoordinator,
) -> None:
    """Fetch the first optimizer values, then check whether the cached device information is current.

    If the optimizers changed (added, removed or updated), the cache is updated and the config
    entry is reloaded so that devices and entities match.
    """
    await coordinator.async_refresh()

    try:
        infos = await device.get_optimizer_system_information_data()
    except HuaweiSolarException as err:
        _LOGGER.debug(
            "Could not refresh optimizer device information of %s: %s",
            device.serial_number,
            err,
        )
        return

    if _to_cached(infos) != await async_load_optimizers(hass, device.serial_number):
        await async_save_optimizers(hass, device.serial_number, infos)
        _LOGGER.info(
            "Optimizers of %s changed, reloading the integration",
            device.serial_number,
        )
        hass.config_entries.async_schedule_reload(entry.entry_id)
