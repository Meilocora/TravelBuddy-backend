from flask import Blueprint, request, jsonify
from app.validation.currency_validation import CurrencyValidation
from db import db
from app.models import Currency
from app.routes.route_protection import token_required

currency_bp = Blueprint('currency', __name__)
    
@currency_bp.route('/add-currency', methods=['POST'])
@token_required
def create_currency(current_user):
    try:
        currency = request.get_json()
    except:
        return jsonify({'error': 'Unknown error'}, 400) 
        
    response, isValid = CurrencyValidation.validate_currency(currency=currency)
    if not isValid:
        return jsonify({'currencyFormValues': response, 'status': 400})
    
    try:
        print('Creating currency:', currency)
        # Create a new currency
        new_currency = Currency(
            code=currency['code']['value'],
            name=currency['name']['value'],
            symbol=currency['symbol']['value'],
            conversion_rate=float(currency['conversionRate']['value']),
            user_id=current_user
        )
        
        print('New currency object:', new_currency)
        db.session.add(new_currency)
        db.session.commit()
        
        return jsonify({'status': 201})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)
    
    
@currency_bp.route('/update-currency/<int:currencyId>', methods=['POST'])
@token_required
def update_currency(current_user, currencyId):
    try:
        currency = request.get_json()
    except:
        return jsonify({'error': 'Unknown error'}, 400)
        
    response, isValid = CurrencyValidation.validate_currency(currency=currency)
    
    if not isValid:
        return jsonify({'currencyFormValues': response, 'status': 400})
        
    try:        
        # Update the currency
        db.session.execute(db.update(Currency).where(Currency.id == currencyId).values(
            code=currency['code']['value'],
            name=currency['name']['value'],
            symbol=currency['symbol']['value'],
            conversion_rate=float(currency['conversionRate']['value']),
            user_id=current_user
        ))
        db.session.commit()        
        
        return jsonify({'status': 200})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)
        
        
@currency_bp.route('/delete-currency/<int:currencyId>', methods=['DELETE'])
@token_required
def delete_currency(current_user, currencyId):
    try:
        currency_to_delete = db.get_or_404(Currency, currencyId)
        db.session.delete(currency_to_delete)
        db.session.commit()
        
        return jsonify({'status': 200})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)
    
  