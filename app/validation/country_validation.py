from app.validation.validation import Validation

class CountryValidation(Validation):
  def __init__(self):
    super().__init__()
    
  
  @staticmethod
  def validate_custom_country_update(country):
        errors = False
      
        if CountryValidation().validate_string(country['visum_regulations']['value'], min_length=0, max_length=100):
            country['visum_regulations']['errors'].append(f", {CountryValidation().validate_string(country['visum_regulations']['value'], 0, 100)}")
            country['visum_regulations']['isValid'] = False
            
        if CountryValidation().validate_string(country['best_time_to_visit']['value'], min_length=0, max_length=50):
            country['best_time_to_visit']['errors'].append(f", {CountryValidation().validate_string(country['best_time_to_visit']['value'], 0, 50)}")
            country['best_time_to_visit']['isValid'] = False
            
        if CountryValidation().validate_string(country['general_information']['value'], min_length=0, max_length=300):
            country['general_information']['errors'].append(f", {CountryValidation().validate_string(country['general_information']['value'], 0, 300)}")
            country['general_information']['isValid'] = False
            
            
        for key, value in country.items():
            if 'errors' in value and value['errors']:
                errors = True
                break
        
     
        return country, not errors   
