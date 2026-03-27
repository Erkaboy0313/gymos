import pytest
from users.models import Gym
from branches.models import Branch
from devices.models import Device


@pytest.mark.django_db
def test_kiosk_device_does_not_require_api_key():
    gym = Gym.objects.create(name="G1")
    branch = Branch.objects.create(gym=gym, name="Main")

    d = Device.objects.create(branch=branch, name="Gate 1", mode=Device.MODE_KIOSK)

    assert d.api_key == ""


@pytest.mark.django_db
def test_api_device_auto_generates_api_key():
    gym = Gym.objects.create(name="G1")
    branch = Branch.objects.create(gym=gym, name="Main")

    d = Device.objects.create(branch=branch, name="Gate API", mode=Device.MODE_API)

    assert d.api_key is not None
    assert len(d.api_key) > 10


@pytest.mark.django_db
def test_device_name_unique_per_branch():
    gym = Gym.objects.create(name="G1")
    branch = Branch.objects.create(gym=gym, name="Main")

    Device.objects.create(branch=branch, name="Gate 1")

    with pytest.raises(Exception):
        Device.objects.create(branch=branch, name="Gate 1")