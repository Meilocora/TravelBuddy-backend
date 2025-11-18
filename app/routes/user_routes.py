from flask import Blueprint, request, jsonify
from app.routes.route_protection import token_required
from app.routes.util import calculate_time_zone_offset, get_local_currency

user_bp = Blueprint('user', __name__)

@user_bp.route('/get-user-data', methods=['GET'])
@token_required
def get_user_data(current_user):
    latitude = request.args.get('latitude', type=float)
    longitude = request.args.get('longitude', type=float)

    currencyInfo = {'code': 'EUR', 'name': 'Euro', 'symbol': '€', 'conversion_rate': 1.0}
    user_time_zone_offset = 0
    
    if latitude is None or longitude is None:
        user_time_zone_offset = 0
    else:
        try:
            user_time_zone_offset =  calculate_time_zone_offset(latitude, longitude)
            currencyInfo = get_local_currency(latitude, longitude)
        except Exception as e:
            print(f"Error occurred: {e}")
    return jsonify({'offset': user_time_zone_offset, 'status': 200, 'localCurrency': currencyInfo})
