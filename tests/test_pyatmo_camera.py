"""Define tests for Camera module."""
import json

import pytest
from freezegun import freeze_time

import pyatmo

INVALID_NAME = "InvalidName"


def test_CameraData(cameraHomeData):
    assert cameraHomeData.default_home == "MYHOME"
    assert cameraHomeData.default_camera["id"] == "12:34:56:00:f1:62"
    assert cameraHomeData.default_camera["name"] == "Hall"


@pytest.mark.parametrize(
    "hid, expected",
    [
        ("91763b24c43d3e344f424e8b", "MYHOME"),
        (INVALID_NAME, "MYHOME"),
        pytest.param(None, None),
    ],
)
def test_CameraData_homeById(cameraHomeData, hid, expected):
    if hid is None or hid == INVALID_NAME:
        assert cameraHomeData.homeById(hid) is None
    else:
        assert cameraHomeData.homeById(hid)["name"] == expected


@pytest.mark.parametrize(
    "name, expected",
    [
        ("MYHOME", "91763b24c43d3e344f424e8b"),
        (None, "91763b24c43d3e344f424e8b"),
        ("", "91763b24c43d3e344f424e8b"),
        pytest.param(INVALID_NAME, None),
    ],
)
def test_CameraData_homeByName(cameraHomeData, name, expected):
    if name == INVALID_NAME:
        with pytest.raises(pyatmo.exceptions.InvalidHome):
            assert cameraHomeData.homeByName(name)
    else:
        assert cameraHomeData.homeByName(name)["id"] == expected


@pytest.mark.parametrize(
    "cid, expected",
    [
        ("12:34:56:00:f1:62", "Hall"),
        ("12:34:56:00:a5:a4", "Garden"),
        ("None", None),
        (None, None),
    ],
)
def test_CameraData_cameraById(cameraHomeData, cid, expected):
    camera = cameraHomeData.cameraById(cid)
    if camera:
        assert camera["name"] == expected
    else:
        assert camera is expected


@pytest.mark.parametrize(
    "name, home, home_id, expected",
    [
        ("Hall", None, None, "12:34:56:00:f1:62"),
        (None, None, None, "12:34:56:00:f1:62"),
        ("", None, None, "12:34:56:00:f1:62"),
        ("Hall", "MYHOME", None, "12:34:56:00:f1:62"),
        ("Hall", None, "91763b24c43d3e344f424e8b", "12:34:56:00:f1:62"),
        (None, None, "91763b24c43d3e344f424e8b", "12:34:56:00:f1:62"),
        (None, "MYHOME", None, "12:34:56:00:f1:62"),
        ("", "MYHOME", None, "12:34:56:00:f1:62"),
        ("Garden", "MYHOME", None, "12:34:56:00:a5:a4"),
        ("Garden", None, "InvalidHomeID", "12:34:56:00:a5:a4"),
        (INVALID_NAME, None, None, None),
        (None, INVALID_NAME, None, None),
    ],
)
def test_CameraData_cameraByName(cameraHomeData, name, home, home_id, expected):
    if home == INVALID_NAME or name == INVALID_NAME or home_id == "InvalidHomeID":
        assert cameraHomeData.cameraByName(name, home, home_id) is None
    elif home_id is None:
        assert cameraHomeData.cameraByName(name, home)["id"] == expected
    elif home is None:
        assert cameraHomeData.cameraByName(name, home_id=home_id)["id"] == expected
    else:
        assert cameraHomeData.cameraByName(name, home, home_id)["id"] == expected


def test_CameraData_moduleById(cameraHomeData):
    assert cameraHomeData.moduleById("00:00:00:00:00:00") is None


def test_CameraData_moduleByName(cameraHomeData):
    assert cameraHomeData.moduleByName() is None


@pytest.mark.parametrize(
    "camera, home, cid, expected",
    [
        (None, None, None, "NACamera"),
        ("Hall", None, None, "NACamera"),
        ("Hall", "MYHOME", None, "NACamera"),
        (None, "MYHOME", None, "NACamera"),
        (None, "MYHOME", "12:34:56:00:f1:62", "NACamera"),
        (None, None, "12:34:56:00:f1:62", "NACamera"),
        ("Garden", None, None, "NOC"),
        (INVALID_NAME, None, None, None),
        pytest.param(None, INVALID_NAME, None, None),
    ],
)
def test_CameraData_cameraType(cameraHomeData, camera, home, cid, expected):
    assert cameraHomeData.cameraType(camera, home, cid) == expected


def test_CameraData_cameraUrls(cameraHomeData, requests_mock):
    vpn_url = (
        "https://prodvpn-eu-2.netatmo.net/restricted/10.255.248.91/"
        "6d278460699e56180d47ab47169efb31/"
        "MpEylTU2MDYzNjRVD-LJxUnIndumKzLboeAwMDqTTg,,"
    )
    local_url = "http://192.168.0.123/678460a0d47e5618699fb31169e2b47d"
    with open("fixtures/camera_ping.json") as f:
        json_fixture = json.load(f)
    requests_mock.post(
        vpn_url + "/command/ping",
        json=json_fixture,
        headers={"content-type": "application/json"},
    )
    with open("fixtures/camera_ping.json") as f:
        json_fixture = json.load(f)
    requests_mock.post(
        local_url + "/command/ping",
        json=json_fixture,
        headers={"content-type": "application/json"},
    )
    assert cameraHomeData.cameraUrls() == (vpn_url, local_url)


def test_CameraData_cameraUrls_disconnected(auth, requests_mock):
    with open("fixtures/camera_home_data_disconnected.json") as f:
        json_fixture = json.load(f)
    requests_mock.post(
        pyatmo.camera._GETHOMEDATA_REQ,
        json=json_fixture,
        headers={"content-type": "application/json"},
    )
    camera_data = pyatmo.CameraData(auth)
    assert camera_data.cameraUrls() == (None, None)


@pytest.mark.parametrize(
    "home, expected",
    [
        (None, ["Richard Doe"]),
        ("MYHOME", ["Richard Doe"]),
        pytest.param(
            INVALID_NAME,
            None,
            # marks=pytest.mark.xfail(reason="Invalid home name not handled yet"),
        ),
    ],
)
def test_CameraData_personsAtHome(cameraHomeData, home, expected):
    if home == INVALID_NAME:
        with pytest.raises(pyatmo.exceptions.InvalidHome):
            assert cameraHomeData.personsAtHome(home)
    else:
        assert cameraHomeData.personsAtHome(home) == expected


@freeze_time("2019-06-16")
@pytest.mark.parametrize(
    "name, exclude, expected",
    [
        ("John Doe", None, True),
        ("Richard Doe", None, False),
        ("Unknown", None, False),
        ("John Doe", 1, False),
        ("John Doe", 50000, True),
        ("Jack Doe", None, False),
    ],
)
def test_CameraData_personSeenByCamera(cameraHomeData, name, exclude, expected):
    assert cameraHomeData.personSeenByCamera(name, exclude=exclude) is expected


def test_CameraData__knownPersons(cameraHomeData):
    knownPersons = cameraHomeData._knownPersons()
    assert len(knownPersons) == 3
    assert knownPersons["91827374-7e04-5298-83ad-a0cb8372dff1"]["pseudo"] == "John Doe"


def test_CameraData_knownPersonsNames(cameraHomeData):
    assert sorted(cameraHomeData.knownPersonsNames()) == [
        "Jane Doe",
        "John Doe",
        "Richard Doe",
    ]


@freeze_time("2019-06-16")
@pytest.mark.parametrize(
    "name, expected",
    [
        ("John Doe", "91827374-7e04-5298-83ad-a0cb8372dff1"),
        ("Richard Doe", "91827376-7e04-5298-83af-a0cb8372dff3"),
    ],
)
def test_CameraData_getPersonId(cameraHomeData, name, expected):
    assert cameraHomeData.getPersonId(name) == expected


@pytest.mark.parametrize(
    "hid, pid, json_fixture, expected",
    [
        (
            "91763b24c43d3e344f424e8b",
            "91827374-7e04-5298-83ad-a0cb8372dff1",
            "status_ok.json",
            "ok",
        ),
        (
            "91763b24c43d3e344f424e8b",
            "91827376-7e04-5298-83af-a0cb8372dff3",
            "status_ok.json",
            "ok",
        ),
    ],
)
def test_CameraData_setPersonsAway(
    cameraHomeData, requests_mock, hid, pid, json_fixture, expected
):
    with open("fixtures/%s" % json_fixture) as f:
        json_fixture = json.load(f)
    requests_mock.post(
        pyatmo.camera._SETPERSONSAWAY_REQ,
        json=json_fixture,
        headers={"content-type": "application/json"},
    )
    assert cameraHomeData.setPersonsAway(pid, hid)["status"] == expected


@pytest.mark.parametrize(
    "hid, pids, json_fixture, expected",
    [
        (
            "91763b24c43d3e344f424e8b",
            [
                "91827374-7e04-5298-83ad-a0cb8372dff1",
                "91827376-7e04-5298-83af-a0cb8372dff3",
            ],
            "status_ok.json",
            "ok",
        ),
        (
            "91763b24c43d3e344f424e8b",
            "91827376-7e04-5298-83af-a0cb8372dff3",
            "status_ok.json",
            "ok",
        ),
    ],
)
def test_CameraData_setPersonsHome(
    cameraHomeData, requests_mock, hid, pids, json_fixture, expected
):
    with open("fixtures/%s" % json_fixture) as f:
        json_fixture = json.load(f)
    requests_mock.post(
        pyatmo.camera._SETPERSONSHOME_REQ,
        json=json_fixture,
        headers={"content-type": "application/json"},
    )
    assert cameraHomeData.setPersonsHome(pids, hid)["status"] == expected


@freeze_time("2019-06-16")
@pytest.mark.parametrize(
    "home, camera, exclude, expected",
    [
        (None, None, None, True),
        (None, None, 5, False),
        (None, "InvalidCamera", None, False),
        ("InvalidHome", None, None, False),
    ],
)
def test_CameraData_someoneKnownSeen(cameraHomeData, home, camera, exclude, expected):
    assert cameraHomeData.someoneKnownSeen(home, camera, exclude) == expected


@freeze_time("2019-06-16")
@pytest.mark.parametrize(
    "home, camera, exclude, expected",
    [
        (None, None, None, False),
        (None, None, 100, False),
        (None, INVALID_NAME, None, False),
        (INVALID_NAME, None, None, False),
    ],
)
def test_CameraData_someoneUnknownSeen(cameraHomeData, home, camera, exclude, expected):
    assert cameraHomeData.someoneUnknownSeen(home, camera, exclude) == expected


@freeze_time("2019-06-16")
@pytest.mark.parametrize(
    "home, camera, exclude, expected",
    [
        (None, None, None, False),
        (None, None, 140000, True),
        (None, None, 130000, False),
        (None, INVALID_NAME, None, False),
        (INVALID_NAME, None, None, False),
    ],
)
def test_CameraData_motionDetected(cameraHomeData, home, camera, exclude, expected):
    assert cameraHomeData.motionDetected(home, camera, exclude) == expected


def test_CameraData_getHomeName(cameraHomeData):
    assert cameraHomeData.getHomeName() == "MYHOME"
    home_id = "91763b24c43d3e344f424e8b"
    assert cameraHomeData.getHomeName(home_id) == "MYHOME"
    home_id = "91763b24c43d3e344f424e8c"
    assert cameraHomeData.getHomeName(home_id) == "Unknown"
    home_id = "InvalidHomeID"
    with pytest.raises(pyatmo.InvalidHome):
        assert cameraHomeData.getHomeName(home_id) == "Unknown"


def test_CameraData_gethomeId(cameraHomeData):
    assert cameraHomeData.gethomeId() == "91763b24c43d3e344f424e8b"
    assert cameraHomeData.gethomeId("MYHOME") == "91763b24c43d3e344f424e8b"
    with pytest.raises(pyatmo.InvalidHome):
        assert cameraHomeData.gethomeId("InvalidName")


@pytest.mark.parametrize(
    "sid, expected",
    [
        ("12:34:56:00:8b:a2", "Hall"),
        ("12:34:56:00:8b:ac", "Kitchen"),
        ("None", None),
        (None, None),
    ],
)
def test_CameraData_smokedetectorById(cameraHomeData, sid, expected):
    smokedetector = cameraHomeData.smokedetectorById(sid)
    if smokedetector:
        assert smokedetector["name"] == expected
    else:
        assert smokedetector is expected


@pytest.mark.parametrize(
    "name, home, home_id, expected",
    [
        ("Hall", None, None, "12:34:56:00:8b:a2"),
        (None, None, None, None),
        ("", None, None, "12:34:56:00:8b:a2"),
        ("Hall", "MYHOME", None, "12:34:56:00:8b:a2"),
        ("Hall", None, "91763b24c43d3e344f424e8b", "12:34:56:00:8b:a2"),
        (None, None, "91763b24c43d3e344f424e8b", "12:34:56:00:8b:a2"),
        (None, "MYHOME", None, "12:34:56:00:8b:a2"),
        ("", "MYHOME", None, "12:34:56:00:8b:a2"),
        ("Kitchen", "MYHOME", None, "12:34:56:00:8b:ac"),
        (INVALID_NAME, None, None, None),
        (None, INVALID_NAME, None, None),
    ],
)
def test_CameraData_smokedetectorByName(cameraHomeData, name, home, home_id, expected):
    if (
        home == INVALID_NAME
        or name == INVALID_NAME
        or (name is None and home is None and home_id is None)
    ):
        assert cameraHomeData.smokedetectorByName(name, home, home_id) is None
    elif home_id is None:
        assert cameraHomeData.smokedetectorByName(name, home)["id"] == expected
    elif home is None:
        assert (
            cameraHomeData.smokedetectorByName(name, home_id=home_id)["id"] == expected
        )
    else:
        assert cameraHomeData.smokedetectorByName(name, home, home_id)["id"] == expected


@pytest.mark.parametrize(
    "home_id, camera_id, floodlight, monitoring, json_fixture, expected",
    [
        (
            "91763b24c43d3e344f424e8b",
            "12:34:56:00:f1:ff",
            "on",
            None,
            "camera_set_state_error.json",
            False,
        ),
        (
            "91763b24c43d3e344f424e8b",
            "12:34:56:00:f1:62",
            None,
            "on",
            "camera_set_state_ok.json",
            True,
        ),
        (None, "12:34:56:00:f1:62", None, "on", "camera_set_state_ok.json", True,),
        (
            "91763b24c43d3e344f424e8b",
            "12:34:56:00:f1:62",
            "auto",
            "on",
            "camera_set_state_ok.json",
            True,
        ),
        (
            "91763b24c43d3e344f424e8b",
            "12:34:56:00:f1:62",
            None,
            "on",
            "camera_set_state_error_already_on.json",
            True,
        ),
        (
            "91763b24c43d3e344f424e8b",
            "12:34:56:00:f1:62",
            "on",
            None,
            "camera_set_state_error_wrong_parameter.json",
            False,
        ),
    ],
)
def test_CameraData_set_state(
    cameraHomeData,
    requests_mock,
    home_id,
    camera_id,
    floodlight,
    monitoring,
    json_fixture,
    expected,
):
    with open("fixtures/%s" % json_fixture) as f:
        json_fixture = json.load(f)
    requests_mock.post(
        pyatmo.camera._SETSTATE_REQ,
        json=json_fixture,
        headers={"content-type": "application/json"},
    )
    assert (
        cameraHomeData.set_state(
            home_id=home_id,
            camera_id=camera_id,
            floodlight=floodlight,
            monitoring=monitoring,
        )
        == expected
    )
