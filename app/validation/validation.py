from datetime import datetime, date
import re

class Validation:
  def __init__(self):
    self.error_list = []
    self.current_date_string = datetime.now().strftime('%Y-%m-%d')
    
  def __return_feedback(self):    
    if len(self.error_list) == 0:
      return False
    elif len(self.error_list) == 1:
      return self.error_list[0]
    elif len(self.error_list) > 1:
      return ', '.join(self.error_list)
  
  
  def validate_string(self, value: str, min_length: int = 1, max_length: int = 250) -> bool | None:    
    if not value:
      return self.__return_feedback()
    elif len(value.strip()) < min_length:
      self.error_list.append(f'Min length is {min_length}')
    
    try:
      if len(value.strip()) > max_length:
        self.error_list.append(f'Max length is {max_length}')
    except AttributeError:
      pass
      
    return self.__return_feedback()
    
    
  def validate_date_time(self, value: str, min_date_time: str = None) -> bool | None:
    try:
      datetime.strptime(value, '%d.%m.%Y %H:%M')
    except (TypeError , ValueError):
      self.error_list.append('Required format: DD.MM.YYYY HH:MM')
    else:
      if not min_date_time:
        min_date_time = self.current_date_string
        
      if datetime.strptime(value, '%d.%m.%Y %H:%M') < datetime.strptime(min_date_time, '%d.%m.%Y %H:%M'):
        self.error_list.append("Can't be earlier than now")
    finally:
      return self.__return_feedback()
    
  
  def validate_date(self, value: str, min_date: str = None) -> bool | None:
    try:
      datetime.strptime(value, '%d.%m.%Y')
    except (TypeError , ValueError):
      # self.error_list.append('Wrong format')
      return self.__return_feedback()
    else:
      if not min_date:
        min_date = self.current_date_string
        
      if datetime.strptime(value, '%d.%m.%Y') < datetime.strptime(min_date, '%d.%m.%Y'):
        self.error_list.append("Can't be earlier than now")
    finally:
      return self.__return_feedback()
  
  
  def compare_date_times(self, start_date_time: str, end_date_time: str) -> bool | str:      
      try:
        datetime.strptime(start_date_time, '%d.%m.%Y %H:%M')
        datetime.strptime(end_date_time, '%d.%m.%Y %H:%M')
      except (TypeError , ValueError):
        return self.__return_feedback()
      else:
        if datetime.strptime(start_date_time, '%d.%m.%Y %H:%M') > datetime.strptime(end_date_time, '%d.%m.%Y %H:%M'):
          self.error_list.append("Can't be later than end date")
          
        return self.__return_feedback()
      
  def compare_dates(self, start_date: str, end_date: str) -> bool | str:
    try:
      datetime.strptime(start_date, '%d.%m.%Y')
      datetime.strptime(end_date, '%d.%m.%Y')
    except (TypeError , ValueError):
      return self.__return_feedback()
    else:
      if datetime.strptime(start_date, '%d.%m.%Y') > datetime.strptime(end_date, '%d.%m.%Y'):
        self.error_list.append("Can't be later than end date")
      
      return self.__return_feedback()
    
    
  def check_for_overlap(self, new_date: str, existing_start_date: date, existing_end_date: date, overlap_superior_name: str) -> bool:
    try:
      new_date = datetime.strptime(new_date, '%d.%m.%Y')
    except (TypeError , ValueError):
      # self.error_list.append('Error with overlap check occured')
      return self.__return_feedback()
    else:
      if new_date >= existing_start_date and new_date <= existing_end_date:
        self.error_list.append(f'Overlaps with "{overlap_superior_name}"')
    return self.__return_feedback()


  def check_for_inferior_collision(self, new_date: str, inferior_start_date: date, inferior_end_date: date, inferior_name: str) -> bool:
    try:
      new_date = datetime.strptime(new_date, '%d.%m.%Y')
    except (TypeError , ValueError):
      self.error_list.append('Error with inferior collision check occured')
    else:
      if new_date > inferior_start_date and new_date < inferior_end_date:
        self.error_list.append(f'Collides with "{inferior_name}"')
    return self.__return_feedback()


  def validate_amount(self, amount: float):
    try:
      amount = float(amount)
    except ValueError:
      self.error_list.append('Invalid amount format')
      return self.__return_feedback()
     
    if amount < 0:
      self.error_list.append('Amount cannot be negative')
    
    return self.__return_feedback()
  
  
  def validate_email(self, email:str):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    if(not re.fullmatch(regex, email)):
        self.error_list.append("Invalid Email")
    
    return self.__return_feedback()
  
  
  def validate_password(self, password:str, min_length:int = 6, max_length:int = 20):
    if len(password) < min_length:
      self.error_list.append(f'Min length is {min_length}')
      
    if len(password) > max_length:
      self.error_list.append(f'Max length is {max_length}')
      
    if(not re.match(r'(.*?[A-Z])', password)):
      self.error_list.append("Must contain one uppercase letter")
      
    if(not re.match(r'(.*?[a-z])', password)):
      self.error_list.append("Must contain one lowercase letter")
      
    if(not re.match(r'(.*?[0-9])', password)):
      self.error_list.append("Must contain one digit")
      
    if(not re.match(r"(.*?[!\?\(\)\[\]@#$%^&*])", password)):
      self.error_list.append("Must contain one special character")
    
    return self.__return_feedback()
  
  
  def validate_hyperlink(self, hyperlink:str):
    regex = r'(http|https)://[a-zA-Z0-9\-.]+\.[a-zA-Z]{2,}(\/\S*)?'
    if(not re.fullmatch(regex, hyperlink)):
        self.error_list.append("Invalid Hyperlink")
    
    return self.__return_feedback()
  
  
  def validate_spendings_category(self, category:str):
    if category not in ['Transportation', 'Acommodation', 'Activities', 'Dine out', 'Basic needs', 'Souvenirs', 'Other']:
      self.error_list.append('Invalid category')
    
    return self.__return_feedback()
  
  
  def validate_transportation_type(self, type:str):
    if type not in ['Bus', 'Car', 'Boat', 'Plane', 'Train', 'Other']:
      self.error_list.append('Invalid transportation type')      
    
    return self.__return_feedback()
  
  
  def validate_coordinates(self, latitude:str, longitude:str):
    try:
        lat = float(latitude['value'])
        lng = float(longitude['value'])
    except (TypeError, ValueError, KeyError):
        self.error_list.append('No location picked')
        
        return self.__return_feedback()
    return self.__return_feedback()