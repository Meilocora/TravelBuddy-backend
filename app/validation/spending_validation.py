import locale
from app.validation.validation import Validation

locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')

class SpendingValidation(Validation):
  def __init__(self):
    super().__init__()
    
  
  @staticmethod
  def validate_spending(spending):
        errors = False
        
        for key, value in spending.items():
            if value['value'] == "" or value['value'] == None or value['value'] == 0:
                spending[key]['errors'].append(f'Input is required')
                spending[key]['isValid'] = False
                 
        name_val = SpendingValidation().validate_string(spending['name']['value'], min_length=3, max_length=50)
        if name_val:
            spending['name']['errors'].append(f", {name_val}")
            spending['name']['isValid'] = False
          
        money_val = SpendingValidation().validate_amount(spending['amount']['value'])
        if money_val:
            spending['amount']['errors'].append(f", {money_val}")
            spending['amount']['isValid'] = False
        
        date_val = SpendingValidation().validate_date(spending['date']['value'])
        if date_val:
            spending['date']['errors'].append(f", {date_val}")
            spending['date']['isValid'] = False
                
        category_val = SpendingValidation().validate_spendings_category(spending['category']['value'])
        if category_val:
            spending['category']['errors'].append(f", {category_val}")
            spending['category']['isValid'] = False
                        
        for key, value in spending.items():
            if 'errors' in value and value['errors']:
                errors = True
                break
        
     
        return spending, not errors
    