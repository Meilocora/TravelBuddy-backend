from flask import Blueprint, jsonify, request

from app.models import Costs, Journey, MajorStage, Transportation
from app.routes.resource_access import (
    get_user_major_stage,
    get_user_minor_stage,
    get_user_transportation,
)
from app.routes.route_protection import token_required
from app.routes.util import (
    calculate_journey_costs,
    formatDateTimeToString,
    parseDateTime,
)
from app.validation.transportation_validation import TransportationValidation
from db import db

transportation_bp = Blueprint('transportation', __name__)

@transportation_bp.route('/create-major-stage-transportation/<int:majorStageId>', methods=['POST'])
@token_required 
def create_major_stage_transportation(current_user, majorStageId):
    try:
        major_stage = get_user_major_stage(
            current_user,
            majorStageId
        )
        if major_stage is None:
            return jsonify({'error': 'Major stage not found'}), 404
        
        transportation = request.get_json()
        journey = db.get_or_404(Journey, major_stage.journey_id)
        journey_costs = db.session.execute(db.select(Costs).filter_by(journey_id=journey.id)).scalars().first()
         
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500
    
    response, isValid = TransportationValidation.validate_transportation(transportation)
    
    if not isValid:
        return jsonify({'transportationFormValues': response}), 400
    
    try:     
        # Remove line breaks from the name
        clean_place_of_departure = transportation['place_of_departure']['value'].replace('\n', ' ').replace('\r', ' ')
        clean_place_of_arrival = transportation['place_of_arrival']['value'].replace('\n', ' ').replace('\r', ' ')
        # Create a new transportation
        new_transportation = Transportation(
            type=transportation['type']['value'],
            start_time=parseDateTime(transportation['start_time']['value']),
            arrival_time=parseDateTime(transportation['arrival_time']['value']),
            place_of_departure=clean_place_of_departure,
            departure_latitude=transportation.get('departure_latitude', {}).get('value', None),
            departure_longitude=transportation.get('departure_longitude', {}).get('value', None),
            place_of_arrival=clean_place_of_arrival,
            arrival_latitude=transportation.get('arrival_latitude', {}).get('value', None),
            arrival_longitude=transportation.get('arrival_longitude', {}).get('value', None),
            transportation_costs=transportation['transportation_costs']['value'],
            link=transportation['link']['value'],
            major_stage_id=majorStageId
        )
        db.session.add(new_transportation)
        db.session.commit()
        
        calculate_journey_costs(journey_costs)
        
        # build response transportation object for the frontend
        response_transportation = {'id': new_transportation.id,
                                    'type': new_transportation.type,
                                    'start_time': formatDateTimeToString(new_transportation.start_time),
                                    'arrival_time': formatDateTimeToString(new_transportation.arrival_time),
                                    'place_of_departure': new_transportation.place_of_departure,
                                    'departure_latitude': new_transportation.departure_latitude if new_transportation.departure_latitude else None,
                                    'departure_longitude': new_transportation.departure_longitude if new_transportation.departure_longitude else None,
                                    'place_of_arrival': new_transportation.place_of_arrival,
                                    'arrival_latitude': new_transportation.arrival_latitude if new_transportation.arrival_latitude else None,
                                    'arrival_longitude': new_transportation.arrival_longitude if new_transportation.arrival_longitude else None,
                                    'transportation_costs': new_transportation.transportation_costs,
                                    'link': new_transportation.link}
        
        return jsonify({'transportation': response_transportation}), 201
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
@transportation_bp.route('/create-minor-stage-transportation/<int:minorStageId>', methods=['POST'])
@token_required 
def create_minor_stage_transportation(current_user, minorStageId):
    try:
        minor_stage = get_user_minor_stage(
            current_user,
            minorStageId
        )
        if minor_stage is None:
            return jsonify({'error': 'Minor stage not found'}), 404
                
        transportation = request.get_json()
        major_stage = db.get_or_404(MajorStage, minor_stage.major_stage_id)        
        journey = db.get_or_404(Journey, major_stage.journey_id)
        journey_costs = db.session.execute(db.select(Costs).filter_by(journey_id=journey.id)).scalars().first()
         
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    response, isValid = TransportationValidation.validate_transportation(transportation)
    
    if not isValid:
        return jsonify({'transportationFormValues': response}), 400
    
    try:
         # Remove line breaks from the name
        clean_place_of_departure = transportation['place_of_departure']['value'].replace('\n', ' ').replace('\r', ' ')
        clean_place_of_arrival = transportation['place_of_arrival']['value'].replace('\n', ' ').replace('\r', ' ')
        # Create a new transportation
        new_transportation = Transportation(
            type=transportation['type']['value'],
            start_time=parseDateTime(transportation['start_time']['value']),
            arrival_time=parseDateTime(transportation['arrival_time']['value']),
            place_of_departure=clean_place_of_departure,
            departure_latitude=transportation.get('departure_latitude', {}).get('value', None),
            departure_longitude=transportation.get('departure_longitude', {}).get('value', None),
            place_of_arrival=clean_place_of_arrival,
            arrival_latitude=transportation.get('arrival_latitude', {}).get('value', None),
            arrival_longitude=transportation.get('arrival_longitude', {}).get('value', None),
            transportation_costs=transportation['transportation_costs']['value'],
            link=transportation['link']['value'],
            minor_stage_id=minorStageId
        )
        db.session.add(new_transportation)
        db.session.commit()
        
        calculate_journey_costs(journey_costs)
        
        # build response transportation object for the frontend
        response_transportation = {'id': new_transportation.id,
                                    'type': new_transportation.type,
                                    'start_time': formatDateTimeToString(new_transportation.start_time),
                                    'arrival_time': formatDateTimeToString(new_transportation.arrival_time),
                                    'place_of_departure': new_transportation.place_of_departure,
                                    'departure_latitude': new_transportation.departure_latitude if new_transportation.departure_latitude else None,
                                    'departure_longitude': new_transportation.departure_longitude if new_transportation.departure_longitude else None,
                                    'place_of_arrival': new_transportation.place_of_arrival,
                                    'arrival_latitude': new_transportation.arrival_latitude if new_transportation.arrival_latitude else None,
                                    'arrival_longitude': new_transportation.arrival_longitude if new_transportation.arrival_longitude else None,
                                    'transportation_costs': new_transportation.transportation_costs,
                                    'link': new_transportation.link}
        
        return jsonify({'transportation': response_transportation, 'backendMajorStageId': major_stage.id}), 201
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    
@transportation_bp.route('/update-major-stage-transportation/<int:majorStageId>/<int:transportationId>', methods=['POST'])
@token_required 
def update_major_stage_transportation(current_user, majorStageId, transportationId):
    try:
        major_stage = get_user_major_stage(
            current_user,
            majorStageId
        )
        old_transportation = get_user_transportation(
            current_user,
            transportationId
        )
        
        if major_stage is None or old_transportation is None:
            return jsonify({'error': 'Resource not found'}), 404
        
        new_transportation = request.get_json()
        journey = db.get_or_404(Journey, major_stage.journey_id)
        journey_costs = db.session.execute(db.select(Costs).filter_by(journey_id=journey.id)).scalars().first()
         
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    response, isValid = TransportationValidation.validate_transportation(new_transportation)
    
    if not isValid:
        return jsonify({'transportationFormValues': response}), 400
    
    try:
         # Remove line breaks from the name
        clean_place_of_departure = new_transportation['place_of_departure']['value'].replace('\n', ' ').replace('\r', ' ')
        clean_place_of_arrival = new_transportation['place_of_arrival']['value'].replace('\n', ' ').replace('\r', ' ')
        # Update old transportation
        old_transportation.type = new_transportation['type']['value']
        old_transportation.start_time = parseDateTime(new_transportation['start_time']['value'])
        old_transportation.arrival_time = parseDateTime(new_transportation['arrival_time']['value'])
        old_transportation.place_of_departure = clean_place_of_departure
        old_transportation.departure_latitude = new_transportation.get('departure_latitude', {}).get('value', None)
        old_transportation.departure_longitude = new_transportation.get('departure_longitude', {}).get('value', None)
        old_transportation.place_of_arrival = clean_place_of_arrival
        old_transportation.arrival_latitude = new_transportation.get('arrival_latitude', {}).get('value', None)
        old_transportation.arrival_longitude = new_transportation.get('arrival_longitude', {}).get('value', None)
        old_transportation.transportation_costs = new_transportation['transportation_costs']['value']
        old_transportation.link = new_transportation['link']['value']
        db.session.commit()
        
        calculate_journey_costs(journey_costs)
        
        # build response transportation object for the frontend
        response_transportation = {'id': old_transportation.id,
                                    'type': new_transportation['type']['value'],
                                    'start_time': new_transportation['start_time']['value'],
                                    'arrival_time': new_transportation['arrival_time']['value'],
                                    'place_of_departure': new_transportation['place_of_departure']['value'],
                                    'departure_latitude': new_transportation['departure_latitude']['value'] if new_transportation['departure_latitude'] else None,
                                    'departure_longitude': new_transportation['departure_longitude']['value'] if new_transportation['departure_longitude'] else None,
                                    'place_of_arrival': new_transportation['place_of_arrival']['value'],
                                    'arrival_latitude': new_transportation['arrival_latitude']['value'] if new_transportation['arrival_latitude'] else None,
                                    'arrival_longitude': new_transportation['arrival_longitude']['value'] if new_transportation['arrival_longitude'] else None,
                                    'transportation_costs': new_transportation['transportation_costs']['value'],
                                    'link': new_transportation['link']['value']}

        return jsonify({'transportation': response_transportation}), 201
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
@transportation_bp.route('/update-minor-stage-transportation/<int:minorStageId>/<int:transportationId>', methods=['POST'])
@token_required 
def update_minor_stage_transportation(current_user, minorStageId, transportationId):
    try:
        old_transportation = get_user_transportation(
            current_user,
            transportationId,
            minor_stage_id=minorStageId,
        )
        
        if old_transportation is None:
            return jsonify({'error': 'Resource not found'}), 404
        
        
        new_transportation = request.get_json()
        major_stage = db.get_or_404(MajorStage, old_transportation.major_stage_id)
        journey = db.get_or_404(Journey, major_stage.journey_id)
        journey_costs = db.session.execute(db.select(Costs).filter_by(journey_id=journey.id)).scalars().first()
         
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500 
    
    response, isValid = TransportationValidation.validate_transportation(new_transportation)
    
    if not isValid:
        return jsonify({'transportationFormValues': response}), 400
    
    try:
        # Remove line breaks from the name
        clean_place_of_departure = new_transportation['place_of_departure']['value'].replace('\n', ' ').replace('\r', ' ')
        clean_place_of_arrival = new_transportation['place_of_arrival']['value'].replace('\n', ' ').replace('\r', ' ')
        # Update old transportation
        old_transportation.type = new_transportation['type']['value']
        old_transportation.start_time = parseDateTime(new_transportation['start_time']['value'])
        old_transportation.arrival_time = parseDateTime(new_transportation['arrival_time']['value'])
        old_transportation.place_of_departure = clean_place_of_departure
        old_transportation.departure_latitude = new_transportation.get('departure_latitude', {}).get('value', None)
        old_transportation.departure_longitude = new_transportation.get('departure_longitude', {}).get('value', None)
        old_transportation.place_of_arrival = clean_place_of_arrival
        old_transportation.arrival_latitude = new_transportation.get('arrival_latitude', {}).get('value', None)
        old_transportation.arrival_longitude = new_transportation.get('arrival_longitude', {}).get('value', None)
        old_transportation.transportation_costs = new_transportation['transportation_costs']['value']
        old_transportation.link = new_transportation['link']['value']
        db.session.commit()
        
        calculate_journey_costs(journey_costs)
        
        # build response transportation object for the frontend
        response_transportation = {'id': old_transportation.id,
                                    'type': new_transportation['type']['value'],
                                    'start_time': new_transportation['start_time']['value'],
                                    'arrival_time': new_transportation['arrival_time']['value'],
                                    'place_of_departure': new_transportation['place_of_departure']['value'],
                                    'departure_latitude': new_transportation['departure_latitude']['value'] if new_transportation['departure_latitude'] else None,
                                    'departure_longitude': new_transportation['departure_longitude']['value'] if new_transportation['departure_longitude'] else None,
                                    'place_of_arrival': new_transportation['place_of_arrival']['value'],
                                    'arrival_latitude': new_transportation['arrival_latitude']['value'] if new_transportation['arrival_latitude'] else None,
                                    'arrival_longitude': new_transportation['arrival_longitude']['value'] if new_transportation['arrival_longitude'] else None,
                                    'transportation_costs': new_transportation['transportation_costs']['value'],
                                    'link': new_transportation['link']['value']}

        return jsonify({'transportation': response_transportation, 'backendMajorStageId': major_stage.id}), 201
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    
@transportation_bp.route('/delete-major-stage-transportation/<int:majorStageId>', methods=['DELETE'])
@token_required
def delete_major_stage_transportation(current_user, majorStageId):
    major_stage = get_user_major_stage(
        current_user,
        majorStageId
    )
    if major_stage is None:
        return jsonify({'error': 'Resource not found'}), 404
    
    
    journey = db.session.execute(db.select(Journey).join(MajorStage).filter(MajorStage.id == majorStageId)).scalars().first()
    journey_costs = db.session.execute(db.select(Costs).filter_by(journey_id=journey.id)).scalars().first()
    try:        
        db.session.execute(db.delete(Transportation).where(Transportation.major_stage_id == majorStageId))
        db.session.commit()    
        
        calculate_journey_costs(journey_costs)
        
        return jsonify({'status': 200}), 200
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    

@transportation_bp.route('/delete-minor-stage-transportation/<int:minorStageId>', methods=['DELETE'])
@token_required
def delete_minor_stage_transportation(current_user, minorStageId):
    minor_stage = get_user_minor_stage(
        current_user,
        minorStageId
    )
    if minor_stage is None:
        return jsonify({'error': 'Resource not found'}), 404
    
    major_stage = db.get_or_404(MajorStage, minor_stage.major_stage_id)
    journey = db.session.execute(db.select(Journey).join(MajorStage).filter(MajorStage.id == major_stage.id)).scalars().first()
    journey_costs = db.session.execute(db.select(Costs).filter_by(journey_id=journey.id)).scalars().first()
    try:        
        db.session.execute(db.delete(Transportation).where(Transportation.minor_stage_id == minorStageId))
        db.session.commit()    
        
        calculate_journey_costs(journey_costs)
        
        return jsonify({ 'backendMajorStageId': major_stage.id}), 200
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500