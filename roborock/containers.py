from __future__ import annotations

import datetime
import json
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import timezone
from enum import Enum
from typing import Any, NamedTuple

from dacite import Config, from_dict

from .code_mappings import (
    RoborockCategory,
    RoborockDockDustCollectionModeCode,
    RoborockDockErrorCode,
    RoborockDockTypeCode,
    RoborockDockWashTowelModeCode,
    RoborockErrorCode,
    RoborockFanPowerCode,
    RoborockFanSpeedP10,
    RoborockFanSpeedQ7Max,
    RoborockFanSpeedS6Pure,
    RoborockFanSpeedS7,
    RoborockFanSpeedS7MaxV,
    RoborockMopIntensityCode,
    RoborockMopIntensityP10,
    RoborockMopIntensityS5Max,
    RoborockMopIntensityS6MaxV,
    RoborockMopIntensityS7,
    RoborockMopIntensityV2,
    RoborockMopModeCode,
    RoborockMopModeS7,
    RoborockMopModeS8ProUltra,
    RoborockStateCode,
)
from .const import (
    FILTER_REPLACE_TIME,
    MAIN_BRUSH_REPLACE_TIME,
    ROBOROCK_G10S_PRO,
    ROBOROCK_P10,
    ROBOROCK_Q7_MAX,
    ROBOROCK_S4_MAX,
    ROBOROCK_S5_MAX,
    ROBOROCK_S6,
    ROBOROCK_S6_MAXV,
    ROBOROCK_S6_PURE,
    ROBOROCK_S7,
    ROBOROCK_S7_MAXV,
    ROBOROCK_S8,
    ROBOROCK_S8_PRO_ULTRA,
    SENSOR_DIRTY_REPLACE_TIME,
    SIDE_BRUSH_REPLACE_TIME,
)
from .exceptions import RoborockException

_LOGGER = logging.getLogger(__name__)


def camelize(s: str):
    first, *others = s.split("_")
    if len(others) == 0:
        return s
    return "".join([first.lower(), *map(str.title, others)])


def decamelize(s: str):
    return re.sub("([A-Z]+)", "_\\1", s).lower()


def decamelize_obj(d: dict | list, ignore_keys: list[str]):
    if isinstance(d, RoborockBase):
        d = d.as_dict()
    if isinstance(d, list):
        return [decamelize_obj(i, ignore_keys) if isinstance(i, dict | list) else i for i in d]
    return {
        (decamelize(a) if a not in ignore_keys else a): decamelize_obj(b, ignore_keys)
        if isinstance(b, dict | list)
        else b
        for a, b in d.items()
    }


@dataclass
class RoborockBase:
    _ignore_keys = []  # type: ignore
    is_cached = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        if isinstance(data, dict):
            ignore_keys = cls._ignore_keys
            try:
                return from_dict(cls, decamelize_obj(data, ignore_keys), config=Config(cast=[Enum]))
            except AttributeError as err:
                raise RoborockException("It seems like you have an outdated version of dacite.") from err

    def as_dict(self) -> dict:
        return asdict(
            self,
            dict_factory=lambda _fields: {
                camelize(key): value.value if isinstance(value, Enum) else value
                for (key, value) in _fields
                if value is not None
            },
        )


@dataclass
class RoborockBaseTimer(RoborockBase):
    start_hour: int | None = None
    start_minute: int | None = None
    end_hour: int | None = None
    end_minute: int | None = None
    enabled: int | None = None
    start_time: datetime.time | None = None
    end_time: datetime.time | None = None

    def __post_init__(self) -> None:
        self.start_time = (
            datetime.time(hour=self.start_hour, minute=self.start_minute)
            if self.start_hour is not None and self.start_minute is not None
            else None
        )
        self.end_time = (
            datetime.time(hour=self.end_hour, minute=self.end_minute)
            if self.end_hour is not None and self.end_minute is not None
            else None
        )


@dataclass
class Reference(RoborockBase):
    r: str | None = None
    a: str | None = None
    m: str | None = None
    l: str | None = None


@dataclass
class RRiot(RoborockBase):
    u: str
    s: str
    h: str
    k: str
    r: Reference


@dataclass
class UserData(RoborockBase):
    uid: int | None = None
    tokentype: str | None = None
    token: str | None = None
    rruid: str | None = None
    region: str | None = None
    countrycode: str | None = None
    country: str | None = None
    nickname: str | None = None
    rriot: RRiot | None = None
    tuya_device_state: int | None = None
    avatarurl: str | None = None


@dataclass
class HomeDataProductSchema(RoborockBase):
    id: Any | None = None
    name: Any | None = None
    code: Any | None = None
    mode: Any | None = None
    type: Any | None = None
    product_property: Any | None = None
    desc: Any | None = None


@dataclass
class HomeDataProduct(RoborockBase):
    id: str
    name: str
    model: str
    category: RoborockCategory
    code: str | None = None
    iconurl: str | None = None
    attribute: Any | None = None
    capability: int | None = None
    schema: list[HomeDataProductSchema] | None = None


@dataclass
class HomeDataDevice(RoborockBase):
    duid: str
    name: str
    local_key: str
    fv: str
    product_id: str
    attribute: Any | None = None
    active_time: int | None = None
    runtime_env: Any | None = None
    time_zone_id: str | None = None
    icon_url: str | None = None
    lon: Any | None = None
    lat: Any | None = None
    share: Any | None = None
    share_time: Any | None = None
    online: bool | None = None
    pv: str | None = None
    room_id: Any | None = None
    tuya_uuid: Any | None = None
    tuya_migrated: bool | None = None
    extra: Any | None = None
    sn: str | None = None
    feature_set: str | None = None
    new_feature_set: str | None = None
    device_status: dict | None = None
    silent_ota_switch: bool | None = None
    setting: Any | None = None
    f: bool | None = None


@dataclass
class HomeDataRoom(RoborockBase):
    id: int
    name: str


@dataclass
class HomeData(RoborockBase):
    id: int
    name: str
    products: list[HomeDataProduct] = field(default_factory=lambda: [])
    devices: list[HomeDataDevice] = field(default_factory=lambda: [])
    received_devices: list[HomeDataDevice] = field(default_factory=lambda: [])
    lon: Any | None = None
    lat: Any | None = None
    geo_name: Any | None = None
    rooms: list[HomeDataRoom] = field(default_factory=list)

    def get_all_devices(self) -> list[HomeDataDevice]:
        devices = []
        if self.devices is not None:
            devices += self.devices
        if self.received_devices is not None:
            devices += self.received_devices
        return devices


@dataclass
class LoginData(RoborockBase):
    user_data: UserData
    email: str
    home_data: HomeData | None = None


@dataclass
class Status(RoborockBase):
    msg_ver: int | None = None
    msg_seq: int | None = None
    state: RoborockStateCode | None = None
    battery: int | None = None
    clean_time: int | None = None
    clean_area: int | None = None
    square_meter_clean_area: float | None = None
    error_code: RoborockErrorCode | None = None
    map_present: int | None = None
    in_cleaning: int | None = None
    in_returning: int | None = None
    in_fresh_state: int | None = None
    lab_status: int | None = None
    water_box_status: int | None = None
    back_type: int | None = None
    wash_phase: int | None = None
    wash_ready: int | None = None
    fan_power: RoborockFanPowerCode | None = None
    dnd_enabled: int | None = None
    map_status: int | None = None
    is_locating: int | None = None
    lock_status: int | None = None
    water_box_mode: RoborockMopIntensityCode | None = None
    water_box_carriage_status: int | None = None
    mop_forbidden_enable: int | None = None
    camera_status: int | None = None
    is_exploring: int | None = None
    home_sec_status: int | None = None
    home_sec_enable_password: int | None = None
    adbumper_status: list[int] | None = None
    water_shortage_status: int | None = None
    dock_type: RoborockDockTypeCode | None = None
    dust_collection_status: int | None = None
    auto_dust_collection: int | None = None
    avoid_count: int | None = None
    mop_mode: RoborockMopModeCode | None = None
    debug_mode: int | None = None
    collision_avoid_status: int | None = None
    switch_map_mode: int | None = None
    dock_error_status: RoborockDockErrorCode | None = None
    charge_status: int | None = None
    unsave_map_reason: int | None = None
    unsave_map_flag: int | None = None
    wash_status: int | None = None
    distance_off: int | None = None
    in_warmup: int | None = None
    dry_status: int | None = None
    rdt: int | None = None
    clean_percent: int | None = None
    rss: int | None = None
    dss: int | None = None
    common_status: int | None = None
    corner_clean_mode: int | None = None
    error_code_name: str | None = None
    state_name: str | None = None
    water_box_mode_name: str | None = None
    fan_power_options: list[str] = field(default_factory=list)
    fan_power_name: str | None = None
    mop_mode_name: str | None = None

    def __post_init__(self) -> None:
        self.square_meter_clean_area = round(self.clean_area / 1000000, 1) if self.clean_area is not None else None
        if self.error_code is not None:
            self.error_code_name = self.error_code.name
        if self.state is not None:
            self.state_name = self.state.name
        if self.water_box_mode is not None:
            self.water_box_mode_name = self.water_box_mode.name
        if self.fan_power is not None:
            self.fan_power_options = self.fan_power.keys()
            self.fan_power_name = self.fan_power.name
        if self.mop_mode is not None:
            self.mop_mode_name = self.mop_mode.name

    def get_fan_speed_code(self, fan_speed: str) -> int:
        if self.fan_power is None:
            raise RoborockException("Attempted to get fan speed before status has been updated.")
        return self.fan_power.as_dict().get(fan_speed)

    def get_mop_intensity_code(self, mop_intensity: str) -> int:
        if self.water_box_mode is None:
            raise RoborockException("Attempted to get mop_intensity before status has been updated.")
        return self.water_box_mode.as_dict().get(mop_intensity)

    def get_mop_mode_code(self, mop_mode: str) -> int:
        if self.mop_mode is None:
            raise RoborockException("Attempted to get mop_mode before status has been updated.")
        return self.mop_mode.as_dict().get(mop_mode)


@dataclass
class S4MaxStatus(Status):
    fan_power: RoborockFanSpeedS6Pure | None = None
    water_box_mode: RoborockMopIntensityS7 | None = None
    mop_mode: RoborockMopModeS7 | None = None


@dataclass
class S5MaxStatus(Status):
    fan_power: RoborockFanSpeedS6Pure | None = None
    water_box_mode: RoborockMopIntensityS5Max | None = None


@dataclass
class Q7MaxStatus(Status):
    fan_power: RoborockFanSpeedQ7Max | None = None
    water_box_mode: RoborockMopIntensityV2 | None = None


@dataclass
class S6MaxVStatus(Status):
    fan_power: RoborockFanSpeedS7MaxV | None = None
    water_box_mode: RoborockMopIntensityS6MaxV | None = None


@dataclass
class S6PureStatus(Status):
    fan_power: RoborockFanSpeedS6Pure | None = None


@dataclass
class S7MaxVStatus(Status):
    fan_power: RoborockFanSpeedS7MaxV | None = None
    water_box_mode: RoborockMopIntensityS7 | None = None
    mop_mode: RoborockMopModeS7 | None = None


@dataclass
class S7Status(Status):
    fan_power: RoborockFanSpeedS7 | None = None
    water_box_mode: RoborockMopIntensityS7 | None = None
    mop_mode: RoborockMopModeS7 | None = None


@dataclass
class S8ProUltraStatus(Status):
    fan_power: RoborockFanSpeedS7MaxV | None = None
    water_box_mode: RoborockMopIntensityS7 | None = None
    mop_mode: RoborockMopModeS8ProUltra | None = None


@dataclass
class S8Status(Status):
    fan_power: RoborockFanSpeedS7MaxV | None = None
    water_box_mode: RoborockMopIntensityS7 | None = None
    mop_mode: RoborockMopModeS8ProUltra | None = None


@dataclass
class P10Status(Status):
    fan_power: RoborockFanSpeedP10 | None = None
    water_box_mode: RoborockMopIntensityP10 | None = None
    mop_mode: RoborockMopModeS8ProUltra | None = None


ModelStatus: dict[str, type[Status]] = {
    ROBOROCK_S4_MAX: S4MaxStatus,
    ROBOROCK_S5_MAX: S5MaxStatus,
    ROBOROCK_Q7_MAX: Q7MaxStatus,
    ROBOROCK_S6: S6PureStatus,
    ROBOROCK_S6_MAXV: S6MaxVStatus,
    ROBOROCK_S6_PURE: S6PureStatus,
    ROBOROCK_S7_MAXV: S7MaxVStatus,
    ROBOROCK_S7: S7Status,
    ROBOROCK_S8: S8Status,
    ROBOROCK_S8_PRO_ULTRA: S8ProUltraStatus,
    ROBOROCK_G10S_PRO: S7MaxVStatus,
    ROBOROCK_P10: P10Status,
}


@dataclass
class DnDTimer(RoborockBaseTimer):
    """DnDTimer"""


@dataclass
class ValleyElectricityTimer(RoborockBaseTimer):
    """ValleyElectricityTimer"""


@dataclass
class CleanSummary(RoborockBase):
    clean_time: int | None = None
    clean_area: int | None = None
    square_meter_clean_area: float | None = None
    clean_count: int | None = None
    dust_collection_count: int | None = None
    records: list[int] | None = None
    last_clean_t: int | None = None

    def __post_init__(self) -> None:
        self.square_meter_clean_area = round(self.clean_area / 1000000, 1) if self.clean_area is not None else None


@dataclass
class CleanRecord(RoborockBase):
    begin: int | None = None
    begin_datetime: datetime.datetime | None = None
    end: int | None = None
    end_datetime: datetime.datetime | None = None
    duration: int | None = None
    area: int | None = None
    square_meter_area: float | None = None
    error: int | None = None
    complete: int | None = None
    start_type: int | None = None
    clean_type: int | None = None
    finish_reason: int | None = None
    dust_collection_status: int | None = None
    avoid_count: int | None = None
    wash_count: int | None = None
    map_flag: int | None = None

    def __post_init__(self) -> None:
        self.square_meter_area = round(self.area / 1000000, 1) if self.area is not None else None
        self.begin_datetime = (
            datetime.datetime.fromtimestamp(self.begin).astimezone(timezone.utc) if self.begin else None
        )
        self.end_datetime = datetime.datetime.fromtimestamp(self.end).astimezone(timezone.utc) if self.end else None


@dataclass
class Consumable(RoborockBase):
    main_brush_work_time: int | None = None
    side_brush_work_time: int | None = None
    filter_work_time: int | None = None
    filter_element_work_time: int | None = None
    sensor_dirty_time: int | None = None
    strainer_work_times: int | None = None
    dust_collection_work_times: int | None = None
    cleaning_brush_work_times: int | None = None
    main_brush_time_left: int | None = None
    side_brush_time_left: int | None = None
    filter_time_left: int | None = None
    sensor_time_left: int | None = None

    def __post_init__(self) -> None:
        self.main_brush_time_left = (
            MAIN_BRUSH_REPLACE_TIME - self.main_brush_work_time if self.main_brush_work_time is not None else None
        )
        self.side_brush_time_left = (
            SIDE_BRUSH_REPLACE_TIME - self.side_brush_work_time if self.side_brush_work_time is not None else None
        )
        self.filter_time_left = (
            FILTER_REPLACE_TIME - self.filter_work_time if self.filter_work_time is not None else None
        )
        self.sensor_time_left = (
            SENSOR_DIRTY_REPLACE_TIME - self.sensor_dirty_time if self.sensor_dirty_time is not None else None
        )


@dataclass
class MultiMapsListMapInfoBakMaps(RoborockBase):
    mapflag: Any | None = None
    add_time: Any | None = None


@dataclass
class MultiMapsListMapInfo(RoborockBase):
    _ignore_keys = ["mapFlag"]

    mapFlag: int
    name: str
    add_time: Any | None = None
    length: Any | None = None
    bak_maps: list[MultiMapsListMapInfoBakMaps] | None = None


@dataclass
class MultiMapsList(RoborockBase):
    _ignore_keys = ["mapFlag"]

    max_multi_map: int | None = None
    max_bak_map: int | None = None
    multi_map_count: int | None = None
    map_info: list[MultiMapsListMapInfo] | None = None


@dataclass
class SmartWashParams(RoborockBase):
    smart_wash: int | None = None
    wash_interval: int | None = None


@dataclass
class DustCollectionMode(RoborockBase):
    mode: RoborockDockDustCollectionModeCode | None = None


@dataclass
class WashTowelMode(RoborockBase):
    wash_mode: RoborockDockWashTowelModeCode | None = None


@dataclass
class NetworkInfo(RoborockBase):
    ip: str
    ssid: str | None = None
    mac: str | None = None
    bssid: str | None = None
    rssi: int | None = None


@dataclass
class DeviceData(RoborockBase):
    device: HomeDataDevice
    model: str
    host: str | None = None


@dataclass
class RoomMapping(RoborockBase):
    segment_id: int
    iot_id: str


@dataclass
class ChildLockStatus(RoborockBase):
    lock_status: int


@dataclass
class FlowLedStatus(RoborockBase):
    status: int


@dataclass
class BroadcastMessage(RoborockBase):
    duid: str
    ip: str


class ServerTimer(NamedTuple):
    id: str
    status: str
    dontknow: int


@dataclass
class RoborockProductStateValue(RoborockBase):
    value: list
    desc: dict


@dataclass
class RoborockProductState(RoborockBase):
    dps: int
    desc: dict
    value: list[RoborockProductStateValue]


@dataclass
class RoborockProductSpec(RoborockBase):
    state: RoborockProductState
    battery: dict | None = None
    dry_countdown: dict | None = None
    extra: dict | None = None
    offpeak: dict | None = None
    countdown: dict | None = None
    mode: dict | None = None
    ota_nfo: dict | None = None
    pause: dict | None = None
    program: dict | None = None
    shutdown: dict | None = None
    washing_left: dict | None = None


@dataclass
class RoborockProduct(RoborockBase):
    id: int
    name: str
    model: str
    packagename: str
    ssid: str
    picurl: str
    cardpicurl: str
    medium_cardpicurl: str
    resetwifipicurl: str
    resetwifitext: dict
    tuyaid: str
    status: int
    rriotid: str
    cardspec: str
    pictures: list
    nc_mode: str
    scope: None
    product_tags: list
    agreements: list
    plugin_pic_url: None
    products_specification: RoborockProductSpec | None = None

    def __post_init__(self):
        if self.cardspec:
            self.products_specification = RoborockProductSpec.from_dict(json.loads(self.cardspec).get("data"))


@dataclass
class RoborockProductCategory(RoborockBase):
    id: int
    display_name: str
    icon_url: str


@dataclass
class RoborockCategoryDetail(RoborockBase):
    category: RoborockProductCategory
    product_list: list[RoborockProduct]


@dataclass
class ProductResponse(RoborockBase):
    category_detail_list: list[RoborockCategoryDetail]
