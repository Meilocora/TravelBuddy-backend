from app.validation.validation import Validation

class PlaceValidation(Validation):
  def __init__(self):
    super().__init__()
    
  
  @staticmethod
  def validate_place(place):
        errors = False
      
        for key, value in place.items():
            if key != 'description' and key != 'link' and key != 'latitude' and key != 'longitude':
                try:
                    if value['value'] == "" or value['value'] == None:
                        place[key]['errors'].append(f'Input is required')
                        place[key]['isValid'] = False
                except KeyError:
                    place['name']['errors'].append(f", Inputs is required")
                    place['name']['isValid'] = False
                    errors = True
                    return place, not errors
        
        try: 
            place['latitude']['value']
            place['longitude']['value']
        except KeyError:
            place['name']['errors'].append(f", Select a location on the map")
            place['name']['isValid'] = False
            place['latitude']['isValid'] = False
        else: 
            pass            
            
            
        if PlaceValidation().validate_string(place['name']['value'], min_length=3, max_length=50):
            place['name']['errors'].append(f", {PlaceValidation().validate_string(place['name']['value'], 3, 50)}")
            place['name']['isValid'] = False
            
        if PlaceValidation().validate_string(place['description']['value'], min_length=0, max_length=100):
            place['description']['errors'].append(f", {PlaceValidation().validate_string(place['description']['value'], 0, 300)}")
            place['description']['isValid'] = False
            
        if PlaceValidation().validate_string(place['link']['value'], min_length=0, max_length=200):
            place['link']['errors'].append(f", {PlaceValidation().validate_string(place['link']['value'], 0, 200)}")
            place['link']['isValid'] = False
            
        for key, value in place.items():
            if 'errors' in value and value['errors']:
                errors = True
                break
        
     
        return place, not errors
