from app.validation.validation import Validation
from app.routes.util import get_all_currencies

class CurrencyValidation(Validation):
  def __init__(self):
    super().__init__()
    
  
  @staticmethod
  def validate_currency(currency):
        errors = False
      
        for key, value in currency.items():
            if value['value'] == "" or value['value'] == None:
                currency[key]['errors'].append(f'Input is required')
                currency[key]['isValid'] = False         
            
        code_val = CurrencyValidation().validate_string(currency['code']['value'], min_length=1, max_length=6)
        if code_val:
            currency['code']['errors'].append(f", {code_val}")
            currency['code']['isValid'] = False
        
        name_val = CurrencyValidation().validate_string(currency['name']['value'], min_length=3, max_length=20)
        if name_val:
            currency['name']['errors'].append(f", {name_val}")
            currency['name']['isValid'] = False
            
        symbol_val = CurrencyValidation().validate_string(currency['symbol']['value'], min_length=1, max_length=6)
        if symbol_val:
            currency['symbol']['errors'].append(f", {symbol_val}")
            currency['symbol']['isValid'] = False
            
        conversion_rate_val = CurrencyValidation().validate_amount(currency['conversionRate']['value'])
        if conversion_rate_val:
            currency['conversionRate']['errors'].append(f", {conversion_rate_val}")
            currency['conversionRate']['isValid'] = False
            
        for key, value in currency.items():
            if 'errors' in value and value['errors']:
                errors = True
                break
        
        return currency, not errors
