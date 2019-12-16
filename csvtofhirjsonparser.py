"""
CSV to FHIR JSON python script
"""
import csv
from datetime import datetime
import random
import uuid
from io import StringIO
import pytz
import werkzeug
from flask import Flask
from flask_restplus import Resource, Api, Namespace, reqparse
from fhir.resources.bundle import Bundle
from fhir.resources.patient import Patient
from fhir.resources.address import Address
from fhir.resources.humanname import HumanName
from fhir.resources.fhirreference import FHIRReference
from fhir.resources.identifier import Identifier
from fhir.resources.composition import Composition
from fhir.resources.practitioner import Practitioner
from fhir.resources.practitioner import PractitionerQualification
from fhir.resources.observation import Observation
from fhir.resources.bundle import BundleEntry
from fhir.resources.composition import CompositionSection
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.reference import Reference
from fhir.resources.coding import Coding
from fhir.resources.extension import Extension
from fhir.resources.parameterdefinition import ParameterDefinition
from fhir.resources.condition import Condition
from fhir.resources.narrative import Narrative
from fhir.resources.composition import CompositionEvent
from fhir.resources.composition import CompositionAttester


# app defaults
VERSION = '1.0'
TITLE = 'FHIR JSON Generator'
DESCRIPTION = ('This API accepts csv file will return a bundle json object.')
APP = Flask(__name__)

# api defaults
API = Api(
    app=APP,
    version=VERSION,
    title=TITLE,
    description=DESCRIPTION,
    doc='/swagger-ui.html'
)

API.namespaces.pop(0)
NS = Namespace('entity', description='FHIR JSON Generator')
API.add_namespace(NS)

# csv file upload
FILE_UPLOAD = reqparse.RequestParser()
FILE_UPLOAD.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')

# patient-decedent structure definitions array
PATIENT_DECEDENT_SD = {
    "sdr-decedent-Age-extension": "http://nightingaleproject.github.io/fhirDeathRecord/"
                                  "StructureDefinition/sdr-decedent-Age-extension",
    "sdr-decedent-Birthplace-extension": "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"
                                         "sdr-decedent-Birthplace-extension",
    "sdr-decedent-Disposition-extension": "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"
                                          "sdr-decedent-Disposition-extension",
    "sdr-decedent-DispositionFacility-extension": "http://nightingaleproject.github.io/fhirDeathRecord/"
                                                  "StructureDefinition/sdr-decedent-DispositionFacility-extension",
    "sdr-decedent-DispositionType-extension": "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"
                                              "sdr-decedent-DispositionType-extension",
    "sdr-decedent-Education-extension": "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"
                                        "sdr-decedent-Education-extension",
    "sdr-decedent-FacilityName-extension": "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"
                                           "sdr-decedent-FacilityName-extension",
    "sdr-decedent-FuneralFacility-extension": "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"
                                              "sdr-decedent-FuneralFacility-extension",
    "sdr-decedent-Industry-extension": "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"
                                       "sdr-decedent-Industry-extension",
    "sdr-decedent-Job-extension": "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"
                                  "sdr-decedent-Job-extension",
    "sdr-decedent-MaritalStatusAtDeath-extension": "http://nightingaleproject.github.io/fhirDeathRecord/"
                                                   "StructureDefinition/sdr-decedent-MaritalStatusAtDeath-extension",
    "sdr-decedent-Occupation-extension": "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"
                                         "sdr-decedent-Occupation-extension",
    "sdr-decedent-PlaceOfDeath-extension": "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"
                                           "sdr-decedent-PlaceOfDeath-extension",
    "sdr-decedent-PlaceOfDeathType-extension": "http://nightingaleproject.github.io/fhirDeathRecord/"
                                               "StructureDefinition/sdr-decedent-PlaceOfDeathType-extension",
    "sdr-decedent-ServerInArmedForces-extension": "http://nightingaleproject.github.io/fhirDeathRecord/"
                                                  "StructureDefinition/sdr-decedent-ServerInArmedForces-extension",
    "sdr-decedent-SocialSecurityNumber-extension": "http://nightingaleproject.github.io/fhirDeathRecord/"
                                                   "StructureDefinition/sdr-decedent-SocialSecurityNumber-extension",
    "sdr-decedent-Decedent-extension": "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"
                                       "sdr-decedent-Decedent-extension",
    "sdr-decedent-DecedentID-extension": "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"
                                         "sdr-decedent-DecedentID-extension"
}
# patient address types
PATIENT_ADDRESS_SD = []
PATIENT_ADDRESS_SD.append(
    "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/shr-core-InsideCityLimits-extension")
PATIENT_ADDRESS_SD.append(
    "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/shr-core-PostalAddress")
PATIENT_ADDRESS_SD.append(
    "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/shr-core-PostalAddress-extension")

# Resource type observation from the certificate(Meta profile information)
OBSERVATION_SD = {
    "sdr-causeOfDeath-CauseOfDeathCondition":
        "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"
        "sdr-causeOfDeath-CauseOfDeathCondition",
    "sdr-causeOfDeath-ContributeToDeathCondition":
        "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"
        "sdr-causeOfDeath-ContributeToDeathCondition",
    "sdr-causeOfDeath-DatePronoucedDead":
        "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/sdr-causeOfDeath-DatePronoucedDead",
    "sdr-causeOfDeath-DeathFromTransportInjury":
        "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"
        "sdr-causeOfDeath-DeathFromTransportInjury",
    "sdr-causeOfDeath-DeathFromWorkInjury":
        "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/sdr-causeOfDeath-DeathFromWorkInjury",
    "sdr-causeOfDeath-DetailsOfInjury":
        "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/sdr-causeOfDeath-DetailsOfInjury",
    "sdr-causeOfDeath-MannerOfDeath":
        "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"
        "sdr-causeOfDeath-MannerOfDeath",
    "sdr-causeOfDeath-MedicalExaminerContacted":
        "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"
        "sdr-causeOfDeath-MedicalExaminerContacted",
    "sdr-causeOfDeath-PlaceOfInjury-extention":
        "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"
        "sdr-causeOfDeath-PlaceOfInjury-extention",
    # check once
    "sdr-causeOfDeath-TimingOfRecentPregnancyInRelationToDeath":
        "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/sdr-causeOfDeath-TimingOfRecentPregnan"
        "cyInRelationToDeath",
    "sdr-causeOfDeath-TobaccoUseContributedToDeath":
        "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"
        "sdr-causeOfDeath-TobaccoUseContributedToDeath",
    "sdr-causeOfDeath-ActualOrPresumedDateOfDeath":
        "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"
        "sdr-causeOfDeath-ActualOrPresumedDateOfDeath",
    "sdr-causeOfDeath-AutopsyPerformed":
        "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/sdr-causeOfDeath-AutopsyPerformed",
    "sdr-causeOfDeath-AutopsyResultsAvailable":
        "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"
        "sdr-causeOfDeath-AutopsyResultsAvailable"
}
# composition meta-profile
COMPOSITION_SD = []
COMPOSITION_SD.append(
    "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/sdr-deathRecord-DeathRecordContents")

# practitioner extention data
PRACTITIONER_SD = {
    "sdr-deathRecord-CertifierType-extension":
        "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"
        "sdr-deathRecord-CertifierType-extension"
}

# practitioner's education codes and display items
PRACTITIONER_EDU_CODES = {
    "MA": "Master of Arts",
    "MBA": "Master of Business Administration",
    "MCE": "Master of Civil Engineering",
    "MD": "Doctor of Medicine",
    "MDA": "Medical Assistant",
    "MDI": "Master of Divinity",
    "ME": "Master of Engineering",
    "MED": "Master of Education",
    "MEE": "Master of Electrical Engineering",
    "MFA": "Master of Fine Arts",
    "MME": "Master of Mechanical Engineering",
    "MS": "Master of Science",
    "MSL": "Master of Science - Law",
    "MSN": "Master of Science - Nursing",
    "MT": "Medical Technician",
    "MTH": "Master of Theology",
    "NG": "Non-Graduate",
    "NP": "Nurse Practitioner",
    "PA": "Physician Assistant",
    "PHD": "Doctor of Philosophy",
    "PHE": "Doctor of Engineering",
    "PHS": "Doctor of Science",
    "PN": "Advanced Practice Nurse",
    "PharmD": "Doctor of Pharmacy",
    "RMA": "Registered Medical Assistant",
    "RN": "Registered Nurse",
    "RPH": "Registered Pharmacist",
    "SEC": "Secretarial Certificate",
    "TS": "Trade School Graduate",
    "AA": "Associate of Arts",
    "AAS": "Associate of Applied Science",
    "ABA": "Associate of Business Administration",
    "AE": "Associate of Engineering",
    "AS": "Associate of Science",
    "BA": "Bachelor of Arts",
    "BBA": "Bachelor of Business Administration",
    "BE": "Bachelor or Engineering",
    "BFA": "Bachelor of Fine Arts",
    "BN": "Bachelor of Nursing",
    "BS": "Bachelor of Science",
    "BSL": "Bachelor of Science - Law",
    "BSN": "Bachelor on Science - Nursing",
    "BT": "Bachelor of Theology",
    "CANP": "Certified Adult Nurse Practitioner",
    "CER": "Certificate",
    "CMA": "Certified Medical Assistant",
    "CNM": "Certified Nurse Midwife",
    "CNP": "Certified Nurse Practitioner",
    "CNS": "Certified Nurse Specialist",
    "CPNP": "Certified Pediatric Nurse Practitioner",
    "CRN": "Certified Registered Nurse",
    "CTR": "Certified Tumor Registrar",
    "DBA": "Doctor of Business Administration",
    "DED": "Doctor of Education",
    "DIP": "Diploma",
    "DO": "Doctor of Osteopathy",
    "EMT": "Emergency Medical Technician",
    "EMTP": "Emergency Medical Technician - Paramedic",
    "FPNP": "Family Practice Nurse Practitioner",
    "HS": "High School Graduate",
    "JD": "Juris Doctor"
}


# methods to load data from PDF

def generate_uuid():
    """
    This functions generates uuid's for all the profiles we need to generate bundle object
    :return: returns a dictionary
    """
    uuid_dict = {}
    uuid_dict['Patient'] = "urn:uuid:" + str(uuid.uuid4())
    uuid_dict['Practitioner'] = "urn:uuid:" + str(uuid.uuid4())
    uuid_dict['Composition'] = "urn:uuid:" + str(uuid.uuid4())
    uuid_dict['CompositionEvent'] = "urn:uuid" + str(uuid.uuid4())
    for i in range(1, len(OBSERVATION_SD), 1):
        uuid_dict["Observation" + str(i)] = "urn:uuid:" + str(uuid.uuid4())

    return uuid_dict


# This method generates composition data randomly. No fields from CSV or PDF are populated. Assumed that this parser is
# for Death Certificates.
# not from PDF randomly generate the ids

def load_composition_data(uuiddict):
    """
    This funtion generates composition json object
    :param uuiddict: this data structure holds uuids
    :return: returns composition json object
    """
    composition = Composition()
    authorreference = FHIRReference()
    authorreference.reference = uuiddict['Practitioner']
    # author : reference would be of practitioner
    composition.author = []
    composition.author.append(del_none(authorreference.__dict__))

    # id
    composition.id = uuiddict['Practitioner']

    # meta
    meta_profile_data = ParameterDefinition()
    meta_profile_data.profile = []
    meta_profile_data.profile.append(COMPOSITION_SD[0])
    composition.meta = del_none(meta_profile_data.__dict__)

    # date
    # this should be populated from the certificate/when the json object was created
    composition.date = datetime.now(tz=pytz.utc).strftime(
        '%Y-%m-%dT%H:%M:%S.%f%z')  # from pdf - current date time would also work

    # section
    section_data = []  # array
    section_data_item = CompositionSection()

    section_codeable_concept_item = CodeableConcept()

    section_coding_item = Coding()
    section_coding_item.code = "69453-9"
    section_coding_item.system = "http://loinc.org"

    section_codeable_concept_item.coding = del_none(section_coding_item.__dict__)

    section_data_item.code = del_none(section_codeable_concept_item.__dict__)

    section_entry_ref_array = []

    for item in uuiddict:
        if item != 'Composition':
            ref = Reference()
            ref.reference = uuiddict[item]
            section_entry_ref_array.append(del_none(ref.__dict__))

    section_data_item.entry = section_entry_ref_array

    section_data.append(del_none(section_data_item.__dict__))
    composition.section = section_data

    # status
    composition.status = "final"

    # title
    composition.title = "Record of Death"

    # subject
    composition.subject = []
    subject_ref = Reference()
    subject_ref.reference = uuiddict['Patient']
    composition.subject.append(del_none(subject_ref.__dict__))

    # type
    type_coding = []
    type_coding_arr_value = CodeableConcept()

    type_coding_arr_value.coding = []
    # add code and system value for death certificate
    coding_arr_value = Coding()
    coding_arr_value.code = "64297-5"
    coding_arr_value.system = "http://loinc.org"

    type_coding_arr_value.coding.append(del_none(coding_arr_value.__dict__))

    type_coding.append(del_none(type_coding_arr_value.__dict__))
    composition.type = type_coding

    composition.__dict__['resourceType'] = "Composition"

    # event
    eventcoding = Coding()
    eventcoding.code = "103693007"
    eventcoding.display = "Diagnostic procedure"
    eventcoding.system = "http://snomed.info/sct"

    event_code = CodeableConcept()
    event_code.coding = []
    event_code.coding.append(del_none(eventcoding.__dict__))

    composition.event = []

    compositionevent = CompositionEvent()
    compositionevent.code = del_none(eventcoding.__dict__)
    compositionevent.detail = []
    reference = Reference()
    reference.reference = uuiddict['CompositionEvent']
    compositionevent.detail.append(del_none(reference.__dict__))

    composition.event.append(del_none(compositionevent.__dict__))

    # attester
    composition.attester = []
    compositionattester = CompositionAttester()
    compositionattester.mode = []
    compositionattester.mode.append("legal")
    compositionattester.party = uuiddict["Practitioner"]
    compositionattester.time = datetime.now(tz=pytz.utc).strftime(
        '%Y-%m-%dT%H:%M:%S.%f%z')  # from CSV PDF file when the certifier approved
    composition.attester.append(del_none(compositionattester.__dict__))

    return composition

# patient - decedent data
def load_patient_data(uuid_dict, csvjsonobject):
    """
    This function returns loads patient's data in json data
    :param uuid_dict: this data structure holds uuid's generated
    :param csvjsonobject: this data structure holds csv json object from CSV file
    :return: returns patient data json object
    """
    patient = Patient()

    # address
    address = []
    address_item = Address()  # from pdf
    address_item.city = csvjsonobject['PATIENTS_ADDRESS_CITY']  # from pdf  - patient's city
    address_item.country = csvjsonobject['PATIENTS_ADDRESS_COUNTRY']  # from pdf - patient's country
    address_item.district = csvjsonobject['PATIENTS_ADDRESS_DISTRICT']  # from pdf - patient's district
    address_item.state = csvjsonobject['PATIENTS_ADDRESS_STATE']  # from pdf - patient's state
    address_item.use = "official"  # from pdf - patient's address use
    address_item.line = []
    address_item.line.append(csvjsonobject['PATIENTS_ADDRESS_LINE'])  # from pdf - patient's address line

    address_extention = Extension()
    address_extention.url = PATIENT_ADDRESS_SD[0]
    address_extention.valueBoolean = True


    address_item.extension = del_none(address_extention.__dict__)
    address.append(del_none(address_item.__dict__))
    patient.address = address

    # birthDate
    patient.birthDate = datetime.now(tz=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f%z')  # birthDate from PDF

    # deceased Date Time
    patient.deceasedDateTime = datetime.now(tz=pytz.utc).strftime(
        '%Y-%m-%dT%H:%M:%S.%f%z')  # deceased Date and Time from PDF

    # deceased Boolean Value
    patient.deceasedBoolean = True

    # gender from PDF
    patient.gender = csvjsonobject['PATIENT_GENDER_ATTIMEOFDEATH']  # from pdf - patient's birth sex/gender

    # id - identifier
    patient.id = uuid_dict['Patient']

    # identifier for verification of Patient line SSN or any other document
    patient_identifier_array = []
    patient_identifier = Identifier()

    patient_identifier.system = "http://hl7.org/fhir/sid/us-ssn"  # assumed its SSN
    patient_identifier.value = random.randint(100000000, 999999999)

    patient_identifier_array.append(del_none(patient_identifier.__dict__))
    patient.identifier = patient_identifier_array

    # patient Name from PDF
    patient_name = HumanName()
    patient_name.given = [csvjsonobject['PATIENTS_GIVENNAME']]  # from pdf - patient's given name
    patient_name.family = csvjsonobject['PATIENTS_FAMILYNAME']  # from pdf - patient's family name
    patient_name.use = "official"

    patient.name = del_none(patient_name.__dict__)

    # patient extensions
    patient.extension = loadpatientextensions(csvjsonobject)

    patient.__dict__['resourceType'] = 'Patient'
    return patient

def patientseducation(string):
    """
    This function returns code value for the passed string. This function is specific to patient's education
    :param str: patient's education string value from CSV
    :return: code value for patient's education
    """
    code = "UNK"

    if "8th grade or less".upper() in string.upper():
        code = "PHC1448"

    if ("9th through 12th grade".upper() in string.upper()) or ("no diploma".upper() in string.upper()):
        code = "PHC1449"

    if "High School Graduate or GED Completed".upper() in string.upper():
        code = "PHC1450"

    if "Some college credit, but no degree".upper() in string.upper():
        code = "PHC1451"

    if "Associate Degree".upper() in string.upper():
        code = "PHC1452"

    if "Bachelor's Degree".upper() in string.upper():
        code = "PHC1453"

    if "Master's Degree".upper() in string.upper():
        code = "PHC1454"

    if "Doctorate Degree or Professional Degree".upper() in string.upper():
        code = "PHC1455"

    return code


def dispositiontype(string):
    """
    This function returns the code as per the standards for disposition type
    :param string: this value is read from csv file
    :return: code as per the standards
    """
    code = "UNK"

    if "Other".upper() in string.upper():
        code = "OTH"

    if "Donation".upper() in string.upper():
        code = "449951000124101"

    if "Burial".upper() in string.upper():
        code = "449971000124106"

    if "Cremation".upper() in string.upper():
        code = "449961000124104"

    if "Entombment".upper() in string.upper():
        code = "449931000124108"

    if "Removal from state".upper() in string.upper():
        code = "449941000124103"

    if "Hospital Disposition".upper() in string.upper():
        code = "455401000124109"

    return code


# Below are the extentions for patient's profile
# Patient's extentions -
# Age
# Birth Sex
# Birth Place
# Place of death
# Facility Name
# Funeral Facility Name
# Race of Patient 1-5
# Patient's Education
# Patient's Job
# Patient's Industry
# Patient's Army Service
# Patient's Disposition Type
# Patient's Disposition Faclity Name
# Patient's Disposition Faclity Address -
#     City
#     Country
#     District
#     State
#     Line
# Patient's Funeral Facility Name
# Patient's Funeral Facility Address -
#     City
#     Country
#     District
#     State
#     Line


def loadpatientextensions(csvjsonobject):
    """
    This function loads patients extentions from CSV file
    :param csvjsonobject: csn json object to load data
    :return: returns json object with patient's extentions data
    """
    extension_array = []

    # 1
    ext1 = Extension()
    ext1.url = PATIENT_DECEDENT_SD["sdr-decedent-Age-extension"]
    ext1.valueDecimal = int(csvjsonobject['PATIENT_AGE'])
    extension_array.append(del_none(ext1.__dict__))
    # 2
    ext2 = Extension()
    ext2.url = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-birthsex"
    ext2codeableconcept = CodeableConcept()

    coding = Coding()
    coding.code = 'F'  # csvjsonobject["PATIENT_BIRTH_SEX"]  # birth sex from PDF
    if (coding.code == "F" or coding.code == "f"):
        coding.display = "Female"
    elif (coding.code == "M" or coding.code == "m"):
        coding.display = "Male"
    else:
        coding.display = "Unspecified"
    coding.system = "http://hl7.org/fhir/us/core/ValueSet/us-core-birthsex"
    ext2codeableconcept.coding = coding.__dict__
    ext2.valueCodeableConcept = ext2codeableconcept.__dict__
    extension_array.append(del_none(ext2.__dict__))
    # 3
    ext3 = Extension()
    ext3.url = PATIENT_DECEDENT_SD["sdr-decedent-Birthplace-extension"]

    address = Address()
    address.city = csvjsonobject['PATIENT_BIRTH_CITY']  # city of birth place from PDF
    address.country = csvjsonobject['PATIENT_BIRTH_COUNTRY'] # from PDF - birth place country
    address.district = csvjsonobject['PATIENT_BIRTH_DISTRICT']  # from PDF - birth place district
    address.line = [csvjsonobject['PATIENT_BIRTH_LINE']]  # from PDF - birth place line
    address.state = csvjsonobject['PATIENT_BIRTH_STATE']  # from PDF - birth place state
    address.type = "postal"

    ext3.valueAddress = address.__dict__

    extension_array.append(del_none(ext3.__dict__))
    # 4
    ext4 = Extension()
    ext4.url = PATIENT_DECEDENT_SD["sdr-decedent-PlaceOfDeath-extension"]

    ext4.extension = []

    # first extention in Place of Death Data
    ext401 = Extension()
    ext401.url = PATIENT_DECEDENT_SD["sdr-decedent-PlaceOfDeathType-extension"]

    ext401codeableconcept = CodeableConcept()

    coding = Coding()
    coding.code = "16983000"  # check from PDF and write a if statements for possible palces of deaths
    coding.display = "Death in hospital"  # from PDF - place of death extention
    coding.system = "http://snomed.info/sct"
    ext401codeableconcept.coding = coding.__dict__
    ext401.valueCodeableConcept = ext401codeableconcept.__dict__

    ext4.extension.append(del_none(ext401.__dict__))

    # second extention in Place of Death Data
    ext402 = Extension()
    ext402.url = PATIENT_DECEDENT_SD["sdr-decedent-FacilityName-extension"]
    ext402.valueString = csvjsonobject["PATIENT_PLACE_OF_DEATH"]  # facility name patient's death from PDF

    ext4.extension.append(del_none(ext402.__dict__))

    # third extension in Place of Death Data
    ext403 = Extension()
    ext403.url = "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"\
                 "shr-core-PostalAddress-extension"

    address = Address()
    address.city = csvjsonobject['PATIENTS_FUNERAL_FACILITY_CITY']  # city of birth place from PDF
    address.country = csvjsonobject['PATIENTS_FUNERAL_FACILITY_COUNTRY']  # from PDF - place of death country
    address.district = csvjsonobject['PATIENTS_FUNERAL_FACILITY_DISTRICT']  # from PDF - place of death district
    address.line = [csvjsonobject['PATIENTS_FUNERAL_FACILITY_LINE']]  # from PDF - place of death line
    address.state = csvjsonobject['PATIENTS_FUNERAL_FACILITY_STATE']  # from PDF - place of death state
    address.type = "postal"

    ext403.valueAddress = address.__dict__
    ext4.extension.append(del_none(ext403.__dict__))

    # add to #4
    extension_array.append(del_none(ext4.__dict__))

    # 5

    ext5 = Extension()
    ext5.url = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity"

    ext5.extension = []

    # first extension to mention race of patient from PDF
    ext501 = Extension()
    ext501.url = "text"
    ext501.valueString = csvjsonobject['RACE_OF_PATIENT_1']  # from PDF - race of patient

    ext5.extension.append(del_none(ext501.__dict__))

    # second extention to mention race of patient from PDF
    ext502 = Extension()
    ext502.url = "ombCategory"

    coding = Coding()
    coding.code = "2186-5"  # generate from PDF
    coding.display = csvjsonobject['RACE_OF_PATIENT_2']  # RACE OF PATIENT - from PDF
    coding.system = "urn:oid:2.16.840.1.113883.6.238"

    ext502.valueCodeableConcept = del_none(coding.__dict__)

    ext5.extension.append(del_none(ext502.__dict__))

    extension_array.append(del_none(ext5.__dict__))
    # 6
    ext6 = Extension()
    ext6.url = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race"

    ext6.extension = []

    ext601 = Extension()
    ext601.url = "text"
    ext601.valueString = csvjsonobject['RACE_OF_PATIENT_3']  # from PDF - second extentsion race of patient
    ext6.extension.append(del_none(ext601.__dict__))

    ext602 = Extension()
    ext602.url = "ombCategory"

    coding = Coding()
    coding.code = "2106-3"
    coding.display = "White"  # from PDF - second extention race of patient
    coding.system = "urn:oid:2.16.840.1.113883.6.238"

    ext602.valueCoding = del_none(coding.__dict__)
    ext6.extension.append(del_none(ext602.__dict__))

    ext603 = Extension()
    ext603.url = "text"
    ext603.valueString = csvjsonobject['RACE_OF_PATIENT_4']  # from PDF - third extension race of patient
    ext6.extension.append(del_none(ext603.__dict__))

    ext604 = Extension()
    ext604.url = "ombCategory"

    coding = Coding()
    coding.code = "2118-8"
    coding.display = "Middle Eastern or North African"  # from PDF - fourth extention race of patient
    coding.system = "urn:oid:2.16.840.1.113883.6.238"

    ext604.valueCoding = del_none(coding.__dict__)
    ext6.extension.append(del_none(ext604.__dict__))

    ext605 = Extension()
    ext605.url = "text"
    ext605.valueString = "Asian"  # from PDF - fifth extenion race of patient
    ext6.extension.append(del_none(ext605.__dict__))

    ext606 = Extension()
    ext606.url = "ombCategory"

    coding = Coding()
    coding.code = "2028-9"
    coding.display = csvjsonobject['RACE_OF_PATIENT_5']  # from PDF
    coding.system = "urn:oid:2.16.840.1.113883.6.238"

    ext606.valueCoding = del_none(coding.__dict__)
    ext6.extension.append(del_none(ext606.__dict__))

    extension_array.append(del_none(ext6.__dict__))

    # 7
    ext7 = Extension()
    ext7.url = PATIENT_DECEDENT_SD["sdr-decedent-Education-extension"]

    codeable_concept = CodeableConcept()
    codeable_concept.coding = []

    coding = Coding()
    coding.display = csvjsonobject['PATIENTS_EDUCATION']  # generate from PDF - patient's education
    coding.code = patientseducation(csvjsonobject['PATIENTS_EDUCATION'])   # read and generate from PDF
    coding.system = "http://github.com/nightingaleproject/fhirDeathRecord/sdr/decedent/cs/EducationCS"

    codeable_concept.coding.append(del_none(coding.__dict__))

    ext7.valueCodeableConcept = del_none(codeable_concept.__dict__)

    extension_array.append(del_none(ext7.__dict__))

    # 8 Occupation
    ext8 = Extension()
    ext8.url = PATIENT_DECEDENT_SD["sdr-decedent-Occupation-extension"]
    ext8.extension = []

    # ext 1 - Job
    ext801 = Extension()
    ext801.url = PATIENT_DECEDENT_SD["sdr-decedent-Job-extension"]
    ext801.valueString = csvjsonobject['PATIENTS_JOB']  # from PDF - patient's job title

    ext8.extension.append(del_none(ext801.__dict__))

    # ext2 - Industry
    ext802 = Extension()
    ext802.url = PATIENT_DECEDENT_SD["sdr-decedent-Industry-extension"]
    ext802.valueString = csvjsonobject['PATIENTS_INDUSTRY']  # from PDF - patient's job industry

    ext8.extension.append(del_none(ext802.__dict__))

    extension_array.append(del_none(ext8.__dict__))

    # 9 served in Armed Forces
    ext9 = Extension()
    ext9.url = PATIENT_DECEDENT_SD["sdr-decedent-ServerInArmedForces-extension"]
    if (csvjsonobject['PATIENTS_ARMY_SERVICE'] == 'TRUE' or
            csvjsonobject['PATIENTS_ARMY_SERVICE'] == 'true'):
        ext9.valueBoolean = True  # generate from PDF - if patient served in armed forces
    else:
        ext9.valueBoolean = False
    extension_array.append(del_none(ext9.__dict__))

    # 10
    ext10 = Extension()
    ext10.url = PATIENT_DECEDENT_SD["sdr-decedent-Disposition-extension"]
    ext10.extension = []

    # ext1 - disposition type

    # Concept Code	Preferred Concept Name
	# OTH	            Other
	# 449951000124101	Donation
	# 449971000124106	Burial
	# 449961000124104	Cremation
	# 449931000124108	Entombment
	# 449941000124103	Removal from state
	# 455401000124109	Hospital Disposition
	# UNK	            Unknown

    ext101 = Extension()
    ext101.url = PATIENT_DECEDENT_SD["sdr-decedent-DispositionType-extension"]

    codeable_concept = CodeableConcept()
    codeable_concept.coding = []

    coding = Coding()
    coding.code = dispositiontype(csvjsonobject['PATIENTS_DISPOSITION_TYPE'])
    coding.display = csvjsonobject['PATIENTS_DISPOSITION_TYPE']  # from PDF - decedent's dispositon type
    coding.system = "http://snomed.info/sct"

    codeable_concept.coding.append(del_none(coding.__dict__))

    ext101.valueCodeableConcept = del_none(codeable_concept.__dict__)

    ext10.extension.append(del_none(ext101.__dict__))

    # ext2 - disposition facility
    ext102 = Extension()
    ext102.url = PATIENT_DECEDENT_SD["sdr-decedent-DispositionFacility-extension"]
    ext102.extension = []

    # sub ext 1 - facility Name
    subext1021 = Extension()
    subext1021.url = PATIENT_DECEDENT_SD["sdr-decedent-FacilityName-extension"]
    subext1021.valueString = csvjsonobject['PATIENTS_DISPOSITION_FACLITY_NAME']  # from PDF - facility name

    ext102.extension.append(del_none(subext1021.__dict__))
    # sub ext 2 - sh-core postal address
    subext1022 = Extension()
    subext1022.url = "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"\
                     "shr-core-PostalAddress-extension"

    address = Address()
    address.city = csvjsonobject['PATIENTS_DISPOSITION_FACLITY_CITY']  # from PDF - disposition facilty city
    address.country = csvjsonobject['PATIENTS_DISPOSITION_FACLITY_COUNTRY']  # from PDF - dispoaition facility country
    address.district = csvjsonobject[
        'PATIENTS_DISPOSITION_FACLITY_DISTRICT']  # from PDF - disposition facility district
    address.line = [csvjsonobject['PATIENTS_DISPOSITION_FACLITY_LINE']]  # from PDF - disposition facility line
    address.state = csvjsonobject['PATIENTS_DISPOSITION_FACLITY_STATE']  # from PDF - disposition facility state
    address.type = "postal"

    subext1022.valueAddress = del_none(address.__dict__)
    ext102.extension.append(del_none(subext1022.__dict__))

    ext10.extension.append((del_none(ext102.__dict__)))
    # ext3 - Funeral Facility
    ext103 = Extension()
    ext103.url = PATIENT_DECEDENT_SD["sdr-decedent-FuneralFacility-extension"]
    ext103.extension = []

    # sub ext 1 - facility Name
    subext1031 = Extension()
    subext1031.url = PATIENT_DECEDENT_SD["sdr-decedent-FacilityName-extension"]
    subext1031.valueString = csvjsonobject['PATIENTS_FUNERAL_FACILITY_NAME']  # from PDF - funeral facility name

    ext103.extension.append(del_none(subext1031.__dict__))
    # sub ext 2 - sh-core postal address
    subext1032 = Extension()
    subext1032.url = "http://nightingaleproject.github.io/fhirDeathRecord/StructureDefinition/"\
                     "shr-core-PostalAddress-extension"

    address = Address()
    address.city = csvjsonobject['PATIENTS_FUNERAL_FACILITY_CITY']  # place from PDF - funeral facility city
    address.country = csvjsonobject['PATIENTS_FUNERAL_FACILITY_COUNTRY']  # from PDF - funeral facility country
    address.district = csvjsonobject['PATIENTS_FUNERAL_FACILITY_DISTRICT']  # from PDF - funeral facility district
    address.line = [csvjsonobject['PATIENTS_FUNERAL_FACILITY_LINE']]  # from PDF - funeral facility line
    address.state = csvjsonobject['PATIENTS_FUNERAL_FACILITY_STATE']  # from PDF - funeral facility state
    address.type = "postal"

    subext1032.valueAddress = del_none(address.__dict__)
    ext103.extension.append(del_none(subext1032.__dict__))

    ext10.extension.append(del_none(ext103.__dict__))

    extension_array.append(del_none(ext10.__dict__))

    return extension_array


# Pracitioner:
#
# Practitioner's Address
#     City
#     Country
#     District
#     Line
#     State
# Certifier Type - Extention
# Practitioner's Family name
# Practitioner's given name
# Practitioner's suffix
# Practitioner's Education


# practitioner data
def load_practitioner_data(uuid_dict, csvjsondata):
    """
    This function loads practitioner's data from CSV file.
    :param uuid_dict: uuid_dict holds the uuid data which are generated everytime the program is executed
    :param csvjsondata: holds json data from csv
    :return: returns practitioner's json object
    """
    practitioner = Practitioner()

    # resource type
    practitioner.resource_type = "Practitioner"

    # address
    address = Address()

    address.city = csvjsondata['PRACTITIONERS_ADDRESS_CITY']  # from PDF - practitioner's city
    address.country = csvjsondata['PRACTITIONERS_ADDRESS_COUNTRY']  # from PDF - practitioner's country
    address.district = csvjsondata['PRACTITIONERS_ADDRESS_DISTRICT']  # from PDF - practitioner's district
    address.line = [csvjsondata['PRACTITIONERS_ADDRESS_LINE']]  # from PDF - practitioner's line
    address.state = csvjsondata['PRACTITIONERS_ADDRESS_STATE']  # from PDF - practitioner's state

    practitioner.address = del_none(address.__dict__)
    # extention

    # Codes for the extention for Practitioners
    #
    # Concept Code	Concept Name
	# 434641000124105	Physician certified death certificate
	# 434651000124107	Physician certified and pronounced death certificate
	# 310193003		Coroner
	# 440051000124108	Medical Examiner
	# OTH	            Other


    # extention
    # extention = Extension()
    # extention.url = PRACTITIONER_SD["sdr-deathRecord-CertifierType-extension"]
    #
    # codeableconcept = CodeableConcept()
    # codeableconcept.coding = []
    # coding = Coding()
    # coding.code = "434651000124107"  # generate from PDF and refer the system link
    # coding.display = "Physician (Pronouncer and Certifier)"  # generate from PDF and refer the system link
    # coding.system = "http://snomed.info/sct"
    #
    # codeableconcept.coding.append(del_none(coding.__dict__))
    #
    # extention.valueCodeableConcept = del_none(codeableconcept.__dict__)
    #
    # practitioner.extension = del_none(extention.__dict__)
    # id
    practitioner.id = uuid_dict["Practitioner"]

    # name
    practitionername = HumanName()
    practitionername.family = csvjsondata['PRACTITIONERS_FAMILY_NAME']  # from PDF - practitioner's family name
    practitionername.given = [csvjsondata['PRACTITIONERS_GIVEN_NAME']]  # from PDF - practitioner's given name
    practitionername.suffix = [csvjsondata['PRACTITIONERS_SUFFIX']]  # from PDF - practitioner's suffix
    practitionername.use = "official"

    practitioner.name = del_none(practitionername.__dict__)

    # qualification
    practitioner.qualification = []

    practitioner_qualification_items = PractitionerQualification()

    # GENERATED CODE FROM THE EDUCATION
    practitioner_qualification_items.code = csvjsondata[
        'PRACTITIONERS_EDUCATION']  # generate from PDF and refer http://hl7.org/fhir/v2/0360/2.7
    practitioner_qualification_items.display = PRACTITIONER_EDU_CODES.get(
        csvjsondata['PRACTITIONERS_EDUCATION'])  # generate from http://hl7.org/fhir/v2/0360/2.7
    practitioner_qualification_items.system = "http://hl7.org/fhir/v2/0360/2.7"

    practitioner.qualification.append(del_none(practitioner_qualification_items.__dict__))

    return practitioner


    # Bundle Entry:
    #     FullUrl
    #     Entry


# create entry for bundle entry
def createbundleentry(uuid_dict, profile_name):
    """
    This function creates bundle entry
    :param uuid_dict: this data structure holds uuid generated from the uuid dict function
    :param profile_name: this variable holds profile name to lookup into the uuid dict
    :return: returns bundle entry
    """
    bundle_entry = BundleEntry()
    bundle_entry.fullUrl = uuid_dict[profile_name]

    return bundle_entry, uuid_dict[profile_name]


def mannerofdeath(string):
    """
    This function returns code value for manner of death depending on the value in csv file
    :param string: manner of death from death certificate
    :return: code value for the specified manner of death
    """

    code = "65037004" # "Could not be determined"

    if "Natural".upper() in string.upper():
        code = "38605008"

    if "Accident".upper() in string.upper():
        code = "7878000"

    if "Suicide".upper() in string.upper():
        code = "44301001"

    if "Homicide".upper() in string.upper():
        code = "27935005"

    if "Pending Investigation".upper() in string.upper():
        code = "185973002"

    return code

# Cause of Death Data:
# ---------------------------------------------
# Manner of Death
# Actual or Presumerd Date of Death
# Date Pronounced Dead
# Cause of Death Condition 1
#     Time cause of death condition 1 occured
# Cause of Death Condition 2
#     Time cause of death condition 2 occured
# Contributed to Death Condition
# Autopsy performed[True/False]
# Autopsy results avaliable [True/False]
# Medical examiner contacted [True/False]
# Tobacco contributed to death
# Timing of Recent Pregnancy In Relation

# observations and conditions

def load_cod_data(uuiddict, csvjsonobject):
    """
    Returns cause of death data json object for bundle object
    :param uuiddict:
    :param csvjsonobject:
    :return: cause of death data json object for bundle object
    """

    # referenced to patient URN:UID
    output = []
    # observation bundle entry 1

    obentry1, idurn = createbundleentry(uuiddict, "Observation1")

    observation = Observation()

    # code

    codeableconcept = CodeableConcept()

    codeableconcept.coding = []

    coding = Coding()
    coding.code = "69449-7"
    coding.display = "Manner of death"
    coding.system = "http://loinc.org"

    codeableconcept.coding.append(del_none(coding.__dict__))

    observation.code = del_none(codeableconcept.__dict__)

    obentry1.resource = del_none(observation.__dict__)
    output.append(del_none(obentry1.__dict__))

    # id

    observation.id = idurn

    # meta

    parameterdef = ParameterDefinition()
    parameterdef.profile = []
    parameterdef.profile.append(OBSERVATION_SD["sdr-causeOfDeath-MannerOfDeath"])

    observation.meta = del_none(parameterdef.__dict__)

    # resource Type

    observation.resource_type = "Observation"

    # status

    observation.status = "final"

    # subject

    fhirreference = FHIRReference()
    fhirreference.reference = uuiddict['Patient']

    observation.subject = del_none(fhirreference.__dict__)

    # valueCodeableConcept

    # Manner of death value set
    #     ConceptCode	Preferred Concept Name
    #     38605008	Natural
    #     7878000	    Accident
    #     44301001	Suicide
    #     27935005	Homicide
    #     185973002	Pending Investigation
    #     65037004	Could not be determined

    codeableconcept = CodeableConcept()
    codeableconcept.code = mannerofdeath(csvjsonobject['MANNER_OF_DEATH']) # eg."38605008"  # generate data from PDF
    codeableconcept.display = csvjsonobject['MANNER_OF_DEATH']  # generate from PDF data - manner of death
    codeableconcept.system = "http://snomed.info/sct"

    observation.valueCodeableConcept = del_none(codeableconcept.__dict__)

    # observation bundle entry 2

    obentry2, idurn = createbundleentry(uuiddict, "Observation2")
    observation2 = Observation()

    # code

    codeableconcept = CodeableConcept()

    codeableconcept.coding = []

    coding = Coding()
    coding.code = "81956-5"
    coding.display = "Date and time of death"  # ACTUAL OR PRESUMED DATE OF DEATH
    coding.system = "http://loinc.org"

    codeableconcept.coding.append(del_none(coding.__dict__))

    observation2.code = del_none(codeableconcept.__dict__)

    # id
    observation2.id = idurn

    # meta

    parameterdef = ParameterDefinition()
    parameterdef.profile = []
    parameterdef.profile.append(OBSERVATION_SD["sdr-causeOfDeath-ActualOrPresumedDateOfDeath"])

    observation2.meta = del_none(parameterdef.__dict__)

    # resource Type

    observation2.resource_type = "Observation"

    # status

    observation2.status = "final"

    # subject

    fhirreference = FHIRReference()
    fhirreference.reference = uuiddict['Patient']

    observation2.subject = del_none(fhirreference.__dict__)

    # value Date time
    # CONVERT DATE FROM THE CSV FILE TO BELOW FORMAT

    date = csvjsonobject['ACTUAL_OR_PRESUMERD_DATE_OF_DEATH']
    time = csvjsonobject['ACTUAL_OR_PRESUMERD_TIME_OF_DEATH']

    datetime_to_format = datetime.strptime(date + "T" + time, '%d-%b-%yT%H:%M:%S')
    datetime_to_format = str(datetime_to_format) + ".0000000+00:00"

    observation2.valueDateTime = datetime_to_format  # from PDF - actual or presumer date of death

    obentry2.resource = del_none(observation2.__dict__)
    output.append(del_none(obentry2.__dict__))

    # observation bundle entry 3

    obentry3, idurn = createbundleentry(uuiddict, "Observation3")

    observation3 = Observation()

    # code

    codeableconcept = CodeableConcept()

    codeableconcept.coding = []

    coding = Coding()
    coding.code = "80616-6"
    coding.display = "Date and time pronounced dead"
    coding.system = "http://loinc.org"

    codeableconcept.coding.append(del_none(coding.__dict__))

    observation3.code = del_none(codeableconcept.__dict__)

    # id
    observation3.id = idurn

    # meta

    parameterdef = ParameterDefinition()
    parameterdef.profile = []
    parameterdef.profile.append(OBSERVATION_SD["sdr-causeOfDeath-DatePronoucedDead"])

    observation3.meta = del_none(parameterdef.__dict__)

    # resource Type

    observation3.resource_type = "Observation"

    # status

    observation2.status = "final"

    # subject

    fhirreference = FHIRReference()
    fhirreference.reference = uuiddict['Patient']

    observation3.subject = del_none(fhirreference.__dict__)

    # value Date time
    # CONVERT DATE FROM THE CSV TO BELOW TIME FORMAT
    date = csvjsonobject['DATE_PRONOUNCED_DEAD']
    time = csvjsonobject['TIME_PRONOUNCED_DEAD']

    datetime_to_format = datetime.strptime(date + "T" + time, '%d-%b-%yT%H:%M:%S')
    datetime_to_format = str(datetime_to_format) + ".0000000+00:00"
    observation3.valueDateTime = datetime_to_format # from PDF - date pronounced dead

    obentry3.resource = del_none(observation3.__dict__)
    output.append(del_none(obentry3.__dict__))

    # observation bundle entry 4

    obentry4, idurn = createbundleentry(uuiddict, "Observation4")
    condition4 = Condition()

    # clinical Status
    condition4.clinicalStatus = "active"

    # id
    condition4.id = idurn

    # meta
    parameterdef = ParameterDefinition()
    parameterdef.profile = []
    parameterdef.profile.append(OBSERVATION_SD["sdr-causeOfDeath-CauseOfDeathCondition"])

    # onestString # from PDF
    condition4.onsetString = csvjsonobject[
        'TIME_CAUSE_OF_DEATH_CONDITION_1_OCCURED']  # from PDF - time cause of death condition

    # subject
    fhirreference = FHIRReference()
    fhirreference.reference = uuiddict['Patient']

    condition4.subject = del_none(fhirreference.__dict__)

    condition4.meta = del_none(parameterdef.__dict__)

    # resource type
    condition4.resource_type = "Condition"

    # text
    narrative = Narrative()

    narrative.div = "<div xmlns='http://www.w3.org/1999/xhtml'>" + csvjsonobject[
        'CAUSE_OF_DEATH_CONDITION_1'] + "</div>"  # from PDF
    narrative.status = "additional"

    condition4.text = del_none(narrative.__dict__)

    obentry4.resource = del_none(condition4.__dict__)
    output.append(del_none(obentry4.__dict__))

    ##### observation bundle entry 5

    obentry5, idurn = createbundleentry(uuiddict, "Observation5")
    condition5 = Condition()

    # clinical Status
    condition5.clinicalStatus = "active"

    # id
    condition5.id = idurn

    # meta
    parameterdef = ParameterDefinition()
    parameterdef.profile = []
    parameterdef.profile.append(OBSERVATION_SD["sdr-causeOfDeath-CauseOfDeathCondition"])

    # onestString # from PDF
    condition5.onsetString = csvjsonobject[
        'TIME_CAUSE_OF_DEATH_CONDITION_2_OCCURED']  # from PDF - time cause of death condition 2

    # subject
    fhirreference = FHIRReference()
    fhirreference.reference = uuiddict['Patient']

    condition5.subject = del_none(fhirreference.__dict__)

    condition5.meta = del_none(parameterdef.__dict__)

    # resource type
    condition5.resource_type = "Condition"

    # text
    narrative = Narrative()

    narrative.div = "<div xmlns='http://www.w3.org/1999/xhtml'>" + csvjsonobject[
        'CAUSE_OF_DEATH_CONDITION_2'] + "</div>"  # from PDF - cause of death condition 2
    narrative.status = "additional"

    condition5.text = del_none(narrative.__dict__)

    obentry5.resource = del_none(condition5.__dict__)

    obentry5.resource = del_none(condition5.__dict__)
    output.append(del_none(obentry5.__dict__))

    #####observation bundle entry 6

    obentry6, idurn = createbundleentry(uuiddict, "Observation6")
    condition6 = Condition()

    # resource type
    condition6.resource_type = "Condition"

    # meta
    parameterdef = ParameterDefinition()
    parameterdef.profile = []
    parameterdef.profile.append(OBSERVATION_SD["sdr-causeOfDeath-ContributeToDeathCondition"])

    # text
    narrative = Narrative()

    narrative.div = "<div xmlns='http://www.w3.org/1999/xhtml'>" + csvjsonobject[
        'CONTRIBUTED_TO_DEATH_CONDITION'] + "</div>"  # from PDF - contributed to death condition
    narrative.status = "additional"

    condition6.text = del_none(narrative.__dict__)

    # subject
    fhirreference = FHIRReference()
    fhirreference.reference = uuiddict['Patient']

    condition6.subject = del_none(fhirreference.__dict__)

    condition6.meta = del_none(parameterdef.__dict__)

    obentry6.resource = del_none(condition6.__dict__)
    output.append(del_none(obentry6.__dict__))

    ##### observation bundle entry 7

    obentry7, idurn = createbundleentry(uuiddict, "Observation7")
    observation7 = Observation()

    # id
    observation7.id = idurn

    # resource type
    observation7.resource_type = "Observation"

    # meta
    parameterdef = ParameterDefinition()
    parameterdef.profile = []
    parameterdef.profile.append(OBSERVATION_SD["sdr-causeOfDeath-AutopsyPerformed"])

    # subject
    fhirreference = FHIRReference()
    fhirreference.reference = uuiddict['Patient']

    observation7.subject = del_none(fhirreference.__dict__)

    observation7.meta = del_none(parameterdef.__dict__)

    # status
    observation7.status = "final"

    # code

    codeableconcept = CodeableConcept()

    codeableconcept.coding = []

    coding = Coding()
    coding.code = "85699-7"
    coding.display = "Autopsy was performed"
    coding.system = "http://loinc.org"

    codeableconcept.coding.append(del_none(coding.__dict__))

    observation7.code = del_none(codeableconcept.__dict__)

    # value Boolean
    if (csvjsonobject['AUTOPSY_PERFORMED[TRUE/FALSE]'] == 'TRUE'
            or csvjsonobject['AUTOPSY_PERFORMED[TRUE/FALSE]'] == 'true'):
        observation7.valueBoolean = True
    else:
        observation7.valueBoolean = False

    obentry7.resource = del_none(observation7.__dict__)
    output.append(del_none(obentry7.__dict__))

    ##### observation bundle entry 8

    obentry8, idurn = createbundleentry(uuiddict, "Observation8")
    observation8 = Observation()

    # id
    observation8.id = idurn

    # resource type
    observation8.resource_type = "Observation"

    # meta
    parameterdef = ParameterDefinition()
    parameterdef.profile = []
    parameterdef.profile.append(OBSERVATION_SD["sdr-causeOfDeath-AutopsyResultsAvailable"])

    # subject
    fhirreference = FHIRReference()
    fhirreference.reference = uuiddict['Patient']

    observation8.subject = del_none(fhirreference.__dict__)

    observation8.meta = del_none(parameterdef.__dict__)

    # status
    observation8.status = "final"

    # code

    codeableconcept = CodeableConcept()

    codeableconcept.coding = []

    coding = Coding()
    coding.code = "69436-4"
    coding.display = "Autopsy results available"
    coding.system = "http://loinc.org"

    codeableconcept.coding.append(del_none(coding.__dict__))

    observation8.code = del_none(codeableconcept.__dict__)

    # value Boolean

    if (csvjsonobject['AUTOPSY_RESULTS_AVALIABLE_[TRUE/FALSE]'] == 'TRUE' or
            csvjsonobject['AUTOPSY_RESULTS_AVALIABLE_[TRUE/FALSE]'] == 'true'):
        observation8.valueBoolean = True
    else:
        observation8.valueBoolean = False

    obentry8.resource = del_none(observation8.__dict__)
    output.append(del_none(obentry8.__dict__))

    ##### observation bundle entry 9

    obentry9, idurn = createbundleentry(uuiddict, "Observation9")
    observation9 = Observation()

    # id
    observation9.id = idurn

    # resource type
    observation9.resource_type = "Observation"

    # meta
    parameterdef = ParameterDefinition()
    parameterdef.profile = []
    parameterdef.profile.append(OBSERVATION_SD["sdr-causeOfDeath-MedicalExaminerContacted"])

    # subject
    fhirreference = FHIRReference()
    fhirreference.reference = uuiddict['Patient']

    observation9.subject = del_none(fhirreference.__dict__)

    observation9.meta = del_none(parameterdef.__dict__)

    # status
    observation9.status = "final"

    # code

    codeableconcept = CodeableConcept()

    codeableconcept.coding = []

    coding = Coding()
    coding.code = "74497-9"
    coding.display = "Medical examiner or coroner was contacted"
    coding.system = "http://loinc.org"

    codeableconcept.coding.append(del_none(coding.__dict__))

    observation9.code = del_none(codeableconcept.__dict__)

    # value Boolean
    if (csvjsonobject['MEDICAL_EXAMINER_CONTACTED_[TRUE/FALSE]'] == 'TRUE'
            or csvjsonobject['MEDICAL_EXAMINER_CONTACTED_[TRUE/FALSE]'] == 'true'):
        observation7.valueBoolean = True
    else:
        observation7.valueBoolean = False
    observation9.valueBoolean = False

    obentry9.resource = del_none(observation9.__dict__)
    output.append(del_none(obentry9.__dict__))

    ##### observation bundle entry 10


    # Contributory Tobacco Use (NCHS)	Details
    #
    # Concept Code	referred Concept Name
	# 373066001	Yes
	# 373067005	No
	# 2931005	3	Probably
	# 261665006	Unknown


    obentry10, idurn = createbundleentry(uuiddict, "Observation10")
    observation10 = Observation()

    # resource_type
    observation10.resource_type = "Observation"

    # id
    observation10.id = idurn

    # meta
    parameterdef = ParameterDefinition()
    parameterdef.profile = []
    parameterdef.profile.append(OBSERVATION_SD["sdr-causeOfDeath-TobaccoUseContributedToDeath"])

    # subject
    fhirreference = FHIRReference()
    fhirreference.reference = uuiddict['Patient']

    observation10.subject = del_none(fhirreference.__dict__)

    observation10.meta = del_none(parameterdef.__dict__)

    # status
    observation10.status = "final"

    # code

    codeableconcept = CodeableConcept()

    codeableconcept.coding = []

    coding = Coding()
    coding.code = "69443-0"
    coding.display = "Did tobacco use contribute to death"
    coding.system = "http://loinc.org"

    codeableconcept.coding.append(del_none(coding.__dict__))

    observation10.code = del_none(codeableconcept.__dict__)

    # value codeable concept

    codeableconcept = CodeableConcept()

    codeableconcept.coding = []

    coding = Coding()
    coding.code = "373067005"  # from pdf - generate from next option
    coding.display = csvjsonobject['TOBACCO_CONTRIBUTED_TO_DEATH']  # from pdf - did tobacco contributed to death
    coding.system = "http://snomed.info/sct"

    codeableconcept.coding.append(del_none(coding.__dict__))
    observation10.valueCodeableConcept = del_none(codeableconcept.__dict__)

    obentry10.resource = del_none(observation10.__dict__)
    output.append(del_none(obentry10.__dict__))

    #### if the patient is female then only
    ##### observation bundle entry 11

    # Pregnancy Status (NCHS)	Deta
    #
    # Concept Preferred Concept Name
	# PHC1260	Not pregnant within past year
	# PHC1261	Pregnant at time of death
	# PHC1262	Not pregnant, but pregnant within 42 days of death
	# PHC1263	Not pregnant, but pregnant 43 days to 1 year before death
	# PHC1264	Unknown if pregnant within the past year
	# NA	    not applicable

    if csvjsonobject['PATIENT_GENDER_ATTIMEOFDEATH'].upper() == "FEMALE":
        # or csvjsonobject['PATIENT_GENDER_ATTIMEOFDEATH'] == "female"):
        obentry11, idurn = createbundleentry(uuiddict, "Observation10")
        pregnancyentry = Observation()

        # resource_type
        pregnancyentry.resource_type = "Observation"

        # id
        pregnancyentry.id = idurn

        # meta
        parameterdef = ParameterDefinition()
        parameterdef.profile = []
        parameterdef.profile.append(OBSERVATION_SD["sdr-causeOfDeath-TimingOfRecentPregnancyInRelationToDeath"])

        # subject
        fhirreference = FHIRReference()
        fhirreference.reference = uuiddict['Patient']

        pregnancyentry.subject = del_none(fhirreference.__dict__)

        pregnancyentry.meta = del_none(parameterdef.__dict__)

        # status
        pregnancyentry.status = "final"

        # code

        codeableconcept = CodeableConcept()

        codeableconcept.coding = []

        coding = Coding()
        coding.code = "69442-2"
        coding.display = "Timing of recent pregnancy in relation to death"
        coding.system = "http://loinc.org"

        codeableconcept.coding.append(del_none(coding.__dict__))

        pregnancyentry.code = del_none(codeableconcept.__dict__)

        # value codeable concept

        codeableconcept = CodeableConcept()

        codeableconcept.coding = []

        coding = Coding()
        coding.code = "PHC1260"  # pregnancy Female patient only from PDF
        coding.display = "Not pregnant within past year"  # from PDF
        coding.system = "http://github.com/nightingaleproject/fhirDeathRecord/sdr/causeOfDeath/vs/PregnancyStatusVS"

        codeableconcept.coding.append(del_none(coding.__dict__))
        observation10.valueCodeableConcept = del_none(codeableconcept.__dict__)

        obentry11.resource = del_none(pregnancyentry.__dict__)
        output.append(del_none(obentry11.__dict__))

    return output

def del_none(inputdict):
    """
    Delete keys with the value ``None`` in a dictionary, recursively.
    This alters the input so you may wish to ``copy`` the dict first.
    """
    for key, value in list(inputdict.items()):
        if value is None:
            del inputdict[key]
        elif isinstance(value, dict):
            del_none(value)
    return inputdict  # For convenience

@NS.route('/fhirjson', endpoint="fhir-json")
@NS.doc()
@NS.expect(FILE_UPLOAD)
class GenerateFhirJson(Resource):
    """
    Generate FHIR JSON from the input CSV file
    """
    def post(self):  # pylint: disable=R0201
        """
        generate FHIR JSON
        :return: FHIR JSON object
        """
        args = FILE_UPLOAD.parse_args()
        uploaded_file = args['file'] # This is FileStorage instance

        byte_data = str(uploaded_file.read(), 'utf-8')

        file = open("data.csv", "w", newline='')

        string_data = StringIO(byte_data)
        for line in string_data:
            file.write(line)

        file.close()

        file = open("data.csv", "r")

        with(file) as csvfile:
            reader1 = csv.reader(csvfile, delimiter=',')
            line_number = 0
            output = []
            for row in reader1:
                # add logic to create a json object
                if line_number == 0:
                    column_name = []
                    # read all the column names
                    for i in range(0, len(row), 1):
                        column_name.append(row[i])
                    line_number = line_number + 1
                else:
                    # create a json object with the variables values in it
                    json_object = {}
                    for i in range(0, len(row), 1):
                        json_object[column_name[i]] = row[i]
                    # bundle entry will have all the document data in dict format
                    uuid_dict = generate_uuid()
                    # composition
                    composition = load_composition_data(uuid_dict)
                    # patient
                    patient = load_patient_data(uuid_dict, json_object)
                    # practitioner
                    practitioner = load_practitioner_data(uuid_dict, json_object)

                    causeofdeathdata = load_cod_data(uuid_dict, json_object)
                    # Creating a bundle record for final output
                    bundle = Bundle()
                    # entry
                    bundle.entry = []
                    bundle.entry.append(del_none(composition.__dict__))
                    bundle.entry.append(del_none(patient.__dict__))
                    bundle.entry.append(del_none(practitioner.__dict__))
                    for i in range(0, len(causeofdeathdata), 1):
                        bundle.entry.append(del_none(causeofdeathdata[i]))
                    # resource_type
                    bundle.resource_type = "Bundle"
                    # type
                    bundle.type = "document"
                    # id
                    bundle.id = random.randint(100000, 900000)
                    line_number = line_number + 1
                    output.append(del_none(bundle.__dict__))
        return output

if __name__ == '__main__':
    APP.run(debug=True)
