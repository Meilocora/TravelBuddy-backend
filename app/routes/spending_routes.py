from flask import Blueprint, jsonify, request

from app.models import Costs, Journey, MajorStage, MinorStage, Spendings
from app.routes.resource_access import get_user_minor_stage, get_user_spending
from app.routes.route_protection import token_required
from app.routes.util import (
    calculate_journey_costs,
    formatDateToString,
    get_all_currencies,
    parseDate,
)
from app.validation.spending_validation import SpendingValidation
from db import db

spending_bp = Blueprint('spending', __name__)

@spending_bp.route('/create-spending/<int:minorStageId>', methods=['POST'])
@token_required 
def create_spending(current_user, minorStageId):
    try:
        minor_stage = get_user_minor_stage(
            current_user,
            minorStageId
        )
        
        if minor_stage is None:
            return jsonify({'error': 'Minor stage not found'}), 404
        
        spending = request.get_json()
        major_stage = db.get_or_404(MajorStage, minor_stage.major_stage_id)
        journey = db.get_or_404(Journey, major_stage.journey_id)
        journey_costs = db.session.execute(db.select(Costs).filter_by(journey_id=journey.id)).scalars().first()
         
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Internal server error"
        }), 500
    
    response, isValid = SpendingValidation.validate_spending(spending)
    
    if not isValid:
        return jsonify({'spendingFormValues': response}), 400
    
    try:
        # Create a new spending
        new_spending = Spendings(
            name=spending['name']['value'],
            amount=spending['amount']['value'],
            date=parseDate(spending['date']['value']),
            category=spending['category']['value'],
            costs_id=minor_stage.costs.id
        )
        db.session.add(new_spending)
        db.session.commit()
        
        calculate_journey_costs(journey_costs)
        
        # build response spending object for the frontend
        response_spending = {'id': new_spending.id,
                                'name': new_spending.name,
                                'amount': new_spending.amount,
                                'date': formatDateToString(new_spending.date),
                                'category': new_spending.category}
        
        return jsonify({'spending': response_spending, 'backendJourneyId': journey.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    
@spending_bp.route('/update-spending/<int:minorStageId>/<int:spendingId>', methods=['POST'])
@token_required 
def update_spending(current_user, minorStageId, spendingId):
    try:
        minor_stage = get_user_minor_stage(
            current_user,
            minorStageId
        )
        old_spending = get_user_spending(
            current_user,
            spendingId
        )
        
        if minor_stage is None or old_spending is None:
            return jsonify({'error': 'Resource not found'}), 404
                
        new_spending = request.get_json()
        major_stage = db.get_or_404(MajorStage, minor_stage.major_stage_id)
        journey = db.get_or_404(Journey, major_stage.journey_id)
        journey_costs = db.session.execute(db.select(Costs).filter_by(journey_id=journey.id)).scalars().first()
         
    except:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    response, isValid = SpendingValidation.validate_spending(new_spending)
        
    if not isValid:
        return jsonify({'spendingFormValues': response}), 400
    
    try:
        # Update old spending
        old_spending.name = new_spending['name']['value']
        old_spending.amount = new_spending['amount']['value']
        old_spending.date = parseDate(new_spending['date']['value'])
        old_spending.category = new_spending['category']['value']
        db.session.commit()
        
        calculate_journey_costs(journey_costs)
        
        # build response spending object for the frontend
        response_spending = {'id': old_spending.id,
                                    'name': new_spending['name']['value'],
                                    'amount': new_spending['amount']['value'],
                                    'date': new_spending['date']['value'],
                                    'category': new_spending['category']['value']}

        return jsonify({'spending': response_spending, 'backendJourneyId': journey.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

    
@spending_bp.route('/delete-spending/<int:spendingId>', methods=['DELETE'])
@token_required
def delete_spending(current_user, spendingId):
    spending = db.get_or_404(Spendings, spendingId)
    
    spending = get_user_spending(
        current_user,
        spendingId
    )
    
    if spending is None:
        return jsonify({'error': 'Spending not found'}), 404
    
    costs = db.get_or_404(Costs, spending.costs_id)
    minor_stage = db.get_or_404(MinorStage, costs.minor_stage_id)
    major_stage = db.get_or_404(MajorStage, minor_stage.major_stage_id)
    journey = db.session.execute(db.select(Journey).join(MajorStage).filter(MajorStage.id == major_stage.id)).scalars().first()
    journey_costs = db.session.execute(db.select(Costs).filter_by(journey_id=journey.id)).scalars().first()
    try:        
        db.session.execute(db.delete(Spendings).where(Spendings.id == spendingId))
        db.session.commit()    
        
        calculate_journey_costs(journey_costs)
        
        return jsonify({'backendJourneyId': journey.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    

@spending_bp.route('/get-currencies', methods=['GET'])
@token_required
def get_currencies(current_user):
    currencies = get_all_currencies(current_user)        
    return jsonify({'currencies': currencies}), 200
