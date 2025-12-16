from flask import Blueprint, jsonify, request
from db import db
from app.routes.route_protection import token_required
from app.routes.util import parseDate, formatDateToString, get_all_currencies, get_conversion_rate
from app.models import Costs, Journey,  MinorStage, MajorStage, Spendings
from app.validation.spending_validation import SpendingValidation
from app.routes.util import calculate_journey_costs

spending_bp = Blueprint('spending', __name__)

@spending_bp.route('/create-spending/<int:minorStageId>', methods=['POST'])
@token_required 
def create_spending(current_user, minorStageId):
    try:
        spending = request.get_json()
        minor_stage = db.get_or_404(MinorStage, minorStageId)
        major_stage = db.get_or_404(MajorStage, minor_stage.major_stage_id)
        journey = db.get_or_404(Journey, major_stage.journey_id)
        journey_costs = db.session.execute(db.select(Costs).filter_by(journey_id=journey.id)).scalars().first()
         
    except:
        return jsonify({'error': 'Unknown error'}, 400) 
    
    response, isValid = SpendingValidation.validate_spending(spending)
    
    if not isValid:
        return jsonify({'spendingFormValues': response, 'status': 400})
    
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
        
        return jsonify({'spending': response_spending, 'backendJourneyId': journey.id, 'status': 201})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)
    
    
@spending_bp.route('/update-spending/<int:minorStageId>/<int:spendingId>', methods=['POST'])
@token_required 
def update_spending(current_user, minorStageId, spendingId):
    try:
        new_spending = request.get_json()
        old_spending = db.get_or_404(Spendings, spendingId)
        minor_stage = db.get_or_404(MinorStage, minorStageId)
        major_stage = db.get_or_404(MajorStage, minor_stage.major_stage_id)
        journey = db.get_or_404(Journey, major_stage.journey_id)
        journey_costs = db.session.execute(db.select(Costs).filter_by(journey_id=journey.id)).scalars().first()
         
    except:
        return jsonify({'error': 'Unknown error'}, 400) 
    
    response, isValid = SpendingValidation.validate_spending(new_spending)
        
    if not isValid:
        return jsonify({'spendingFormValues': response, 'status': 400})
    
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

        return jsonify({'spending': response_spending, 'backendJourneyId': journey.id, 'status': 200})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)

    
@spending_bp.route('/delete-spending/<int:spendingId>', methods=['DELETE'])
@token_required
def delete_spending(current_user, spendingId):
    spending = db.get_or_404(Spendings, spendingId)
    costs = db.get_or_404(Costs, spending.costs_id)
    minor_stage = db.get_or_404(MinorStage, costs.minor_stage_id)
    major_stage = db.get_or_404(MajorStage, minor_stage.major_stage_id)
    journey = db.session.execute(db.select(Journey).join(MajorStage).filter(MajorStage.id == major_stage.id)).scalars().first()
    journey_costs = db.session.execute(db.select(Costs).filter_by(journey_id=journey.id)).scalars().first()
    try:        
        db.session.execute(db.delete(Spendings).where(Spendings.id == spendingId))
        db.session.commit()    
        
        calculate_journey_costs(journey_costs)
        
        return jsonify({'status': 200, 'backendJourneyId': journey.id})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)
    

@spending_bp.route('/get-currencies', methods=['GET'])
@token_required
def get_currencies(current_user):
    currencies = get_all_currencies(current_user)        
    return jsonify({'currencies': currencies, 'status': 200})
