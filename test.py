'''FHIR JSON testing'''
import unittest
from csv_to_fhir_json_parser import APP as app

class FhirJsonTesting(unittest.TestCase):
    '''tests'''

    # # executed prior to each test
    def setUp(self):
        '''Set up'''
        self.app = app.test_client()

    def test_mul_patient_data(self):
        '''
        Test succesful FHIR JSON output for multiple patient data in the csv file
        :return: fhir json object array
        '''

        with open('tests/multiple_patient_data.csv', 'rb') as asset:
            response = self.app.post('entity/fhirjson', data=dict(
                file=(asset, 'data.csv'),
                        ))

            # data = json.loads(response.get_data(as_text=True))
            # print(data)

        self.assertEqual(response.status_code, 200)

    def test_no_patient_data(self):
        '''
        Test succesful FHIR JSON output for no patient data in the csv file
        :return: fhir json object array
        '''

        with open('tests/no_patient_data.csv', 'rb') as asset:
            response = self.app.post('entity/fhirjson', data=dict(
                file=(asset, 'data.csv'),
                        ))
            # data = json.loads(response.get_data(as_text=True))
            # print(data)

        self.assertEqual(response.status_code, 200)

    def test_single_patient_data(self):
        '''
        Test succesful FHIR JSON output for no patient data in the csv file
        :return: fhir json object array
        '''

        with open('tests/single_patient_data.csv', 'rb') as asset:
            response = self.app.post('entity/fhirjson', data=dict(
                file=(asset, 'data.csv'),
                        ))
            # data = json.loads(response.get_data(as_text=True))
            # print(data)

        self.assertEqual(response.status_code, 200)

    def test_missing_patient_data(self):
        '''
        Test succesful FHIR JSON output for missing patient data in the csv file
        :return: fhir json object array
        '''

        with open('tests/missing_fields_patient_data.csv', 'rb') as asset:
            response = self.app.post('entity/fhirjson', data=dict(
                file=(asset, 'data.csv'),
                        ))
            # data = json.loads(response.get_data(as_text=True))
            # print(data)

        self.assertEqual(response.status_code, 500)

if __name__ == '__main__':
    unittest.main(verbosity=2)
