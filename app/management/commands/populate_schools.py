
from app.models import Wilayas, WilayaSchool
import logging
import pandas as pd

from fuzzywuzzy import fuzz
from unidecode import unidecode
import openpyxl
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Import data from an Excel file to database'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the .xlsx file to import')

    def handle(self, *args, **options):
        file_path = options['file_path']

        try:
            vehicle_excel = file_path
            df = pd.read_excel(vehicle_excel, sheet_name="COLLEG-LYCEE", header=2)

            for index, row in df.iterrows():

                wilaya_name = row["WILAYA"]
                wilaya_name = unidecode(wilaya_name).title()
                matching_wilaya = Wilayas.objects.all()
                similarity_threshold = 85
                matching_records = None
                for wilaya_record in matching_wilaya:

                    wilaya_record_name_normalized = unidecode(wilaya_record.name)
                    similarity_score = fuzz.ratio(wilaya_name, wilaya_record_name_normalized)

                    if ("Algiers" in wilaya_record_name_normalized and "Alger" in wilaya_name) or (
                            "M'Sila" in wilaya_record_name_normalized and "M'sila" in wilaya_name):
                        similarity_score = 200

                    if similarity_score >= similarity_threshold:
                        matching_records = wilaya_record
                        break

                logging.log(msg=matching_records, level=1)
                if matching_records:
                    wilaya = matching_records
                    # Logic to distinguish between types
                    wilaya_school, created = WilayaSchool.objects.get_or_create(
                        type='COLLEGE',  # If "COMMERCES" sheet is loaded, set type to 'COMPANY'
                        wilaya=wilaya,
                        defaults={
                            'count': row[1],
                            'normalized': round((100 * row[1] / 2488), 2),
                            'norm_coeff': round((100 * row[1] / 2488), 2) * 10
                        }
                    )

            df = pd.read_excel(vehicle_excel, sheet_name="pRIMAIRE", header=1)

            for index, row in df.iterrows():

                wilaya_name = row["WILAYA"]
                wilaya_name = unidecode(wilaya_name).title()
                matching_wilaya = Wilayas.objects.all()
                similarity_threshold = 85
                matching_records = None

                for wilaya_record in matching_wilaya:
                    wilaya_record_name_normalized = unidecode(wilaya_record.name)
                    similarity_score = fuzz.ratio(wilaya_name, wilaya_record_name_normalized)

                    if ("Algiers" in wilaya_record_name_normalized and "Alger" in wilaya_name) or (
                            "M'Sila" in wilaya_record_name_normalized and "M'sila" in wilaya_name):
                        similarity_score = 200

                    if similarity_score >= similarity_threshold:
                        matching_records = wilaya_record
                        break

                logging.log(msg=matching_records, level=1)

                if matching_records:
                    wilaya = matching_records
                    # Logic to distinguish between types
                    wilaya_school, created = WilayaSchool.objects.get_or_create(
                        type='SCHOOL',  # If "COMMERCES" sheet is loaded, set type to 'COMPANY'
                        wilaya=wilaya,
                        defaults={
                            'count': row[1],
                            'normalized': round((100 * row[1] / 19308), 2),
                            'norm_coeff': round((100 * row[1] / 19308), 2) * 10
                        }
                    )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error processing file: {e}"))
