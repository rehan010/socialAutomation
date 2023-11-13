from django.core.management.base import BaseCommand
from app.models import Wilayas,WilayaPopulation,WilayaSchool,WilayaBusiness ,WilayasVehicle,ScoreCoeff,WilayaScore# Import your model
import json
import csv
class Command(BaseCommand):
    help = 'Create dummy entries for YourModel'

    def handle(self, *args, **options):

        try:
           wilayas=Wilayas.objects.all()
           coeff = ScoreCoeff.objects.first()
           for wilaya in wilayas:
               population = (WilayaPopulation.objects.filter(wilaya=wilaya).first().normalized)*coeff.population if len(WilayaPopulation.objects.filter(wilaya=wilaya)) else 0
               school = (WilayaSchool.objects.filter(wilaya=wilaya, type='SCHOOL').first().normalized)*coeff.company if len(WilayaSchool.objects.filter(wilaya=wilaya,type='SCHOOL')) else 0
               college = (WilayaSchool.objects.filter(wilaya=wilaya, type='COLLEGE').first().normalized)*coeff.company if len(WilayaSchool.objects.filter(wilaya=wilaya, type='COLLEGE')) else 0
               business_shop = (WilayaBusiness.objects.filter(wilaya=wilaya, type='SHOPS').first().normalized)*coeff.business if len(WilayaBusiness.objects.filter(wilaya=wilaya, type='SHOPS')) else 0
               business_company = (WilayaBusiness.objects.filter(wilaya=wilaya, type='COMPANY').first().normalized)*coeff.business if len(WilayaBusiness.objects.filter(wilaya=wilaya, type='COMPANY')) else 0
               vehicle = (WilayasVehicle.objects.filter(wilaya=wilaya).first().normalized)*coeff.vehicles if len(WilayasVehicle.objects.filter(wilaya=wilaya)) else 0
               score = round((population + school + college + business_shop + business_company + vehicle)/10, 2)

               wilaya = wilaya

               wilaya_score, created = WilayaScore.objects.get_or_create(
                   wilaya=wilaya,
                   defaults={
                       'score': score,
                   }
               )
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found at path'))
