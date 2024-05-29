from flask_sqlalchemy import SQLAlchemy
from RandomStringGenerator import RandomStringGenerator
import hashlib
from datetime import datetime, timedelta
from SensorType import *

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(100), name='nume')
    lastName = db.Column(db.String(100), name='prenume')
    cnp = db.Column(db.String(13), name='CNP')
    age = db.Column(db.Integer, name='varsta')
    street = db.Column(db.String(100), name='strada')
    city = db.Column(db.String(50), name='oras')
    county = db.Column(db.String(50), name='judet')
    country = db.Column(db.String(50), name='tara')
    phoneNumber = db.Column(db.String(15), name='numar_telefon')
    emailAddress = db.Column(db.String(100), name='adresa_email')
    profession = db.Column(db.String(100), name='profesie')
    workplace = db.Column(db.String(100), name='loc_munca')
    accessType = db.Column(db.String(50), name='tip_acces')
    hashed_password = db.Column(db.String(64), name='parola')
    password = ""


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.hashed_password:
            passwordGenerator = RandomStringGenerator()
            self.password = passwordGenerator.generate_random_string()
            hasher = hashlib.sha256()
            hasher.update(self.password.encode('utf-8'))
            self.hashed_password = hasher.hexdigest()


    def serialize(self):
        return {
            'id': self.id,
            'firstName': self.firstName,
            'lastName': self.lastName,
            'cnp': self.cnp,
            'age': self.age,
            'street': self.street,
            'city': self.city,
            'county': self.county,
            'country': self.country,
            'phoneNumber': self.phoneNumber,
            'emailAddress': self.emailAddress,
            'profession': self.profession,
            'workplace': self.workplace,
            'password': self.hashed_password,
            'accessType': self.accessType.upper()
        }


    def verify_password(self, password):
        hasher = hashlib.sha256()
        hasher.update(password.encode('utf-8'))
        hashed_password = hasher.hexdigest()
        return hashed_password == self.hashed_password


    def change_password(self, new_password):
        self.password = new_password
        hasher = hashlib.sha256()
        hasher.update(self.password.encode('utf-8'))
        self.hashed_password = hasher.hexdigest()


    def get_pacient_from_self(self):
        return Pacient.query.filter_by(id_user=self.id).first()


    def get_personal_from_self(self):
        return Personal.query.filter_by(id_user=self.id).first()


    def change_access_type(self, new_access_type):
        if self.accessType.upper() == "PACIENT":
            return
        if new_access_type.upper() != "ADMIN":
            Administrator.query.filter_by(id_user=self.id).delete()
            self.accessType = new_access_type
        if new_access_type.upper() == "ADMIN":
            personal = self.get_personal_from_self()
            PacientPersonal.query.filter_by(id_personal=personal.id).delete()
            administrator = Administrator()
            administrator.id_user = self.id
            db.session.add(administrator)

        db.session.commit()


    def delete(self):
        if self.accessType.upper() == "PACIENT":
            pacient = self.get_pacient_from_self()
            medical_record = pacient.get_medical_record()
            if medical_record:
                examinations = medical_record.get_all_examinations()
                for examination in examinations:
                    db.session.delete(examination)
                db.session.delete(medical_record)
            Alarma.query.filter_by(id_pacient=pacient.id).delete()
            InregistrareSenzor.query.filter_by(id_pacient=pacient.id).delete()
            ReferintaSenzor.query.filter_by(id_pacient=pacient.id).delete()
            SetariSenzori.query.filter_by(id_pacient=pacient.id).delete()
            PacientPersonal.query.filter_by(id_pacient=pacient.id).delete()
            PacientAlergie.query.filter_by(id_pacient=pacient.id).delete()
            db.session.delete(pacient)
        elif self.accessType.upper() == "ADMIN":
            Administrator.query.filter_by(id_user=self.id).delete()
        else:
            personal = self.get_personal_from_self()
            PacientPersonal.query.filter_by(id_personal=personal.id).delete()

        conversations = Conversatie.query.filter(
            (Conversatie.id_user1 == self.id) | (Conversatie.id_user2 == self.id)
        ).all()
        for conversation in conversations:
            Mesaj.query.filter_by(id_conversatie=conversation.id).delete()
            db.session.delete(conversation)

        db.session.delete(self)
        db.session.commit()


class Pacient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'), name='id_user')
    allergies = db.relationship('Alergie', secondary='pacient_alergie', backref=db.backref('pacients', lazy='dynamic', cascade='all, delete'))


    def get_medical_record(self):
        return FisaMedicala.query.filter_by(id_pacient=self.id).first()


    def get_sensors_data_from_last_days(self, number_of_days=1):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=number_of_days)

        return InregistrareSenzor.query.filter_by(id_pacient=self.id)\
                                    .filter(InregistrareSenzor.date.between(start_date, end_date))\
                                    .order_by(InregistrareSenzor.date.desc())\
                                    .all()


    def get_unresolved_alarms(self):
        return Alarma.query.filter_by(id_pacient=self.id, is_resolved=False).all()


    def get_sensors_settings(self):
        return {
            'sensorsReferences': ReferintaSenzor.query.filter_by(id_pacient=self.id).first().serialize(),
            'samplingPeriod': SetariSenzori.query.filter_by(id_pacient=self.id).first().sampling_period.upper()
        }


    def update_sensors_settings(self, new_sensor_settings):
        sensors_references = ReferintaSenzor.query.filter_by(id_pacient=self.id).first()
        sensors_settings = SetariSenzori.query.filter_by(id_pacient=self.id).first()

        if sensors_references and sensors_settings:
            sensors_settings.sampling_period = new_sensor_settings['samplingPeriod']
            sensors_references.minimum_blood_pressure = new_sensor_settings['sensorsReferences']['minimumBloodPressure']
            sensors_references.maximum_blood_pressure = new_sensor_settings['sensorsReferences']['maximumBloodPressure']
            sensors_references.minimum_pulse = new_sensor_settings['sensorsReferences']['minimumPulse']
            sensors_references.maximum_pulse = new_sensor_settings['sensorsReferences']['maximumPulse']
            sensors_references.minimum_body_temperature = new_sensor_settings['sensorsReferences']['minimumBodyTemperature']
            sensors_references.maximum_body_temperature = new_sensor_settings['sensorsReferences']['maximumBodyTemperature']
            sensors_references.minimum_weight = new_sensor_settings['sensorsReferences']['minimumWeight']
            sensors_references.maximum_weight = new_sensor_settings['sensorsReferences']['maximumWeight']
            sensors_references.minimum_glucose = new_sensor_settings['sensorsReferences']['minimumGlucose']
            sensors_references.maximum_glucose = new_sensor_settings['sensorsReferences']['maximumGlucose']
            sensors_references.minimum_room_temperature = new_sensor_settings['sensorsReferences']['minimumRoomTemperature']
            sensors_references.maximum_room_temperature = new_sensor_settings['sensorsReferences']['maximumRoomTemperature']
            db.session.commit()
            return True

        return False


    def get_all_allergies(self):
        return self.allergies


    def serialize(self):
        return User.query.filter_by(id=self.id_user).first().serialize()


class FisaMedicala(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_pacient = db.Column(db.Integer, db.ForeignKey('pacient.id'), name='id_pacient')


    def get_all_examinations(self):
        return Consultatie.query.filter_by(id_fisa_medicala=self.id).all()


class Consultatie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_fisa_medicala = db.Column(db.Integer, db.ForeignKey('fisa_medicala.id'), name='id_fisa_medicala')
    examinationDate = db.Column(db.DateTime, name='data')
    diagnostic = db.Column(db.Text, name='diagnostic')
    cure = db.Column(db.Text, name='tratament')
    recomandation = db.Column(db.Text, name='recomandare')

    def serialize(self):
        return {
            'examinationDate': self.examinationDate,
            'diagnostic': self.diagnostic,
            'cure': self.cure,
            'recomandation': self.recomandation
        }


class Conversatie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_user1 = db.Column(db.Integer, db.ForeignKey('user.id'), name='iduser1')
    id_user2 = db.Column(db.Integer, db.ForeignKey('user.id'), name='iduser2')

    def serialize(self):
        return {
            'id': self.id
        }


class Mesaj(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_conversatie = db.Column(db.Integer, db.ForeignKey('conversatie.id'), name='idConversatie')
    sendingUserId = db.Column(db.Integer, db.ForeignKey('user.id'), name='idSendingUser')
    content = db.Column(db.Text, name='continut')
    sendingDate = db.Column(db.DateTime, name='data')


class InregistrareSenzor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_pacient = db.Column(db.Integer, db.ForeignKey('pacient.id'), name='id_pacient')
    date = db.Column(db.DateTime, name='data')
    blood_pressure = db.Column(db.Integer, name='tensiune_arteriala')
    pulse = db.Column(db.Integer, name='puls')
    body_temperature = db.Column(db.Integer, name='temperatura_corporala')
    weight = db.Column(db.Float, name='greutate')
    glucose = db.Column(db.Integer, name='glicemie')
    light = db.Column(db.Boolean, name='lumina')
    room_temperature = db.Column(db.Integer, name='temperatura_ambientala')
    is_gas_present = db.Column(db.Boolean, name='prezenta_gaz')
    humidity = db.Column(db.Boolean, name='umiditate')
    is_in_proximity = db.Column(db.Boolean, name='proximitate')

    def serialize(self, bit_mask):
        serialized_data = {'date': self.date}
        sensor_types = SensorType.extract_sensor_type(bit_mask)

        for sensor_type in sensor_types:
            serialized_data[sensor_type] = getattr(self, sensor_type)

        return serialized_data


class Alarma(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_pacient = db.Column(db.Integer, db.ForeignKey('pacient.id'), name='id_pacient')
    is_resolved = db.Column(db.Boolean, name='e_rezolvata')
    additional_text = db.Column(db.Text, name='text_aditional')
    alarm_type = db.Column(db.String(29), name='tip_alarma')

    def serialize(self):
        return {
            'id': self.id,
            'userId': self.id_pacient,
            'isResolved': self.is_resolved,
            'additionalText': self.additional_text,
            'alarmType': self.alarm_type.upper()
        }


class Personal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'), name='id_user')
    pacients = db.relationship('Pacient', secondary='pacient_personal', backref=db.backref('personals', lazy='dynamic'))

    def get_all_pacients(self):
        return self.pacients


class PacientPersonal(db.Model):
    __tablename__ = 'pacient_personal'
    id_personal = db.Column(db.Integer, db.ForeignKey('personal.id'), primary_key=True)
    id_pacient = db.Column(db.Integer, db.ForeignKey('pacient.id'), primary_key=True)


class Alergie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), name='nume_alergie')


    def serialize(self):
        return {
            'name': self.name
        }


class PacientAlergie(db.Model):
    __tablename__ = 'pacient_alergie'
    id_pacient = db.Column(db.Integer, db.ForeignKey('pacient.id'), primary_key=True)
    id_alergie = db.Column(db.Integer, db.ForeignKey('alergie.id'), primary_key=True)


class ReferintaSenzor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_pacient = db.Column(db.Integer, db.ForeignKey('pacient.id'), name='id_pacient')
    minimum_blood_pressure = db.Column(db.Integer, name='minim_tensiune_arteriala')
    maximum_blood_pressure = db.Column(db.Integer, name='maxim_tensiune_arteriala')
    minimum_pulse = db.Column(db.Integer, name='minim_puls')
    maximum_pulse = db.Column(db.Integer, name='maxim_puls')
    minimum_body_temperature = db.Column(db.Integer, name='minim_temperatura_corporala')
    maximum_body_temperature = db.Column(db.Integer, name='maxim_temperatura_corporala')
    minimum_weight = db.Column(db.Integer, name='minim_greutate')
    maximum_weight = db.Column(db.Integer, name='maxim_greutate')
    minimum_glucose = db.Column(db.Integer, name='minim_glicemie')
    maximum_glucose = db.Column(db.Integer, name='maxim_glicemie')
    minimum_room_temperature = db.Column(db.Integer, name='minim_temperatura_ambientala')
    maximum_room_temperature = db.Column(db.Integer, name='maxim_temperatura_ambientala')


    def serialize(self):
        return {
            'minimumBloodPressure': self.minimum_blood_pressure,
            'maximumBloodPressure': self.maximum_blood_pressure,
            'minimumPulse': self.minimum_pulse,
            'maximumPulse': self.maximum_pulse,
            'minimumBodyTemperature': self.minimum_body_temperature,
            'maximumBodyTemperature': self.maximum_body_temperature,
            'minimumWeight': self.minimum_weight,
            'maximumWeight': self.maximum_weight,
            'minimumGlucose': self.minimum_glucose,
            'maximumGlucose': self.maximum_glucose,
            'minimumRoomTemperature': self.minimum_room_temperature,
            'maximumRoomTemperature': self.maximum_room_temperature
        }


class SetariSenzori(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_pacient = db.Column(db.Integer, db.ForeignKey('pacient.id'), name='id_pacient')
    sampling_period = db.Column(db.String(13), name='perioada_esantionare')


class Administrator(db.Model):
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)