from flask import Blueprint, jsonify, request
from datetime import timedelta

from app.models import Costs, Journey, MajorStage, MinorStage, Spendings, Transportation
from app.routes.db_util import adjust_stages_orders, recalculate_major_stage_dates
from app.routes.resource_access import (
    get_user_journey,
    get_user_major_stage,
    get_user_major_stages_by_ids,
)
from app.routes.route_protection import token_required
from app.routes.util import (
    calculate_journey_costs,
    formatDateTimeToString,
    formatDateToString,
    get_users_stages_titles,
    parseDate,
)
from app.validation.major_stage_validation import MajorStageValidation
from db import db

major_stage_bp = Blueprint('major_stage', __name__)   

@major_stage_bp.route('/create-major-stage/<int:journeyId>', methods=['POST'])
@token_required
def create_major_stage(current_user, journeyId):
    try:
        journey = get_user_journey(current_user, journeyId)

        if journey is None:
            return jsonify({'error': 'Journey not found'}), 404

        major_stage = request.get_json()
        result = db.session.execute(db.select(MajorStage).filter_by(journey_id=journeyId))
        existing_major_stages = result.scalars().all()
                
        assigned_titles = get_users_stages_titles(current_user)
        
        existing_major_stages_costs = []
        for stage in existing_major_stages:
            existing_major_stages_costs.append(db.session.execute(db.select(Costs).filter_by(major_stage_id=stage.id)).scalars().first())
        
        journey_costs = db.session.execute(db.select(Costs).filter_by(journey_id=journeyId)).scalars().first()
         
    except Exception:
        db.session.rollback()
        return jsonify({
            "error": "Internal server error"
        }), 500
    
    response, isValid = MajorStageValidation.validate_major_stage(major_stage, existing_major_stages, existing_major_stages_costs, journey_costs, assigned_titles)
    
    if not isValid:
        return jsonify({'majorStageFormValues': response}), 400
    
    try:
        # Adjust orders of existing major stages if necessary
        if int(major_stage['position']['value']) <= len(existing_major_stages):
            adjust_stages_orders(existing_major_stages, int(major_stage['position']['value']))

        # Create a new major stage
        new_major_stage = MajorStage(
            title=major_stage['title']['value'],
            # scheduled_start_time="",  
            # scheduled_end_time="",
            duration_days=major_stage['duration_days']['value'],
            additional_info=major_stage['additional_info']['value'],
            country=major_stage['country']['value'],
            position=major_stage['position']['value'],
            journey_id=journeyId
        )
        journey.major_stages.append(new_major_stage)
        db.session.add(new_major_stage)
        
        recalculate_major_stage_dates(journey)
        
        # Send the new major stage to the database but do not commit yet
        db.session.flush()          
        
        # Create a new costs for the major stage
        costs = Costs(
            major_stage_id=new_major_stage.id,
            budget=major_stage['budget']['value'],
            spent_money=0,
            money_exceeded=False
        )
        db.session.add(costs)
        db.session.commit()
        
        # build response major stage object for the frontend
        response_major_stage = {'id': new_major_stage.id,
                                'title': new_major_stage.title,
                                'scheduled_start_time': formatDateToString(new_major_stage.scheduled_start_time),
                                'scheduled_end_time': formatDateToString(new_major_stage.scheduled_end_time),
                                'duration_days': new_major_stage.duration_days,
                                'additional_info': new_major_stage.additional_info,
                                'country': new_major_stage.country,
                                'position': new_major_stage.position,
                                'costs': {
                                    'budget': costs.budget,
                                    'spent_money': costs.spent_money,
                                    'money_exceeded': costs.money_exceeded
                                },  
                                'minorStagesIds': []}
        
        return jsonify({'majorStage': response_major_stage}), 201
    except Exception:
        db.session.rollback()
        return jsonify({
            "error": "Internal server error"
        }), 500
    
    
@major_stage_bp.route('/update-major-stage/<int:journeyId>/<int:majorStageId>', methods=['POST'])
@token_required
def update_major_stage(current_user, journeyId, majorStageId):
    try:
        major_stage = request.get_json()
        minor_stages = db.session.execute(db.select(MinorStage).filter_by(major_stage_id=majorStageId)).scalars().all()
        result = db.session.execute(db.select(MajorStage).filter(MajorStage.id != majorStageId, MajorStage.journey_id==journeyId))
        existing_major_stages = result.scalars().all()
        
        old_major_stage = get_user_major_stage(
            current_user,
            majorStageId,
            journey_id=journeyId,
        )

        if old_major_stage is None:
            return jsonify({'error': 'Major stage not found'}), 404
        
        assigned_titles = get_users_stages_titles(current_user)

    
        existing_major_stages_costs = []
        for stage in existing_major_stages:
            existing_major_stages_costs.append(db.session.execute(db.select(Costs).filter_by(major_stage_id=stage.id)).scalars().first())
    
        journey_costs = db.session.execute(db.select(Costs).filter_by(journey_id=journeyId)).scalars().first()
        
    except Exception:
        db.session.rollback()
        return jsonify({
            "error": "Internal server error"
        }), 500
    
    
    response, isValid = MajorStageValidation.validate_major_stage_update(major_stage, existing_major_stages, existing_major_stages_costs, journey_costs, minor_stages, assigned_titles, old_major_stage)
    
    if not isValid:
        return jsonify({'majorStageFormValues': response}), 400
    
    # Delete Minor Stages if Country is changed
    if response['country']['value'] != old_major_stage.country:
        if old_major_stage.minor_stages:
            for minor_stage in old_major_stage.minor_stages:
                db.session.delete(minor_stage)
            db.session.commit()

    money_exceeded = float(response['budget']['value']) < float(response['spent_money']['value'])

    minorStages_result = db.session.execute(db.select(MinorStage).filter_by(major_stage_id=majorStageId))
    minorStages = minorStages_result.scalars().all()
    minorStagesIds = [minorStage.id for minorStage in minorStages]
    
    major_stage_spendings = db.session.execute(db.select(Spendings).join(Costs).filter(Costs.major_stage_id == majorStageId)).scalars().all()
    transportation = db.session.execute(db.select(Transportation).filter_by(major_stage_id=majorStageId)).scalars().first()
    
    try:        
        # Adjust orders of existing major stages if necessary     
        adjust_stages_orders(existing_major_stages, major_stage['position']['value'], old_major_stage.position)

        old_major_stage.title = major_stage['title']['value']
        old_major_stage.duration_days = major_stage['duration_days']['value']
        old_major_stage.additional_info = major_stage['additional_info']['value']
        old_major_stage.country = major_stage['country']['value']
        old_major_stage.position = major_stage['position']['value']
        db.session.flush()
        
        # Recalculate the dates for all major stages in the journey after adding the new one
        journey = db.session.execute(db.select(Journey).filter_by(id=old_major_stage.journey_id)).scalars().first()
        recalculate_major_stage_dates(journey)
       
        # Update the costs for the major stage
        db.session.execute(db.update(Costs).where(Costs.major_stage_id == majorStageId).values(
            budget=major_stage['budget']['value'],
            spent_money=major_stage['spent_money']['value'],
            money_exceeded=money_exceeded
        ))
        db.session.commit()
                
        response_major_stage = {'id': majorStageId,
                                'title': major_stage['title']['value'],
                                'scheduled_start_time': formatDateToString(old_major_stage.scheduled_start_time),
                                'scheduled_end_time': formatDateToString(old_major_stage.scheduled_end_time),
                                'duration_days': major_stage['duration_days']['value'],
                                'additional_info': major_stage['additional_info']['value'],
                                'country': major_stage['country']['value'],
                                'position': major_stage['position']['value'],
                                'costs': {
                                    'budget': major_stage['budget']['value'],
                                    'spent_money': major_stage['spent_money']['value'],
                                    'money_exceeded': money_exceeded
                                },
                                'minorStagesIds': minorStagesIds}
        
        if major_stage_spendings:
            response_major_stage['costs']['spendings'] = [{'name': spending.name, 'amount': spending.amount, 'date': formatDateToString(spending.date), 'category': spending.category} for spending in major_stage_spendings]
        
        if transportation is not None:
            response_major_stage['transportation'] = {
                'type': transportation.type,
                'start_time': formatDateTimeToString(transportation.start_time),
                'arrival_time': formatDateTimeToString(transportation.arrival_time),
                'place_of_departure': transportation.place_of_departure,
                'place_of_arrival': transportation.place_of_arrival,
                'transportation_costs': transportation.transportation_costs,
                'link': transportation.link,
            }
        
        return jsonify({'majorStage': response_major_stage}), 200
    except Exception:
        db.session.rollback()
        return jsonify({
            "error": "Internal server error"
        }), 500
    
    
@major_stage_bp.route('/delete-major-stage/<int:majorStageId>', methods=['DELETE'])
@token_required
def delete_major_stage(current_user, majorStageId):
    journey = db.session.execute(db.select(Journey).join(MajorStage).filter(MajorStage.id == majorStageId)).scalars().first()
    journey_costs = db.session.execute(db.select(Costs).filter_by(journey_id=journey.id)).scalars().first()
    try:             
        major_stage = get_user_major_stage(
            current_user,
            majorStageId,
            journey_id=journey.id,
        )

        if major_stage is None:
            return jsonify({'error': 'Major stage not found'}), 404
        # Adjust orders of existing major stages if necessary
        if major_stage.position < len(journey.major_stages):
            later_major_stages = [other_major_stage for other_major_stage in journey.major_stages if other_major_stage.position > major_stage.position]
            adjust_stages_orders(later_major_stages, 999, major_stage.position)
            
        db.session.delete(major_stage)
        
        db.session.flush()
        
        recalculate_major_stage_dates(journey)
        calculate_journey_costs(journey_costs)
        
        db.session.commit()
        
        return jsonify({'status': 200})
    except Exception:
        db.session.rollback()
        return jsonify({
            "error": "Internal server error"
        }), 500
    
    
@major_stage_bp.route('/swap-major-stages', methods=['POST'])
@token_required
def swap_major_stages(current_user):

    data = request.get_json()
    positions = data.get('stagesPositionList', [])

    stage_ids = [
        int(item['id'])
        for item in positions
    ]

    owned_stages = get_user_major_stages_by_ids(
        current_user,
        stage_ids
    )

    owned_ids = {
        stage.id
        for stage in owned_stages
    }

    if owned_ids != set(stage_ids):
        return jsonify({
            'error': 'One or more stages not found'
        }), 404

    for item in positions:
        db.session.execute(
            db.update(MajorStage)
            .where(MajorStage.id == int(item['id']))
            .values(position=item['position'])
        )

    db.session.flush()
    
    journey = db.session.execute(db.select(Journey).filter_by(id=owned_stages[0].journey_id)).scalars().first()
    recalculate_major_stage_dates(journey)
    db.session.commit()

    return jsonify({'status': 200})