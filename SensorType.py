class SensorType:
    BLOOD_PRESSURE = 0x1
    PULSE = 0x2
    BODY_TEMPERATURE = 0x4
    WEIGHT = 0x8
    GLUCOSE = 0x10
    LIGHT = 0x20
    ROOM_TEMPERATURE = 0x40
    IS_GAS_PRESENT = 0x80
    HUMIDITY = 0x100
    IS_IN_PROXIMITY = 0x200

    def extract_sensor_type(bit_mask):
        sensor_types = []
        if bit_mask & SensorType.BLOOD_PRESSURE:
            sensor_types.append('blood_pressure')
        if bit_mask & SensorType.PULSE:
            sensor_types.append('pulse')
        if bit_mask & SensorType.BODY_TEMPERATURE:
            sensor_types.append('body_temperature')
        if bit_mask & SensorType.WEIGHT:
            sensor_types.append('weight')
        if bit_mask & SensorType.GLUCOSE:
            sensor_types.append('glucose')
        if bit_mask & SensorType.LIGHT:
            sensor_types.append('light')
        if bit_mask & SensorType.ROOM_TEMPERATURE:
            sensor_types.append('room_temperature')
        if bit_mask & SensorType.IS_GAS_PRESENT:
            sensor_types.append('is_gas_present')
        if bit_mask & SensorType.HUMIDITY:
            sensor_types.append('humidity')
        if bit_mask & SensorType.IS_IN_PROXIMITY:
            sensor_types.append('is_in_proximity')

        return sensor_types