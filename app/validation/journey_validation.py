from datetime import datetime
from db import db
from app.validation.validation import Validation
from app.routes.util import parseDate

class JourneyValidation(Validation):
  def __init__(self):
    super().__init__()
    
  
  @staticmethod
  def validate_journey(journey, existing_journeys):
        errors = False
      
        for key, value in journey.items():
            if key != 'description':
                if value['value'] == "" or value['value'] == None:
                    journey[key]['errors'].append(f'Input is required')
                    journey[key]['isValid'] = False
            
        if len(journey['countries']['value']) == 0:
              journey['countries']['errors'].append(f'At least one country is required')
              journey['countries']['isValid'] = False    
              
        name_val = JourneyValidation().validate_string(journey['name']['value'], min_length=3, max_length=50)
        if name_val:
            journey['name']['errors'].append(f", {name_val}")
            journey['name']['isValid'] = False
            
        
        for existing_journey in existing_journeys:
            start_val = JourneyValidation().check_for_overlap(journey['scheduled_start_time']['value'], existing_journey.scheduled_start_time, existing_journey.scheduled_end_time, existing_journey.name)
            if start_val:   
                journey['scheduled_start_time']['errors'].append(f", {start_val}")             
                journey['scheduled_start_time']['isValid'] = False
                
            end_val = JourneyValidation().check_for_overlap(journey['scheduled_end_time']['value'], existing_journey.scheduled_start_time, existing_journey.scheduled_end_time, existing_journey.name)
            if end_val:
                journey['scheduled_end_time']['errors'].append(f", {end_val}")
                journey['scheduled_end_time']['isValid'] = False
                
        start_val = JourneyValidation().validate_date(journey['scheduled_start_time']['value'])
        if start_val:
            journey['scheduled_start_time']['errors'].append(f", {start_val}")
            journey['scheduled_start_time']['isValid'] = False
        
        end_val = JourneyValidation().validate_date(journey['scheduled_end_time']['value'])
        if end_val:
            journey['scheduled_end_time']['errors'].append(f", {end_val}")
            journey['scheduled_end_time']['isValid'] = False
            
        start_end_val = JourneyValidation().compare_dates(journey['scheduled_start_time']['value'], journey['scheduled_end_time']['value'])
        if start_end_val:
            journey['scheduled_start_time']['errors'].append(f", {start_end_val}")
            journey['scheduled_start_time']['isValid'] = False
            
        money_val = JourneyValidation().validate_amount(journey['budget']['value'])
        if money_val:
            journey['budget']['errors'].append(f", {money_val}")
            journey['budget']['isValid'] = False
            
            
        for key, value in journey.items():
            if 'errors' in value and value['errors']:
                errors = True
                break
        
     
        return journey, not errors
     
     
  @staticmethod
  def validate_journey_update(journey, existing_journeys, major_stages):
          errors = False
        
          for key, value in journey.items():
            if key != 'description':
                if value['value'] == "" or value['value'] == None:
                    journey[key]['errors'].append(f'Input is required')
                    journey[key]['isValid'] = False
            
            
          if len(journey['countries']['value']) == 0:
              journey['countries']['errors'].append(f'At least one country is required')
              journey['countries']['isValid'] = False    
              
          name_val = JourneyValidation().validate_string(journey['name']['value'], min_length=3) 
          if name_val:
              journey['name']['errors'].append(f", {name_val}")
              journey['name']['isValid'] = False
               
          for existing_journey in existing_journeys:
            start_val = JourneyValidation().check_for_overlap(journey['scheduled_start_time']['value'], existing_journey.scheduled_start_time, existing_journey.scheduled_end_time, existing_journey.name)
            if start_val:   
                journey['scheduled_start_time']['errors'].append(f", {start_val}")             
                journey['scheduled_start_time']['isValid'] = False
                
            end_val = JourneyValidation().check_for_overlap(journey['scheduled_end_time']['value'], existing_journey.scheduled_start_time, existing_journey.scheduled_end_time, existing_journey.name)
            if end_val:
                journey['scheduled_end_time']['errors'].append(f", {end_val}")
                journey['scheduled_end_time']['isValid'] = False


          for major_stage in major_stages:
            start_val = JourneyValidation().check_for_inferior_collision(journey['scheduled_start_time']['value'], major_stage.scheduled_start_time, major_stage.scheduled_end_time, major_stage.title)
            if start_val:   
                journey['scheduled_start_time']['errors'].append(f", {start_val}")             
                journey['scheduled_start_time']['isValid'] = False

            end_val = JourneyValidation().check_for_inferior_collision(journey['scheduled_end_time']['value'], major_stage.scheduled_start_time, major_stage.scheduled_end_time, major_stage.title)
            if end_val:
                journey['scheduled_end_time']['errors'].append(f", {end_val}")
                journey['scheduled_end_time']['isValid'] = False


          start_val = JourneyValidation().validate_date(journey['scheduled_start_time']['value'])
          if start_val:
              journey['scheduled_start_time']['errors'].append(f", {start_val}")
              journey['scheduled_start_time']['isValid'] = False
            
          end_val = JourneyValidation().validate_date(journey['scheduled_end_time']['value'])
          if end_val:
              journey['scheduled_end_time']['errors'].append(f", {end_val}")
              journey['scheduled_end_time']['isValid'] = False
                
          start_end_val = JourneyValidation().compare_dates(journey['scheduled_start_time']['value'], journey['scheduled_end_time']['value'])
          if start_end_val:
              journey['scheduled_start_time']['errors'].append(f", {start_end_val}")
              journey['scheduled_start_time']['isValid'] = False
                
          money_val = JourneyValidation().validate_amount(journey['budget']['value'])
          if money_val:
              journey['budget']['errors'].append(f", {money_val}")
              journey['budget']['isValid'] = False
                
                
          for key, value in journey.items():
              if 'errors' in value and value['errors']:
                  errors = True
                  break
            
        
          return journey, not errors
     
        
     
