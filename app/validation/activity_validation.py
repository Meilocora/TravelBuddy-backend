import locale
from app.validation.validation import Validation

locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')

class ActivityValidation(Validation):
  def __init__(self):
    super().__init__()
    
  
  @staticmethod
  def validate_activity(activity):
        errors = False
                            
        try:
            if activity['name']['value'] == "" or activity['name']['value'] == None:
                activity['name']['errors'].append(f'Input is required')
                activity['name']['isValid'] = False  
                errors = True                
                return activity, not errors
        except KeyError:
            activity['name']['errors'].append(f'Input is required')
            activity['name']['isValid'] = False   
            errors = True
            return activity, not errors
        
        name_val = ActivityValidation().validate_string(activity['name']['value'], min_length=3, max_length=50)
        if name_val:
            activity['name']['errors'].append(f", {name_val}")
            activity['name']['isValid'] = False
          
        if activity['description']['value'] != "": 
            description_val = ActivityValidation().validate_string(activity['description']['value'], min_length=0, max_length=250)
            if description_val:
                activity['description']['errors'].append(f", {description_val}")
                activity['description']['isValid'] = False
        
        if activity['place']['value'] != "": 
            place_val = ActivityValidation().validate_string(activity['place']['value'], min_length=3, max_length=50)
            if place_val:
                activity['place']['errors'].append(f", {place_val}")
                activity['place']['isValid'] = False
        
        
        if activity['costs']['value'] != "": 
            money_val = ActivityValidation().validate_amount(activity['costs']['value'])
            if money_val:
                activity['costs']['errors'].append(f", {money_val}")
                activity['costs']['isValid'] = False
        
        if activity['link']['value'] != "":
            link_val = ActivityValidation().validate_hyperlink(activity['link']['value'])
            if link_val:
                activity['link']['errors'].append(f", {link_val}")
                activity['link']['isValid'] = False
            
            
        for key, value in activity.items():
            if 'errors' in value and value['errors']:
                errors = True
                break
        
     
        return activity, not errors
    