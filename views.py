from flask import Blueprint, request, jsonify
from models import db, User, Conversatie, Mesaj, Alarma, InregistrareSenzor, Alergie, Consultatie, PacientPersonal
from Email import Email
from constants import *
from ResetPasswordCodesManager import ResetPasswordCodesManager
from AlarmType import *
import requests
from sqlalchemy import func, or_
from itertools import permutations

bp = Blueprint('users', __name__, url_prefix='/')

reset_password_codes_manager = ResetPasswordCodesManager()
dummy_user = User(
    id=-1,
    firstName='-1',
    lastName='-1',
    cnp='-1',
    age=-1,
    street='-1',
    city='-1',
    county='-1',
    country='-1',
    phoneNumber='-1',
    emailAddress='-1',
    profession='-1',
    workplace='-1',
    hashed_password='-1',
    accessType='pacient'
)


@bp.route(ROUTS.ADD_USER, methods=['POST'])
def add_user():
    data = request.json
    user_to_insert = User(**data)
    is_user_to_insert_in_db = User.query.filter_by(cnp=user_to_insert.cnp).first()
    if is_user_to_insert_in_db:
        return '', 409
    is_user_to_insert_in_db = User.query.filter_by(emailAddress=user_to_insert.emailAddress).first()
    if is_user_to_insert_in_db:
        return '', 409
    db.session.add(user_to_insert)
    db.session.commit()
    email = Email(user_to_insert.emailAddress, f'Parola dvs. pentru clinica VITALIS este: {user_to_insert.password}')
    print(f'Parola dvs. pentru clinica VITALIS este: {user_to_insert.password}')
    email.send()
    return '', 201


@bp.route(ROUTS.LOGIN, methods=['POST'])
def login_user():
    data = request.json
    cnp = data.get(PARAMETERS.CNP)
    password = data.get(PARAMETERS.PASSWORD)
    user = User.query.filter_by(cnp=cnp).first()
    if user and user.verify_password(password):
        return jsonify(user.serialize()), 200

    return jsonify(dummy_user.serialize()), 200


@bp.route(ROUTS.RESET_PASSWORD_EMAIL, methods=['POST'])
def reset_password_email():
    data = request.json
    email_address = data.get(PARAMETERS.EMAIL_ADDRESS)
    user = User.query.filter_by(emailAddress=email_address).first()
    if not user:
        return '', 404

    reset_password_codes_manager.generate_and_send_reset_code_for_email(email_address)
    return '', 200


@bp.route(ROUTS.CHECK_CONFIRMATION_CODE, methods=['POST'])
def check_confirmation_code():
    data = request.json
    email_address = data.get(PARAMETERS.EMAIL_ADDRESS)
    confirmation_code = data.get(PARAMETERS.CONFIRMATION_CODE)
    if not reset_password_codes_manager.is_reset_code_valid(email_address, confirmation_code):
        return '', 404

    return '', 200


@bp.route(ROUTS.CHANGE_PASSWORD, methods=['POST'])
def change_password():
    data = request.json
    email_address = data.get(PARAMETERS.EMAIL_ADDRESS)
    new_password = data.get(PARAMETERS.NEW_PASSWORD)
    user = User.query.filter_by(emailAddress=email_address).first()
    if not user:
        return '', 404

    user.change_password(new_password)
    db.session.commit()
    return '', 200


@bp.route(ROUTS.GET_MEDICAL_RECORD, methods=['POST'])
def get_medical_record():
    data = request.json
    id = data.get(PARAMETERS.ID)
    user = User.query.filter_by(id=id).first()
    if not user:
        return '', 404
    pacient = user.get_pacient_from_self()
    if not pacient:
        return '', 404
    medical_record = pacient.get_medical_record()
    if not medical_record:
        return '', 404

    examinations = medical_record.get_all_examinations()
    allergies = pacient.get_all_allergies()

    serialized_examinations = [examination.serialize() for examination in examinations]
    serialized_allergies = [allergy.serialize() for allergy in allergies]
    data_to_send = {
        'user': user.serialize(),
        'examinations': serialized_examinations,
        'allergies': serialized_allergies
    }
    return jsonify(data_to_send), 200


@bp.route(ROUTS.ADD_CHAT, methods=['POST'])
def add_chat():
    data = request.json
    this_user_id = data.get(PARAMETERS.ID)
    other_user_id = data.get(PARAMETERS.OTHER_USER_ID)

    existing_chat = Conversatie.query.filter(
        db.or_(
            db.and_(Conversatie.id_user1 == this_user_id, Conversatie.id_user2 == other_user_id),
            db.and_(Conversatie.id_user1 == other_user_id, Conversatie.id_user2 == this_user_id)
        )
    ).first()
    if existing_chat:
        return jsonify(existing_chat.serialize()), 201

    new_chat = Conversatie()
    new_chat.id_user1 = min(this_user_id, other_user_id)
    new_chat.id_user2 = max(this_user_id, other_user_id)
    db.session.add(new_chat)
    db.session.commit()
    return jsonify(new_chat.serialize()), 201


@bp.route(ROUTS.GET_CHAT, methods=['POST'])
def get_chat_request():
    data = request.json
    user_id = data.get(PARAMETERS.ID)
    chat_id = data.get(PARAMETERS.CHAT_ID)
    conversation = Conversatie.query.filter(
        (Conversatie.id == chat_id) &
        ((Conversatie.id_user1 == user_id) | (Conversatie.id_user2 == user_id))
    ).first()
    if not conversation:
        print("NU AM GASIT CONVERSATIE")
        return '', 200
    messages = Mesaj.query.filter_by(id_conversatie=conversation.id).all()
    serialized_messages = [{
        'sendingUserId': message.sendingUserId,
        'content': message.content,
        'sendingDate': message.sendingDate
    } for message in messages]
    other_user_id = conversation.id_user1 if conversation.id_user1 != user_id else conversation.id_user2
    other_user = User.query.get(other_user_id)
    if not other_user:
        print("CU SIGURANTA NU AR TREBUI SA SE INTRE PE AICI VREODATA DAR JUST IN CASE")
        return '', 404
    chat_data = {
        'id': conversation.id,
        'otherUser': {
            'id': other_user.id,
            'firstName': other_user.firstName,
            'lastName': other_user.lastName # posibil sa mai adaugam pe parcurs
        },
        'messages': serialized_messages
    }
    return jsonify(chat_data), 200


@bp.route(ROUTS.GET_CHAT_HISTORY, methods=['POST'])
def get_chat_history():
    data = request.json
    user_id = data.get(PARAMETERS.ID)
    conversations = Conversatie.query.filter(
        ((Conversatie.id_user1 == user_id) | (Conversatie.id_user2 == user_id))
    ).all()
    if not conversations:
        print("NU AM GASIT CONVERSATIE")
        return '', 200
    chat_history = []
    for conversation in conversations:
        messages = Mesaj.query.filter_by(id_conversatie=conversation.id).all()
        if not messages:
            continue
        serialized_message = [{
            'sendingUserId': messages[-1].sendingUserId,
            'content': messages[-1].content,
            'sendingDate': messages[-1].sendingDate
        }]
        other_user_id = conversation.id_user1 if conversation.id_user1 != user_id else conversation.id_user2
        other_user = User.query.get(other_user_id)
        if not other_user:
            print("CU SIGURANTA NU AR TREBUI SA SE INTRE PE AICI VREODATA DAR JUST IN CASE")
            return '', 404
        chat_data = {
            'id': conversation.id,
            'otherUser': {
                'id': other_user.id,
                'firstName': other_user.firstName,
                'lastName': other_user.lastName # posibil sa mai adaugam pe parcurs
            },
            'messages': serialized_message
        }
        chat_history.append(chat_data)
    return jsonify(chat_history), 200


@bp.route(ROUTS.ADD_MESSAGE, methods=['POST'])
def add_message():
    data = request.json
    chat_id = data.get(PARAMETERS.CHAT_ID)
    chat = Conversatie.query.filter_by(id=chat_id).first()
    if not chat:
        print('404')
    message_to_add = data.get(PARAMETERS.MESSAGE_TO_ADD)
    message_to_insert = Mesaj(**message_to_add)
    message_to_insert.id_conversatie = chat_id
    db.session.add(message_to_insert)
    db.session.commit()
    return '', 201


@bp.route(ROUTS.GET_SENSORS_DATA, methods=['POST'])
def get_sensors_data():
    data = request.json
    id = data.get(PARAMETERS.ID)
    number_of_days = data.get(PARAMETERS.NUMBER_OF_DAYS)
    sensors_types_bit_mask = data.get(PARAMETERS.SENSOR_TYPES_BIT_MASK)
    user = User.query.filter_by(id=id).first()
    if not user:
        return '', 404
    pacient = user.get_pacient_from_self()
    if not pacient:
        return '', 404
    sensors_data_list = pacient.get_sensors_data_from_last_days(number_of_days)
    serialized_sensors_data = [sensors_data.serialize(sensors_types_bit_mask) for sensors_data in sensors_data_list]
    return jsonify(serialized_sensors_data), 200


@bp.route(ROUTS.GET_ALARMS, methods=['POST'])
def get_alarms():
    data = request.json
    id = data.get(PARAMETERS.ID)
    user = User.query.filter_by(id=id).first()
    if not user:
        return '', 404
    pacient = user.get_pacient_from_self()
    if not pacient:
        return '', 404
    alarm_list = pacient.get_unresolved_alarms()
    serialized_alarm_list = [alarm.serialize() for alarm in alarm_list]
    return jsonify(serialized_alarm_list), 200


@bp.route(ROUTS.RESOLVE_ALARM, methods=['POST'])
def resolve_alarm():
    data = request.json
    alarm_id = data.get(PARAMETERS.ID)
    is_resolved = data.get(PARAMETERS.IS_RESOLVED)
    alarma = Alarma.query.filter_by(id=alarm_id).first()
    if not alarma:
        return '', 404

    alarma.is_resolved = is_resolved
    db.session.commit()
    return '', 200


@bp.route(ROUTS.GET_PACIENTS, methods=['POST'])
def get_pacients():
    data = request.json
    user_id = data.get(PARAMETERS.ID)
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return '', 404
    personal = user.get_personal_from_self()
    if not personal:
        return '', 404
    pacients_list = personal.get_all_pacients()
    serialized_pacients_list = [pacient.serialize() for pacient in pacients_list]
    return jsonify(serialized_pacients_list), 200


@bp.route(ROUTS.GET_SENSORS_SETTINGS, methods=['POST'])
def get_sensors_settings():
    data = request.json
    user_id = data.get(PARAMETERS.ID)
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return '', 404
    pacient = user.get_pacient_from_self()
    if not pacient:
        return '', 404

    return jsonify(pacient.get_sensors_settings()), 200


@bp.route(ROUTS.UPDATE_SENSORS_SETTINGS, methods=['POST'])
def update_sensors_settings():
    data = request.json
    user_id = data.get(PARAMETERS.ID)
    new_sensors_settings = data.get(PARAMETERS.NEW_SENSOR_SETTINGS)
    user = User.query.filter_by(id=user_id).first()
    if not new_sensors_settings:
        return '', 404
    if not user:
        return '', 404
    pacient = user.get_pacient_from_self()
    if not pacient:
        return '', 404
    if False == pacient.update_sensors_settings(new_sensors_settings):
        return '', 404

    return '', 200


@bp.route(ROUTS.SAVE_SENSORS_DATA, methods=['POST'])
def save_sensors_data():
    data = request.json
    cnp = data.get(PARAMETERS.CNP)
    sensors_data = data.get(PARAMETERS.SENSORS_DATA)
    user = User.query.filter_by(cnp=cnp).first()
    if not user:
        return '', 404
    pacient = user.get_pacient_from_self()
    if not pacient:
        return '', 404
    if 'pulse' in sensors_data and sensors_data['pulse'] == -1:
        sensors_data['pulse'] = None
    sensors_data['id_pacient'] = pacient.id
    sensors_data['date'] = datetime.now()
    sensors_data_to_insert = InregistrareSenzor(**sensors_data)
    db.session.add(sensors_data_to_insert)
    db.session.commit()
    return '', 200


@bp.route(ROUTS.REPORT_ALARM, methods=['POST'])
def report_alarm():
    data = request.json
    cnp = data.get(PARAMETERS.CNP)
    alarm_data = data.get(PARAMETERS.ALARM)
    user = User.query.filter_by(cnp=cnp).first()
    if not user:
        return '', 404
    pacient = user.get_pacient_from_self()
    if not pacient:
        return '', 404
    alarm_data['id_pacient'] = pacient.id
    alarm_data['is_resolved'] = False
    alarm_data['alarm_type'] = AlarmType.get_alarm_type(alarm_data['alarm_type'])
    alarm_to_insert = Alarma(**alarm_data)
    db.session.add(alarm_to_insert)
    db.session.commit()
    return '', 200


@bp.route(ROUTS.ADD_ALLERGY, methods=['POST'])
def add_allergy():
    data = request.json
    user_id = data.get(PARAMETERS.ID)
    allergy_data = data.get(PARAMETERS.ALLERGY)
    allergy_to_insert = Alergie(**allergy_data)
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return '', 404
    pacient = user.get_pacient_from_self()
    if not pacient:
        return '', 404
    db.session.add(allergy_to_insert)
    db.session.commit()
    pacient.allergies.append(allergy_to_insert)
    db.session.commit()
    return '', 200


@bp.route(ROUTS.SEARCH_USER, methods=['POST'])
def search_user():
    data = request.json
    name = data.get(PARAMETERS.NAME)
    if not name:
        return '', 404

    search_terms = name.split()

    if not search_terms:
        return '', 404

    filters = []
    for term in search_terms:
        filters.append(User.firstName.ilike(f"%{term}%"))
        filters.append(User.lastName.ilike(f"%{term}%"))

    if len(search_terms) > 1:
        for perm in permutations(search_terms):
            filters.append(func.concat(User.firstName, ' ', User.lastName).ilike(f"%{' '.join(perm)}%"))
            filters.append(func.concat(User.lastName, ' ', User.firstName).ilike(f"%{' '.join(perm)}%"))

    users = User.query.filter(or_(*filters)).all()

    if not users:
        return '', 404

    users_data = [user.serialize() for user in users]
    return jsonify(users_data), 200


@bp.route(ROUTS.GET_ALL_USERS, methods=['POST'])
def get_all_users():
    data = request.json
    user = User(**data)
    if user.accessType != 'ADMIN':
        return '', 403

    users_list = User.query.all()
    if not users_list:
        return '', 404

    serialized_user_list = [user.serialize() for user in users_list]
    return jsonify(serialized_user_list), 200


@bp.route(ROUTS.ADD_EXAMINATION, methods=['POST'])
def add_examination():
    data = request.json
    id = data.get(PARAMETERS.ID)
    new_examination = data.get(PARAMETERS.EXAMINATION)
    examination_date = new_examination.get(PARAMETERS.EXAMINATION_DATE)
    formatted_examination_date = datetime(examination_date[YEAR_INDEX], examination_date[MONTH_INDEX], examination_date[DAY_INDEX])
    new_examination[PARAMETERS.EXAMINATION_DATE] = formatted_examination_date
    examination_to_add = Consultatie(**new_examination)
    user = User.query.filter_by(id=id).first()
    if not user:
        return '', 404
    pacient = user.get_pacient_from_self()
    if not pacient:
        return '', 404
    medical_record = pacient.get_medical_record()
    if not medical_record:
        return '', 404
    examination_to_add.id_fisa_medicala = medical_record.id
    db.session.add(examination_to_add)
    db.session.commit()

    return '', 200


@bp.route(ROUTS.DELETE_USER, methods=['POST'])
def delete_user():
    data = request.json
    id = data.get(PARAMETERS.ID)
    user = User.query.filter_by(id=id).first()
    if not user:
        return '', 404

    try:
        user.delete()
        return '', 200
    except Exception as e:
        db.session.rollback()
        return '', 500


@bp.route(ROUTS.CHANGE_USER_ACCESS_TYPE, methods=['POST'])
def change_user_access_type():
    data = request.json
    id = data.get(PARAMETERS.ID)
    new_access_type = data.get(PARAMETERS.ACCESS_TYPE)
    user = User.query.filter_by(id=id).first()
    if not user:
        return '', 404

    try:
        user.change_access_type(new_access_type)
        return '', 200
    except Exception as e:
        db.session.rollback()
        return '', 500


@bp.route(ROUTS.ADD_PACIENT_TO_MEDIC, methods=['POST'])
def add_pacient_to_medic():
    data = request.json
    medic_id = data.get(PARAMETERS.ID)
    user_id_of_pacient = data.get(PARAMETERS.PACIENT_ID)
    medic = User.query.filter_by(id=medic_id).first()
    if not medic:
        return '', 404
    user_pacient = User.query.filter_by(id=user_id_of_pacient).first()
    if not user_pacient:
        return '', 404
    personal = medic.get_personal_from_self()
    if not personal:
        return '', 404
    pacient = user_pacient.get_pacient_from_self()
    if not pacient:
        return '', 404
    existing_entry = PacientPersonal.query.filter_by(id_personal=personal.id, id_pacient=pacient.id).first()
    if existing_entry:
        return '', 409

    pacient_personal = PacientPersonal()
    pacient_personal.id_personal = personal.id
    pacient_personal.id_pacient = pacient.id
    db.session.add(pacient_personal)
    db.session.commit()

    return '', 200