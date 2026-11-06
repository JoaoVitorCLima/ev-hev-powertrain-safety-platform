"""Illustrative 8-byte virtual CAN payload layouts, *not* OEM frames or authenticated CAN.
Project-defined signal scaling and IDs. They can be exported as a synthetic DBC.
"""
import struct
BMS_STATUS_ID = 0x180
VCU_TORQUE_ID = 0x200

def encode_bms(soc_pct: float, temp_c: float, counter: int) -> bytes:
    return struct.pack('<HhBxxx', round(soc_pct * 10), round(temp_c * 10), counter & 0x0F)

def decode_bms(payload: bytes) -> dict:
    if len(payload) != 8:
        raise ValueError('BMS payload must have 8 bytes')
    soc, temp, counter = struct.unpack('<HhBxxx', payload)
    return {'soc_pct': soc / 10, 'battery_temp_c': temp / 10, 'can_counter': counter}

def encode_torque(torque_nm: float) -> bytes:
    if not (-3276.8 <= torque_nm <= 3276.7): raise ValueError('torque out of range')
    return struct.pack('<hxxxxxx', round(torque_nm * 10))

def decode_torque(payload: bytes) -> float:
    if len(payload) != 8: raise ValueError('VCU payload must have 8 bytes')
    return struct.unpack('<hxxxxxx',payload)[0]/10.0
