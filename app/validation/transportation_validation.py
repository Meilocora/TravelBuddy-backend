import locale
from app.validation.validation import Validation

locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')

class TransportationValidation(Validation):
  def __init__(self):
    super().__init__()
    
  
  @staticmethod
  def validate_transportation(transportation):
        errors = False
            
        for key, value in transportation.items():
            if key != 'transportation_costs' and key != 'link' and key != 'departure_latitude' and key != 'departure_longitude' and key != 'arrival_latitude' and key != 'arrival_longitude' and key != 'unconvertedAmount':
                if value['value'] == "" or value['value'] == None:
                    transportation[key]['errors'].append(f'Input is required')
                    transportation[key]['isValid'] = False
                 
        type_val = TransportationValidation().validate_transportation_type(transportation['type']['value'])
        if type_val:
            transportation['type']['errors'].append(f", {type_val}")
            transportation['type']['isValid'] = False
           
        place_departurte_val = TransportationValidation().validate_string(transportation['place_of_departure']['value'], min_length=0, max_length=50)
        if place_departurte_val:
            transportation['place_of_departure']['errors'].append(f", {place_departurte_val}")
            transportation['place_of_departure']['isValid'] = False
            
        coordinated_departure_val = TransportationValidation().validate_coordinates(transportation['departure_latitude'], transportation['departure_longitude'])

        if coordinated_departure_val:
            transportation['place_of_departure']['errors'].append(f", {coordinated_departure_val}")
            transportation['place_of_departure']['isValid'] = False
            transportation['departure_latitude']['isValid'] = False
            
        place_arrival_val = TransportationValidation().validate_string(transportation['place_of_arrival']['value'], min_length=0, max_length=50)
        if place_arrival_val:
            transportation['place_of_arrival']['errors'].append(f", {place_arrival_val}")
            transportation['place_of_arrival']['isValid'] = False
          
        coordinated_arrival_val = TransportationValidation().validate_coordinates(transportation['arrival_latitude'], transportation['arrival_longitude'])
        if coordinated_arrival_val:
            transportation['place_of_arrival']['errors'].append(f", {coordinated_arrival_val}")
            transportation['place_of_arrival']['isValid'] = False
            transportation['arrival_latitude']['isValid'] = False
          
        start_val = TransportationValidation().validate_date_time(transportation['start_time']['value'])
        if start_val:
            transportation['start_time']['errors'].append(f", {start_val}")
            transportation['start_time']['isValid'] = False
            
        arrival_val = TransportationValidation().validate_date_time(transportation['arrival_time']['value'])
        if arrival_val:
            transportation['arrival_time']['errors'].append(f", {arrival_val}")
            transportation['arrival_time']['isValid'] = False
        
        start_end_val = TransportationValidation().compare_date_times(transportation['start_time']['value'], transportation['arrival_time']['value'])
        if start_end_val:
            transportation['start_time']['errors'].append(f", {start_end_val}")
            transportation['start_time']['isValid'] = False
                
        money_val = TransportationValidation().validate_amount(transportation['transportation_costs']['value'])
        if money_val:
            transportation['transportation_costs']['errors'].append(f", {money_val}")
            transportation['transportation_costs']['isValid'] = False
        
        if transportation['link']['value'] != "":
            link_val = TransportationValidation().validate_hyperlink(transportation['link']['value'])
            if link_val:
                transportation['link']['errors'].append(f", {link_val}")
                transportation['link']['isValid'] = False
            
            
        for key, value in transportation.items():
            if 'errors' in value and value['errors']:
                errors = True
                break
        
     
        return transportation, not errors
    