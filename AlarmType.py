class AlarmType:
    GAS_DETECTED = 1
    IS_FLOODED = 2
    TEMPERATURE_INCREASE = 3
    UNUSUAL_BODY_PARAMETERS = 4
    SYSTEM_IS_DOWN = 5

    def get_alarm_type(alarm_type):
        if alarm_type == AlarmType.GAS_DETECTED:
            return "GAZ"
        if alarm_type == AlarmType.IS_FLOODED:
            return "INUNDATIE"
        if alarm_type == AlarmType.TEMPERATURE_INCREASE:
            return "CRESTEREA_TEMPERATURII"
        if alarm_type == AlarmType.UNUSUAL_BODY_PARAMETERS:
            return "PARAMETRII_FIZIOLOGICI_ANORMALI"
        if alarm_type == AlarmType.SYSTEM_IS_DOWN:
            return "SISTEM_CAZUT"