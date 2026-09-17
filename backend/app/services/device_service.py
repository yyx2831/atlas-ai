from app.schemas.device import DeviceCreate, DeviceUpdate

_devices: list[dict] = []
_next_id = 1
def calculate_total(prices: list[float]) -> float:
    return sum(prices)

def group_devices(devices: list[dict]) -> dict[str, list[dict]]:
    groups = {}
    for device in devices:
        group_name = device["group"]
        if group_name not in groups:
            groups[group_name] = []
        groups[group_name].append(device)
    return groups

def filter_alarm_devices(
    devices: list[dict],
    level: str = "critical"
) -> list[dict]:
    return [device for device in devices if device.get("level") == level]
def list_devices() -> list[dict]:
    return _devices
def get_device(device_id: int) -> dict | None:
    for device in _devices:
        if device["id"] == device_id:
            return device
    return None

def create_device(data: DeviceCreate) -> dict:
    global _next_id
    device = {
        "id": _next_id,
        **data.model_dump(mode="json"),
    }
    _next_id += 1
    _devices.append(device)
    return device


def update_device(device_id: int, data: DeviceUpdate) -> dict | None:
    device = get_device(device_id)
    if device is None:
        return None

    update_data = data.model_dump(
        exclude_unset=True,
        exclude_none=True,
        mode="json",
    )
    device.update(update_data)
    return device


def delete_device(device_id: int) -> bool:
    device = get_device(device_id)
    if device is None:
        return False
    _devices.remove(device)
    return True