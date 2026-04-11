import json
import math
from dataclasses import dataclass
from typing import Optional

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String

try:
    from smbus2 import SMBus
except ImportError:  # pragma: no cover
    SMBus = None


REG_CONFIG = 0x00
REG_ADC_CONFIG = 0x01
REG_SHUNT_CAL = 0x02
REG_VSHUNT = 0x04
REG_VBUS = 0x05
REG_DIETEMP = 0x06
REG_CURRENT = 0x07
REG_POWER = 0x08
REG_DIAG_ALRT = 0x0B
REG_MANUFACTURER_ID = 0x3E
REG_DEVICE_ID = 0x3F

MANUFACTURER_ID_TI = 0x5449
DEVICE_ID_INA238 = 0x2380


@dataclass
class Ina238Status:
    available: bool
    message: str
    bus_voltage_v: float = math.nan
    current_a: float = math.nan
    power_w: float = math.nan
    temperature_c: float = math.nan
    shunt_voltage_v: float = math.nan
    config_raw: int = 0
    adc_config_raw: int = 0
    shunt_cal_raw: int = 0
    diag_alert_raw: int = 0
    manufacturer_id: int = 0
    device_id: int = 0
    power_raw: int = 0


class Ina238Reader:
    def __init__(self, i2c_bus: int, address: int, shunt_resistance_ohm: float, max_current_a: float) -> None:
        self.i2c_bus = i2c_bus
        self.address = address
        self.shunt_resistance_ohm = shunt_resistance_ohm
        self.max_current_a = max_current_a
        self.current_lsb = max_current_a / 32768.0
        self.power_lsb = self.current_lsb * 0.2
        self.shunt_cal = max(
            1,
            min(0xFFFF, int(round(819_200_000.0 * self.current_lsb * self.shunt_resistance_ohm))),
        )
        self._bus: Optional[SMBus] = None

    def connect(self) -> None:
        if SMBus is None:
            raise RuntimeError("python3-smbus2 is not installed")
        if self._bus is None:
            self._bus = SMBus(self.i2c_bus)
            self._write_u16(REG_SHUNT_CAL, self.shunt_cal)

    def close(self) -> None:
        if self._bus is not None:
            self._bus.close()
            self._bus = None

    def _read_u16(self, reg: int) -> int:
        assert self._bus is not None
        raw = self._bus.read_word_data(self.address, reg)
        return ((raw & 0xFF) << 8) | (raw >> 8)

    def _read_u24(self, reg: int) -> int:
        assert self._bus is not None
        data = self._bus.read_i2c_block_data(self.address, reg, 3)
        return (data[0] << 16) | (data[1] << 8) | data[2]

    def _write_u16(self, reg: int, value: int) -> None:
        assert self._bus is not None
        raw = ((value & 0xFF) << 8) | ((value >> 8) & 0xFF)
        self._bus.write_word_data(self.address, reg, raw)

    @staticmethod
    def _to_signed(value: int) -> int:
        return value - 0x10000 if value & 0x8000 else value

    @staticmethod
    def _dietemp_celsius(temp_raw: int) -> float:
        value = temp_raw >> 4
        if value & 0x800:
            value -= 0x1000
        return value * 0.125

    def read_status(self) -> Ina238Status:
        self.connect()
        assert self._bus is not None

        config = self._read_u16(REG_CONFIG)
        adc_config = self._read_u16(REG_ADC_CONFIG)
        shunt_cal = self._read_u16(REG_SHUNT_CAL)
        vshunt_raw = self._read_u16(REG_VSHUNT)
        vbus_raw = self._read_u16(REG_VBUS)
        temp_raw = self._read_u16(REG_DIETEMP)
        current_raw = self._read_u16(REG_CURRENT)
        power_raw = self._read_u24(REG_POWER)
        diag_alert = self._read_u16(REG_DIAG_ALRT)
        manufacturer_id = self._read_u16(REG_MANUFACTURER_ID)
        device_id = self._read_u16(REG_DEVICE_ID)

        adcrange = (config >> 4) & 0x1
        shunt_lsb = 1.25e-6 if adcrange else 5.0e-6

        bus_voltage_v = vbus_raw * 3.125e-3
        shunt_voltage_v = self._to_signed(vshunt_raw) * shunt_lsb
        temperature_c = self._dietemp_celsius(temp_raw)
        current_a = self._to_signed(current_raw) * self.current_lsb
        power_w = power_raw * self.power_lsb

        available = manufacturer_id == MANUFACTURER_ID_TI and (device_id & 0xFFF0) == DEVICE_ID_INA238
        if available:
            message = "INA238 responding on I2C"
        else:
            message = "I2C device responded, but ID registers do not match INA238"

        return Ina238Status(
            available=available,
            message=message,
            bus_voltage_v=bus_voltage_v,
            current_a=current_a,
            power_w=power_w,
            temperature_c=temperature_c,
            shunt_voltage_v=shunt_voltage_v,
            config_raw=config,
            adc_config_raw=adc_config,
            shunt_cal_raw=shunt_cal,
            diag_alert_raw=diag_alert,
            manufacturer_id=manufacturer_id,
            device_id=device_id,
            power_raw=power_raw,
        )


class Ina238ReaderNode(Node):
    def __init__(self) -> None:
        super().__init__("navbot_ina238_reader")
        self.declare_parameter("i2c_bus", 1)
        self.declare_parameter("i2c_address", 0x40)
        self.declare_parameter("shunt_resistance_ohm", 0.015)
        self.declare_parameter("max_current_a", 10.0)
        self.declare_parameter("poll_hz", 2.0)

        self.reader = Ina238Reader(
            i2c_bus=int(self.get_parameter("i2c_bus").value),
            address=int(self.get_parameter("i2c_address").value),
            shunt_resistance_ohm=float(self.get_parameter("shunt_resistance_ohm").value),
            max_current_a=float(self.get_parameter("max_current_a").value),
        )

        self.bus_voltage_pub = self.create_publisher(Float32, "/power/ina238/bus_voltage_v", 10)
        self.current_pub = self.create_publisher(Float32, "/power/ina238/current_a", 10)
        self.power_pub = self.create_publisher(Float32, "/power/ina238/power_w", 10)
        self.temperature_pub = self.create_publisher(Float32, "/power/ina238/temperature_c", 10)
        self.shunt_voltage_pub = self.create_publisher(Float32, "/power/ina238/shunt_voltage_v", 10)
        self.status_pub = self.create_publisher(String, "/power/ina238/status", 10)

        poll_hz = max(0.1, float(self.get_parameter("poll_hz").value))
        self.timer = self.create_timer(1.0 / poll_hz, self._poll)
        self._last_error: Optional[str] = None

    def _publish_float(self, publisher, value: float) -> None:
        msg = Float32()
        msg.data = float(value)
        publisher.publish(msg)

    def _publish_status(self, payload: dict) -> None:
        msg = String()
        msg.data = json.dumps(payload, sort_keys=True)
        self.status_pub.publish(msg)

    def _poll(self) -> None:
        try:
            status = self.reader.read_status()
            self._publish_float(self.bus_voltage_pub, status.bus_voltage_v)
            self._publish_float(self.current_pub, status.current_a)
            self._publish_float(self.power_pub, status.power_w)
            self._publish_float(self.temperature_pub, status.temperature_c)
            self._publish_float(self.shunt_voltage_pub, status.shunt_voltage_v)
            payload = {
                "available": status.available,
                "message": status.message,
                "bus_voltage_v": status.bus_voltage_v,
                "current_a": status.current_a,
                "power_w": status.power_w,
                "temperature_c": status.temperature_c,
                "shunt_voltage_v": status.shunt_voltage_v,
                "config_raw": status.config_raw,
                "adc_config_raw": status.adc_config_raw,
                "shunt_cal_raw": status.shunt_cal_raw,
                "diag_alert_raw": status.diag_alert_raw,
                "manufacturer_id": status.manufacturer_id,
                "device_id": status.device_id,
                "power_raw": status.power_raw,
            }
            self._publish_status(payload)
            if self._last_error is not None:
                self.get_logger().info("INA238 read recovered")
                self._last_error = None
        except Exception as exc:  # pragma: no cover
            message = str(exc)
            payload = {
                "available": False,
                "message": message,
            }
            self._publish_status(payload)
            if message != self._last_error:
                self.get_logger().warning(f"INA238 read failed: {message}")
                self._last_error = message

    def destroy_node(self) -> bool:
        self.reader.close()
        return super().destroy_node()


def main() -> None:
    rclpy.init()
    node = Ina238ReaderNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
