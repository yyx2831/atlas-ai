import pytest
from pydantic import ValidationError

from app.schemas.device import DeviceCreate, DeviceUpdate


@pytest.mark.parametrize("model", [DeviceCreate, DeviceUpdate])
def test_blank_name_rejected(model):
    with pytest.raises(ValidationError):
        model(name="   ", device_type="router", ip="192.0.2.1")


def test_name_normalized():
    assert (
        DeviceCreate(name="  router  ", device_type="router", ip="192.0.2.1").name
        == "router"
    )
