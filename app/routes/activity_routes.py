from flask import Blueprint, current_app, jsonify, request

from app.models import Activity, Costs, Journey, MajorStage, MinorStage
from app.routes.resource_access import (
    get_user_activity,
    get_user_minor_stage,
)
from app.routes.route_protection import token_required
from app.routes.util import calculate_journey_costs
from app.validation.activity_validation import ActivityValidation
from db import db

activity_bp = Blueprint('activity', __name__)

@activity_bp.route('/create-activity/<int:minorStageId>', methods=['POST'])
@token_required 
def create_activity(current_user, minorStageId):
    try:
        activity = request.get_json()
                
        minor_stage = get_user_minor_stage(
            current_user,
            minorStageId
        )

        if minor_stage is None:
            return jsonify({'error': 'Minor stage not found'}), 404
        
        major_stage = db.get_or_404(MajorStage, minor_stage.major_stage_id)
        journey = db.get_or_404(Journey, major_stage.journey_id)
        journey_costs = db.session.execute(db.select(Costs).filter_by(journey_id=journey.id)).scalars().first()
         
    except:
        return jsonify({'error': 'Unknown error'}), 400 
    
    response, isValid = ActivityValidation.validate_activity(activity)
    
    if not isValid:
        return jsonify({'activityFormValues': response}), 400
    
    try:
        # Create a new activity
        new_activity = Activity(
            name=activity['name']['value'],
            description=activity['description']['value'],
            place=activity['place']['value'],
            costs=activity['costs']['value'],
            latitude = activity.get('latitude', {}).get('value', None),
            longitude = activity.get('longitude', {}).get('value', None),
            link=activity['link']['value'],
            booked=activity['booked']['value'],
            minor_stage_id=minorStageId
        )
        db.session.add(new_activity)
        db.session.commit()
        
        calculate_journey_costs(journey_costs)
        
        # build response activity object for the frontend
        response_activity = {'id': new_activity.id,
                                'name': new_activity.name,
                                'description': new_activity.description,
                                'place': new_activity.place,
                                'costs': new_activity.costs,
                                'latitude': new_activity.latitude if new_activity.latitude else None,
                                'longitude': new_activity.longitude if new_activity.longitude else None,
                                'link': new_activity.link,
                                'booked': new_activity.booked}
        
        return jsonify({'activity': response_activity, 'backendJourneyId': journey.id}), 201
    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Failed to update activity"
        )

        return jsonify({
            "error": "Internal server error"
        }), 500
    
    
@activity_bp.route('/update-activity/<int:minorStageId>/<int:activityId>', methods=['POST'])
@token_required 
def update_activity(current_user, minorStageId, activityId):
    try:
        old_activity = get_user_activity(
            current_user,
            activityId
        )
        minor_stage = get_user_minor_stage(current_user, minorStageId)

        if old_activity is None or minor_stage is None:
            return jsonify({'error': 'Resource not found'}), 404
        
        new_activity = request.get_json()
        major_stage = db.get_or_404(MajorStage, minor_stage.major_stage_id)
        journey = db.get_or_404(Journey, major_stage.journey_id)
        journey_costs = db.session.execute(db.select(Costs).filter_by(journey_id=journey.id)).scalars().first()
         
    except:
        return jsonify({'error': 'Unknown error'}), 400 
    
    response, isValid = ActivityValidation.validate_activity(new_activity)
    
    if not isValid:
        return jsonify({'activityFormValues': response}), 400
    
    try:
        # Update old activity
        old_activity.name = new_activity['name']['value']
        old_activity.description = new_activity['description']['value']
        old_activity.place = new_activity['place']['value']
        old_activity.costs = new_activity['costs']['value']        
        old_activity.latitude = new_activity.get('latitude', {}).get('value', None)
        old_activity.longitude = new_activity.get('longitude', {}).get('value', None)
        old_activity.link = new_activity['link']['value']
        old_activity.booked = new_activity['booked']['value']
        db.session.commit()
        
        
        calculate_journey_costs(journey_costs)
        
        # build response activity object for the frontend
        response_activity = {'id': old_activity.id,
                                    'name': new_activity['name']['value'],
                                    'description': new_activity['description']['value'],
                                    'place': new_activity['place']['value'],
                                    'costs': new_activity['costs']['value'],
                                    'latitude': new_activity.get('latitude', {}).get('value', None),
                                    'longitude': new_activity.get('longitude', {}).get('value', None),
                                    'link': new_activity['link']['value'],
                                    'booked': new_activity['booked']['value']}
        
        return jsonify({'activity': response_activity, 'backendJourneyId': journey.id}), 200
    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Failed to update activity"
        )

        return jsonify({
            "error": "Internal server error"
        }), 500

    

@activity_bp.route('/delete-activity/<int:activityId>', methods=['DELETE'])
@token_required
def delete_activity(current_user, activityId):

    activity = get_user_activity(
        current_user,
        activityId
    )

    if activity is None:
        return jsonify({'error': 'Activity not found'}), 404

    minor_stage = db.get_or_404(MinorStage, activity.minor_stage_id)
    major_stage = db.get_or_404(MajorStage, minor_stage.major_stage_id)
    journey = db.session.execute(db.select(Journey).join(MajorStage).filter(MajorStage.id == major_stage.id)).scalars().first()
    journey_costs = db.session.execute(db.select(Costs).filter_by(journey_id=journey.id)).scalars().first()
    try:        
        db.session.execute(db.delete(Activity).where(Activity.id == activityId))
        db.session.commit()    
        
        calculate_journey_costs(journey_costs)
        
        return jsonify({'backendJourneyId': journey.id}), 200
    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Failed to delete activity"
        )

        return jsonify({
            "error": "Internal server error"
        }), 500