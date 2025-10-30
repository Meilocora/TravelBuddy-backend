from flask import Blueprint, jsonify, request
from app.routes.db_util import adjust_minor_stages_orders, adjust_stages_orders
from db import db
from app.routes.route_protection import token_required
from app.routes.util import get_users_stages_titles, parseDate, formatDateToString, parseDateTime, formatDateTimeToString
from app.models import Costs, Spendings, MajorStage, MinorStage, Transportation, Accommodation, Activity, PlaceToVisit
from app.validation.minor_stage_validation import MinorStageValidation
from app.routes.util import calculate_journey_costs

minor_stage_bp = Blueprint('minor_stage', __name__)
  

@minor_stage_bp.route('/create-minor-stage/<int:majorStageId>', methods=['POST'])
@token_required
def create_minor_stage(current_user, majorStageId):    
    try:
        minor_stage = request.get_json()
        result = db.session.execute(db.select(MinorStage).filter_by(major_stage_id=majorStageId))
        existing_minor_stages = result.scalars().all()
        assigned_titles = get_users_stages_titles(current_user)
        
        existing_minor_stages_costs = []
        for stage in existing_minor_stages:
            existing_minor_stages_costs.append(db.session.execute(db.select(Costs).filter_by(minor_stage_id=stage.id)).scalars().first())
                
        major_stage_costs = db.session.execute(db.select(Costs).filter_by(major_stage_id=majorStageId)).scalars().first()

        journey_id = db.session.execute(db.select(MajorStage).filter_by(id=majorStageId)).scalars().first().journey_id
        journey_costs = db.session.execute(db.select(Costs).filter_by(journey_id=journey_id)).scalars().first()
        
    except:
        return jsonify({'error': 'Unknown error'}, 400) 
    
    response, isValid = MinorStageValidation.validate_minor_stage(minor_stage, existing_minor_stages, existing_minor_stages_costs, major_stage_costs, assigned_titles)  
    
    if not isValid:
        return jsonify({'minorStageFormValues': response, 'status': 400})
    
    try:
         # Adjust orders of existing major stages if necessary
        if int(minor_stage['order']['value']) <= len(existing_minor_stages):
            adjust_stages_orders(existing_minor_stages, int(minor_stage['order']['value']))

        # Create a new minor stage
        new_minor_stage = MinorStage(
            title=minor_stage['title']['value'],
            scheduled_start_time=parseDate(minor_stage['scheduled_start_time']['value']),
            scheduled_end_time=parseDate(minor_stage['scheduled_end_time']['value']),
            order=minor_stage['order']['value'],
            major_stage_id=majorStageId
        )
        db.session.add(new_minor_stage)
        db.session.commit()
        
        
         # Remove line breaks from the name
        clean_place = minor_stage['accommodation_place']['value'].replace('\n', ' ').replace('\r', ' ')
         # Create a new accommodation for the minor stage
        new_accommodation = Accommodation(
            place=clean_place,
            costs=minor_stage['accommodation_costs']['value'],
            booked=minor_stage['accommodation_booked']['value'],
            latitude=minor_stage.get('accommodation_latitude', {}).get('value', None),
            longitude=minor_stage.get('accommodation_longitude', {}).get('value', None),
            link=minor_stage['accommodation_link']['value'],
            minor_stage_id=new_minor_stage.id
        )
        db.session.add(new_accommodation)
        db.session.commit()
                
        # Create a new costs for the minor stage
        costs = Costs(
            minor_stage_id=new_minor_stage.id,
            budget=minor_stage['budget']['value'],
            spent_money=0,
            money_exceeded=False
        )
        db.session.add(costs)
        db.session.commit()
        
        calculate_journey_costs(journey_costs)
                
        # build response major stage object for the frontend
        response_minor_stage = {'id': new_minor_stage.id,
                                'title': new_minor_stage.title,
                                'scheduled_start_time': formatDateToString(new_minor_stage.scheduled_start_time),
                                'scheduled_end_time': formatDateToString(new_minor_stage.scheduled_end_time),
                                'order': new_minor_stage.order,
                                'costs': {
                                    'budget': costs.budget,
                                    'spent_money': costs.spent_money,
                                    'money_exceeded': costs.money_exceeded
                                },  
                                'accommodation': {
                                    'place': new_accommodation.place,
                                    'costs': new_accommodation.costs,
                                    'booked': new_accommodation.booked,
                                    'latitude': new_accommodation.latitude if new_accommodation.latitude else None,
                                    'longitude': new_accommodation.longitude if new_accommodation.longitude else None,
                                    'link': new_accommodation.link,
                                }
        }
        
        return jsonify({'minorStage': response_minor_stage,'status': 201})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)
    
    
@minor_stage_bp.route('/update-minor-stage/<int:majorStageId>/<int:minorStageId>', methods=['POST'])
@token_required
def update_minor_stage(current_user, majorStageId, minorStageId):
    try:
        minor_stage = request.get_json()
        result = db.session.execute(db.select(MinorStage).filter(MinorStage.id!=minorStageId, MinorStage.major_stage_id==majorStageId))
        existing_minor_stages = result.scalars().all()
        old_minor_stage = db.get_or_404(MinorStage, minorStageId)
        assigned_titles = get_users_stages_titles(current_user)
        
        existing_minor_stages_costs = []
        for stage in existing_minor_stages:
            existing_minor_stages_costs.append(db.session.execute(db.select(Costs).filter_by(minor_stage_id=stage.id)).scalars().first())
        
        major_stage_costs = db.session.execute(db.select(Costs).filter_by(major_stage_id=majorStageId)).scalars().first()

        journey_id = db.session.execute(db.select(MajorStage).filter_by(id=majorStageId)).scalars().first().journey_id
        journey_costs = db.session.execute(db.select(Costs).filter_by(journey_id=journey_id)).scalars().first()
        
    except:
        return jsonify({'error': 'Unknown error'}, 400) 
    
    response, isValid = MinorStageValidation.validate_minor_stage(minor_stage, existing_minor_stages, existing_minor_stages_costs, major_stage_costs, assigned_titles, old_minor_stage)

    if not isValid:
        return jsonify({'minorStageFormValues': response, 'status': 400})

    money_exceeded = float(response['budget']['value']) < float(response['spent_money']['value'])

    spendings = db.session.execute(db.select(Spendings).join(Costs).filter(Costs.minor_stage_id == minorStageId)).scalars().all()
    transportation = db.session.execute(db.select(Transportation).filter_by(minor_stage_id=minorStageId)).scalars().first()
    places_to_visit = db.session.execute(db.select(PlaceToVisit).filter_by(minor_stage_id=minorStageId)).scalars().all()
    activities = db.session.execute(db.select(Activity).filter_by(minor_stage_id=minorStageId)).scalars().all()
    
    
    try:
        # Adjust orders of existing minor stages if necessary
        adjust_stages_orders(existing_minor_stages, minor_stage['order']['value'], old_minor_stage.order)

        # Update the minor stage
        db.session.execute(db.update(MinorStage).where(MinorStage.id == minorStageId).values(
            title=minor_stage['title']['value'],
            scheduled_start_time=parseDate(minor_stage['scheduled_start_time']['value']),
            scheduled_end_time=parseDate(minor_stage['scheduled_end_time']['value']),
            order=minor_stage['order']['value']
        ))
        db.session.commit()
                
        # Remove line breaks from the name
        clean_place = minor_stage['accommodation_place']['value'].replace('\n', ' ').replace('\r', ' ')
         # Update the accommodation for the minor stage
        db.session.execute(db.update(Accommodation).where(Accommodation.minor_stage_id == minorStageId).values(
            place=clean_place,
            costs=minor_stage['accommodation_costs']['value'],
            booked=minor_stage['accommodation_booked']['value'],
            latitude=minor_stage.get('accommodation_latitude', {}).get('value', None),
            longitude=minor_stage.get('accommodation_longitude', {}).get('value', None),
            link=minor_stage['accommodation_link']['value'],
            minor_stage_id=minorStageId
        ))
        db.session.commit()
        
        # Update the costs for the minor stage
        db.session.execute(db.update(Costs).where(Costs.minor_stage_id == minorStageId).values(
            budget=minor_stage['budget']['value'],
            spent_money=minor_stage['spent_money']['value'],
            money_exceeded=money_exceeded,
        ))
        db.session.commit()
        
        calculate_journey_costs(journey_costs)
        
        # build response minor stage object for the frontend
        response_minor_stage = {'id': minorStageId,
                                'title': minor_stage['title']['value'],
                                'scheduled_start_time': minor_stage['scheduled_start_time']['value'],
                                'scheduled_end_time': minor_stage['scheduled_end_time']['value'],
                                'order': minor_stage['order']['value'],
                                'costs': {
                                    'budget': minor_stage['budget']['value'],
                                    'spent_money': minor_stage['spent_money']['value'],
                                    'money_exceeded': money_exceeded
                                },  
                                'accommodation': {
                                    'place': minor_stage['accommodation_place']['value'],
                                    'costs': minor_stage['accommodation_costs']['value'],
                                    'booked': minor_stage['accommodation_booked']['value'],
                                    'latitude': minor_stage.get('accommodation_latitude', {}).get('value', None),
                                    'longitude': minor_stage.get('accommodation_latitude', {}).get('value', None),
                                    'link': minor_stage['accommodation_link']['value'],
                                }
        }
        
                
        if transportation is not None:
            response_minor_stage['transportation'] = {
                  'type': transportation.type,
                    'start_time': formatDateTimeToString(transportation.start_time),
                    'arrival_time': formatDateTimeToString(transportation.arrival_time),
                    'place_of_departure': transportation.place_of_departure,
                    'departure_latitude': transportation.departure_latitude if transportation.departure_latitude else None,
                    'departure_longitude': transportation.departure_longitude if transportation.departure_longitude else None,
                    'place_of_arrival': transportation.place_of_arrival,
                    'arrival_latitude': transportation.arrival_latitude if transportation.arrival_latitude else None,
                    'arrival_longitude': transportation.arrival_longitude if transportation.arrival_longitude else None,
                    'transportation_costs': transportation.transportation_costs,
                    'link': transportation.link,
                }
                
        if spendings is not None:
            response_minor_stage['costs']['spendings'] = [{'name': spending.name, 'amount': spending.amount, 'date': formatDateToString(spending.date), 'category': spending.category} for spending in spendings]
            
        if activities is not None:
            response_minor_stage['activities'] = [{'id': activity.id, 'name': activity.name, 'description': activity.description, 'costs': activity.costs, 'booked': activity.booked, 'place': activity.place, 'latitude': activity.latitude, 'longitude': activity.longitude ,'link': activity.link} for activity in activities]
            
        if places_to_visit is not None:
                response_minor_stage['placesToVisit'] = [{'countryId': place_to_visit.custom_country_id ,'id': place_to_visit.id, 'name': place_to_visit.name, 'description': place_to_visit.description, 'visited': place_to_visit.visited, 'favorite': place_to_visit.favorite, 'latitude': place_to_visit.latitude, 'longitude': place_to_visit.longitude, 'link': place_to_visit.link} for place_to_visit in places_to_visit]

        return jsonify({'minorStage': response_minor_stage,'status': 200})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)
    

@minor_stage_bp.route('/delete-minor-stage/<int:minorStageId>', methods=['DELETE'])
@token_required
def delete_minor_stage(current_user, minorStageId):
    major_stage_id = db.session.execute(db.select(MinorStage).filter_by(id=minorStageId)).scalars().first().major_stage_id
    major_stage = db.session.execute(db.select(MajorStage).filter_by(id=major_stage_id)).scalars().first()
    journey_id = major_stage.journey_id
    journey_costs = db.session.execute(db.select(Costs).filter_by(journey_id=journey_id)).scalars().first()
    try:        
        minor_stage = db.get_or_404(MinorStage, minorStageId)
        
        # Adjust orders of existing major stages if necessary
        if minor_stage.order < len(major_stage.minor_stages):
            later_minor_stages = [other_minor_stage for other_minor_stage in major_stage.minor_stages if other_minor_stage.order > minor_stage.order]
            adjust_stages_orders(later_minor_stages, 999, minor_stage.order)

        db.session.delete(minor_stage)
        db.session.commit()
        
        places_to_visit = db.session.execute(db.select(PlaceToVisit).filter_by(minor_stage_id=minorStageId)).scalars().all()
        for place in places_to_visit:
            place.minor_stage_id = None
            db.session.commit()
        
        calculate_journey_costs(journey_costs)
        
        return jsonify({'status': 200})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)


@minor_stage_bp.route('/swap-minor-stages', methods=['POST'])
@token_required
def swap_minor_stages(current_user):
    stagesOrderList = request.get_json()["stagesOrderList"]
    try:
        for item in stagesOrderList:
            db.session.execute(db.update(MinorStage).where(MinorStage.id == int(item['id'])).values(order=item['order']))
        db.session.commit()
        
        return jsonify({'status': 200})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)