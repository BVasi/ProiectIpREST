from datetime import datetime

#to change with real data:

SERVICE_ACCOUNT_FILE = 'json_email.json'
EMAIL = 'Email'
ADMIN_EMAIL = 'user_name_email@gmail.com'
ADMIN_PASSWORD = 'parola_email'
EMAIL_SUBJECT = f'Parola VITALIS'
FROM = 'From'
TO = 'To'
SUBJECT = 'Subject'
PLAIN = 'plain'
GMAIL_SERVER = 'smtp.gmail.com'
PORT = 587
NEXT_INDEX = 1
YEAR_INDEX = 0
MONTH_INDEX = 1
DAY_INDEX = 2


class ROUTS:
    ADD_USER = "/add_user"
    LOGIN = "/login"
    CHANGE_PASSWORD = "/change_password"
    RESET_PASSWORD_EMAIL = "/reset_password_email"
    CHECK_CONFIRMATION_CODE = "/check_confirmation_code"
    GET_MEDICAL_RECORD = "/get_medical_record"
    ADD_CHAT = "/add_chat"
    GET_CHAT = "/get_chat"
    GET_CHAT_HISTORY = "/get_chat_history"
    ADD_MESSAGE = "/add_message"
    GET_SENSORS_DATA = "/get_sensors_data"
    GET_ALARMS = "/get_alarms"
    RESOLVE_ALARM = "/resolve_alarm"
    GET_PACIENTS = "/get_pacients"
    GET_SENSORS_SETTINGS = "/get_sensors_settings"
    UPDATE_SENSORS_SETTINGS = "/update_sensors_settings"
    SAVE_SENSORS_DATA = "/save_sensors_data"
    REPORT_ALARM = "/report_alarm"
    ADD_ALLERGY = "/add_allergy"
    SEARCH_USER = "/search_user"
    GET_ALL_USERS = "/get_all_users"
    ADD_EXAMINATION = "/add_examination"
    DELETE_USER = "/delete_user"
    CHANGE_USER_ACCESS_TYPE = "/change_user_access_type"
    ADD_PACIENT_TO_MEDIC = "/add_pacient_to_medic"


class PARAMETERS:
    ID = "id"
    CNP = "cnp"
    PASSWORD = "password"
    EMAIL_ADDRESS = "emailAddress"
    NEW_PASSWORD = "newPassword"
    CONFIRMATION_CODE = "confirmationCode"
    CHAT_ID = "chatId"
    MESSAGE_TO_ADD = "messageToAdd"
    NUMBER_OF_DAYS = "numberOfDays"
    SENSOR_TYPES_BIT_MASK = "sensorTypesBitMask"
    IS_RESOLVED = "isResolved"
    NEW_SENSOR_SETTINGS = "newSensorSettings"
    SENSORS_DATA = "sensorsData"
    ALARM = "alarm"
    ALLERGY = "allergy"
    NAME = "name"
    OTHER_USER_ID = "otherUserId"
    EXAMINATION = "examination"
    EXAMINATION_DATE = "examinationDate"
    ACCESS_TYPE = "accessType"
    PACIENT_ID = "pacientId"