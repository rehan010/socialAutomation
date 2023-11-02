from django.core.management.base import BaseCommand
from app.models import WilayasVehicle , Wilayas # Import your model
import logging
from fuzzywuzzy import fuzz
from unidecode import unidecode  # Import unidecode


import pandas as pd
class Command(BaseCommand):
    help = 'Create dummy entries for YourModel'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the JSON file')

    def handle(self, *args, **options):
        file_path = options['file_path']
        try:
            vehicle_excel = file_path
            df = pd.read_excel(vehicle_excel, sheet_name="Feuil1", header=1)
            df = df.dropna()
            df = df.drop(df.index[-1])
            vehicle_list = []
            for index , row in df.iterrows():
                wailya_name = row["WILAYATE"]
                wailya_name = unidecode(wailya_name)
                matching_waliya = Wilayas.objects.all()
                similarity_threshold = 85
                matching_records = None


                for waliya_record in matching_waliya:
                    waliya_record_name_normalized = unidecode(waliya_record.name)
                    similarity_score = fuzz.ratio(wailya_name, waliya_record_name_normalized)


                    if ("Algiers" in waliya_record_name_normalized and "Alger" in wailya_name) or ("M'Sila" in waliya_record_name_normalized and "M'sila" in wailya_name):
                        similarity_score = 200

                    if similarity_score >= similarity_threshold:
                        matching_records = waliya_record
                        break

                logging.log(msg=matching_records,level=1)

                wailya = matching_records
                touring_car = row['Véhicule Tourisme']
                truck = row['Camion']
                cleaning_truck = row['Camion nette']
                bus = row['Autocar Autobus']
                semi_truck = row['Tracteur Routier']
                agricultural_tractor = row['Tracteur Agricole']
                special_vehicle = row['Véhicule Spécial']
                trailer = row['Remorque']
                motorcycle = row['Moto']
                total = row['TOTAL']
                percentage = row['%']
                vehicle_list.append(WilayasVehicle(wilaya=wailya,touring_car=touring_car,truck=truck,cleaning_truck= cleaning_truck ,bus=bus,semi_truck=semi_truck,
                               agricultural_tractor = agricultural_tractor,
                               special_vehicle = special_vehicle,
                               trailer = trailer,
                               motorcycle = motorcycle,
                               total = total,
                               percentage = percentage))

            WilayasVehicle.objects.bulk_create(vehicle_list)
            self.stdout.write(self.style.SUCCESS('Dummy entries created successfully.'))
        except FileNotFoundError:

            self.stdout.write(self.style.ERROR(f'File not found at path: {file_path}'))

