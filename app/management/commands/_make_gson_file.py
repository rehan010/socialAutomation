from django.core.management.base import BaseCommand
from app.models import Wilayas  # Import your model
import json
class Command(BaseCommand):
    help = 'Create dummy entries for YourModel'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the JSON file')
    def handle(self, *args, **options):
        file_path = options['file_path']
        try:
            with open(file_path, 'r',encoding="utf-8") as json_file:
                data = json.load(json_file)
                features = data.get('features')
                waliyas_list = []
                for item in features:
                    properties = item.get('properties')
                    name = properties['name']
                    name_ar = properties.get('name_ar')
                    name_ber = properties.get("name_ber")
                    city_code = properties.get('city_code')
                    cordinates = json.dumps(item['geometry'])

                    waliyas_list.append(Wilayas(name=name,name_ar=name_ar,name_ber=name_ber,city_code=city_code,coordinates=cordinates))

                Wilayas.objects.bulk_create(waliyas_list)
                self.stdout.write(self.style.SUCCESS('Dummy entries created successfully.'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found at path: {file_path}'))
