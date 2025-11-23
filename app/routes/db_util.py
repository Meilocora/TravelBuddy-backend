from db import db
from app.models import Journey, Costs, Spendings, MajorStage, MinorStage, CustomCountry, JourneysCustomCountriesLink, Transportation, Accommodation, Activity, PlaceToVisit
from app.routes.util import formatDateToString, formatDateTimeToString
from app.routes.util import calculate_time_zone_offset


def fetch_journeys(current_user):
    try:    
        # Get all the journeys from the database
        result = db.session.execute(db.select(Journey).filter_by(user_id=current_user).order_by(Journey.scheduled_start_time))
        journeys = result.scalars().all()
                
        # Fetch costs and major_stages for each journey
        journeys_list = []
        for journey in journeys:
            costs_result = db.session.execute(db.select(Costs).filter_by(journey_id=journey.id))
            costs = costs_result.scalars().first()
            spendings = db.session.execute(db.select(Spendings).filter_by(costs_id=costs.id)).scalars().all()
            
            majorStages = db.session.execute(db.select(MajorStage).filter_by(journey_id=journey.id)).scalars().all()
            
            # Append the whole journey, that matches the model from frontend to the list
            journey_data = {
                'id': journey.id,
                'name': journey.name,
                'description': journey.description,
                'costs': {
                    'budget': costs.budget,
                    'spent_money': costs.spent_money,
                    'money_exceeded': costs.money_exceeded,
                    'spendings': [{'id': spending.id, 'name': spending.name, 'amount': spending.amount, 'date': formatDateToString(spending.date), 'category': spending.category} for spending in spendings]
                },
                'scheduled_start_time': formatDateToString(journey.scheduled_start_time),
                'scheduled_end_time': formatDateToString(journey.scheduled_end_time),
            }
            
            custom_countries = fetch_custom_countries(current_user=current_user, journeyId=journey.id)
            if not isinstance(custom_countries, Exception):
                journey_data['countries'] = custom_countries
            else:
                return custom_countries
            
            if majorStages is not None:
                major_stages_list = fetch_major_stages(current_user, journey.id)
                if not isinstance(major_stages_list, Exception):
                  journey_data['majorStages'] = major_stages_list
                else:
                  return major_stages_list
            
            journeys_list.append(journey_data)
        
        return journeys_list
    except Exception as e:
        return e


def fetch_custom_countries(current_user, journeyId):
    try:        
        links = db.session.execute(db.select(JourneysCustomCountriesLink).filter_by(journey_id=journeyId)).scalars().all()
        countryIds = [link.custom_country_id for link in links]
                
        custom_countries = []
                
        for countryId in countryIds:
            custom_country = CustomCountry.query.filter_by(id=countryId).order_by(CustomCountry.name).first()
            custom_countries.append(custom_country)
        
        response_custom_countries = []
        
        for custom_country in custom_countries:    
            places_to_visit = []   
            placesToVisit = PlaceToVisit.query.filter_by(custom_country_id=custom_country.id).all()
            if placesToVisit is not None: 
                places = [{'id': place.id, 'name': place.name, 'description': place.description, 'visited': place.visited, 'favorite': place.favorite, 'link': place.link} for place in placesToVisit]
                places_to_visit += places
            
            response_custom_countries.append({'id': custom_country.id,
                                              'name': custom_country.name,
                                              'code': custom_country.code,
                                              'timezones': custom_country.timezones.split(',') if custom_country.timezones else None, 
                                              'currencies': custom_country.currencies.split(',') if custom_country.currencies else None,
                                              'languages': custom_country.languages.split(',') if custom_country.languages else None,
                                              'capital': custom_country.capital,
                                              'population': custom_country.population,
                                              'region': custom_country.region,
                                              'subregion': custom_country.subregion,
                                              'wiki_link': custom_country.wiki_link, 
                                              'visited': custom_country.visited,
                                              'visum_regulations': custom_country.visum_regulations,
                                                'best_time_to_visit': custom_country.best_time_to_visit,
                                                'general_information': custom_country.general_information,
                                                'placesToVisit': places_to_visit
                                              })
        
        return response_custom_countries
    except Exception as e:
        return e


def fetch_major_stages(current_user, journeyId):
    try:
        # Get all the major stages from the database
        result = db.session.execute(db.select(MajorStage).filter_by(journey_id=journeyId).order_by(MajorStage.position))
        majorStages = result.scalars().all()
        
        # Fetch costs, transportation and minor_stages for each major_stage
        major_stages_list = []
        for majorStage in majorStages:
            costs_result = db.session.execute(db.select(Costs).filter_by(major_stage_id=majorStage.id))
            costs = costs_result.scalars().first()
            
            transportation_result = db.session.execute(db.select(Transportation).filter_by(major_stage_id=majorStage.id))
            transportation = transportation_result.scalars().first()
            
            minorStages = db.session.execute(db.select(MinorStage).filter_by(major_stage_id=majorStage.id)).scalars().all()
    
                        
            # Append the whole major stage, that matches the model from frontend to the list
            major_stage_data = {
                'id': majorStage.id,
                'title': majorStage.title,
                'country': majorStage.country,
                'position': majorStage.position,
                'scheduled_start_time': formatDateToString(majorStage.scheduled_start_time),
                'scheduled_end_time': formatDateToString(majorStage.scheduled_end_time),
                'additional_info': majorStage.additional_info,
                'costs': {
                    'budget': costs.budget,
                    'spent_money': costs.spent_money,
                    'money_exceeded': costs.money_exceeded,
                }
            }
            
            
            custom_country = fetch_custom_country(current_user=current_user, countryName=majorStage.country)
            if not isinstance(custom_country, Exception):
                major_stage_data['country'] = custom_country
            else:
                return custom_country
            
            if transportation is not None:
                start_time_offset = calculate_time_zone_offset(transportation.departure_latitude, transportation.departure_longitude)
                arrival_time_offset = calculate_time_zone_offset(transportation.arrival_latitude, transportation.arrival_longitude)
                
                major_stage_data['transportation'] = {
                    'id': transportation.id,
                    'type': transportation.type,
                    'start_time': formatDateTimeToString(transportation.start_time),
                    'start_time_offset': start_time_offset,
                    'arrival_time': formatDateTimeToString(transportation.arrival_time),
                    'arrival_time_offset': arrival_time_offset,
                    'place_of_departure': transportation.place_of_departure,
                    'departure_latitude': transportation.departure_latitude,
                    'departure_longitude': transportation.departure_longitude,
                    'place_of_arrival': transportation.place_of_arrival,
                    'arrival_latitude': transportation.arrival_latitude,
                    'arrival_longitude': transportation.arrival_longitude,
                    'transportation_costs': transportation.transportation_costs,
                    'link': transportation.link,
                }
                
            
            if minorStages is not None:
                minor_stages_list = fetch_minor_stages(majorStage.id)
                if not isinstance(minor_stages_list, Exception):
                  major_stage_data['minorStages'] = minor_stages_list
                else:
                  return minor_stages_list
                            
            major_stages_list.append(major_stage_data)
        
        return major_stages_list
    except Exception as e:
        return e
    
def fetch_custom_country(current_user, countryName):
    try:        
        custom_country = db.session.execute(db.select(CustomCountry).filter_by(user_id=current_user, name=countryName)).scalars().first()
        
        places_to_visit = []   
        placesToVisit = PlaceToVisit.query.filter_by(custom_country_id=custom_country.id).all()
        if placesToVisit is not None: 
            places = [{'id': place.id, 'name': place.name, 'description': place.description, 'visited': place.visited, 'favorite': place.favorite, 'link': place.link} for place in placesToVisit]
            places_to_visit += places
            
        response_custom_country = {'id': custom_country.id,
                                            'name': custom_country.name,
                                            'code': custom_country.code,
                                            'timezones': custom_country.timezones.split(',') if custom_country.timezones else None, 
                                            'currencies': custom_country.currencies.split(',') if custom_country.currencies else None,
                                            'languages': custom_country.languages.split(',') if custom_country.languages else None,
                                            'capital': custom_country.capital,
                                            'population': custom_country.population,
                                            'region': custom_country.region,
                                            'subregion': custom_country.subregion,
                                            'wiki_link': custom_country.wiki_link, 
                                            'visited': custom_country.visited,
                                            'visum_regulations': custom_country.visum_regulations,
                                            'best_time_to_visit': custom_country.best_time_to_visit,
                                            'general_information': custom_country.general_information,
                                            'placesToVisit': places_to_visit
                                            }
        
        return response_custom_country
    except Exception as e:
        return e
      
      
def fetch_minor_stages(majorStageId):
    try:
        # Get all the minor stages from the database
        result = db.session.execute(db.select(MinorStage).filter_by(major_stage_id=majorStageId).order_by(MinorStage.position))
        minorStages = result.scalars().all()
                
        # Fetch costs, transportation, accommodation, activities and places_to_visit for each minor_stage
        minor_stages_list = []
        for minorStage in minorStages:
            costs_result = db.session.execute(db.select(Costs).filter_by(minor_stage_id=minorStage.id))
            costs = costs_result.scalars().first()
            spendings = db.session.execute(db.select(Spendings).filter_by(costs_id=costs.id).order_by(Spendings.date)).scalars().all()
            
            transportation = db.session.execute(db.select(Transportation).filter_by(minor_stage_id=minorStage.id)).scalars().first()
            accommodation = db.session.execute(db.select(Accommodation).filter_by(minor_stage_id=minorStage.id)).scalars().first()          
            activities = db.session.execute(db.select(Activity).filter_by(minor_stage_id=minorStage.id)).scalars().all()
            places_to_visit = minorStage.places_to_visit
                                           
            # Append the whole minor stage, that matches the model from frontend to the list
            minor_stage_data = {
                'id': minorStage.id,
                'title': minorStage.title,
                'scheduled_start_time': formatDateToString(minorStage.scheduled_start_time),
                'scheduled_end_time': formatDateToString(minorStage.scheduled_end_time),
                'position': minorStage.position,
                'costs': {
                    'budget': costs.budget,
                    'spent_money': costs.spent_money,
                    'money_exceeded': costs.money_exceeded,
                },
                'accommodation': {
                                    'place': accommodation.place,
                                    'costs': accommodation.costs,
                                    'booked': accommodation.booked,
                                    'latitude': accommodation.latitude if accommodation.latitude else None,
                                    'longitude': accommodation.longitude if accommodation.longitude else None,
                                    'link': accommodation.link,
                                }
            }
            
            if transportation is not None:
                start_time_offset = calculate_time_zone_offset(transportation.departure_latitude, transportation.departure_longitude)
                arrival_time_offset = calculate_time_zone_offset(transportation.arrival_latitude, transportation.arrival_longitude)
                
                minor_stage_data['transportation'] = {
                    'id': transportation.id,
                    'type': transportation.type,
                    'start_time': formatDateTimeToString(transportation.start_time),
                    'start_time_offset': start_time_offset,
                    'arrival_time': formatDateTimeToString(transportation.arrival_time),
                    'arrival_time_offset': arrival_time_offset,
                    'place_of_departure': transportation.place_of_departure,
                    'departure_latitude': transportation.departure_latitude,
                    'departure_longitude': transportation.departure_longitude,
                    'place_of_arrival': transportation.place_of_arrival,
                    'arrival_latitude': transportation.arrival_latitude,
                    'arrival_longitude': transportation.arrival_longitude,
                    'transportation_costs': transportation.transportation_costs,
                    'link': transportation.link,
                }
                
            if spendings is not None:
                minor_stage_data['costs']['spendings'] = [{'id': spending.id, 'name': spending.name, 'amount': spending.amount, 'date': formatDateToString(spending.date), 'category': spending.category} for spending in spendings]
                        
            if activities is not None:
                minor_stage_data['activities'] = [{'id': activity.id, 'name': activity.name, 'description': activity.description, 'costs': activity.costs, 'booked': activity.booked, 'place': activity.place, 'latitude': activity.latitude, 'longitude': activity.longitude ,'link': activity.link} for activity in activities]
            
            if places_to_visit is not None:
                minor_stage_data['placesToVisit'] = [{'countryId': place_to_visit.custom_country_id ,'id': place_to_visit.id, 'name': place_to_visit.name, 'description': place_to_visit.description, 'visited': place_to_visit.visited, 'favorite': place_to_visit.favorite, 'latitude': place_to_visit.latitude, 'longitude': place_to_visit.longitude, 'link': place_to_visit.link} for place_to_visit in places_to_visit]
            
            minor_stages_list.append(minor_stage_data)
        
        return minor_stages_list
    except Exception as e:
        return e


def adjust_stages_orders(other_stages, new_order, old_order=None):    
    for stage in other_stages:
        if old_order is None:   
            if stage.position >= new_order:
                stage.position = stage.position + 1
        elif old_order < new_order:
            if stage.position > old_order and stage.position <= new_order:
                stage.position = stage.position - 1
        elif old_order > new_order:
            if stage.position < old_order and stage.position >= new_order:
                stage.position = stage.position + 1
        db.session.commit()