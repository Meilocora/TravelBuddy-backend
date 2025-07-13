from flask import Blueprint, request, jsonify
from db import db
from app.models import PlaceToVisit, CustomCountry
from app.validation.place_validation import PlaceValidation
from app.routes.route_protection import token_required

place_bp = Blueprint('place-to-visit', __name__)

@place_bp.route('/get-places', methods=['GET'])
@token_required
def get_places(current_user):
    try:
        # Get all the journeys from the database
        result = db.session.execute(db.select(PlaceToVisit).filter_by(user_id=current_user))
        places = result.scalars().all()
        
        places_list = []
        for place in places:
            # Append the whole place, that matches the model from frontend to the list
            places_list.append({
                'countryId': place.custom_country_id,
                'id': place.id,
                'name': place.name,
                'description': place.description,
                'visited': place.visited,
                'favorite': place.favorite,
                'latitude': place.latitude, 
                'longitude': place.longitude,
                'link': place.link,
            })    
        return jsonify({'places': places_list, 'status': 200})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)
    
    
@place_bp.route('/get-available-places-by-country/<int:minorStageId>/<string:countryName>', methods=['GET'])
@token_required
def get_places_by_country(current_user, minorStageId, countryName):
    try:        
        country = db.session.execute(db.select(CustomCountry).filter_by(user_id = current_user, name=countryName)).scalars().first()
        result = db.session.execute(db.select(PlaceToVisit).filter_by(user_id=current_user, custom_country_id=country.id))
        places = result.scalars().all()
        # Filter for places that are not assigned to another minor stage        
        places = [place for place in places if place.minor_stage_id == None or place.minor_stage_id == minorStageId]
                          
        places_list = []
        for place in places:
            # Append the whole place, that matches the model from frontend to the list
            places_list.append({
                'countryId': place.custom_country_id,
                'id': place.id,
                'name': place.name,
                'description': place.description,
                'visited': place.visited,
                'favorite': place.favorite,
                'latitude': place.latitude, 
                'longitude': place.longitude,
                'link': place.link,
            })    
                    
        return jsonify({'places': places_list, 'countryId': country.id, 'status': 200})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)
    
    
@place_bp.route('/create-place', methods=['POST'])
@token_required
def create_place(current_user):
    try:
        place = request.get_json()
    except:
        return jsonify({'error': 'Unknown error'}, 400) 
        
    response, isValid = PlaceValidation.validate_place(place=place)
    if not isValid:
        return jsonify({'placeFormValues': response, 'status': 400})
    

    
    try:
        # Remove line breaks from the name
        clean_name = place['name']['value'].replace('\n', ' ').replace('\r', ' ')

        # Create a new place
        new_place = PlaceToVisit(
            custom_country_id=place['countryId']['value'],
            name=clean_name,
            description=place['description']['value'],
            visited=place['visited']['value'],
            favorite=place['favorite']['value'],
            latitude=place['latitude']['value'],
            longitude=place['longitude']['value'],
            link=place['link']['value'],
            user_id=current_user
        )
        db.session.add(new_place)
        db.session.commit()
        
        response_place = {'id': new_place.id,
                'countryId': new_place.custom_country_id,
                'name': new_place.name,
                'description': new_place.description,
                'visited': new_place.visited,
                'favorite': new_place.favorite,
                'latitude': new_place.latitude,
                'longitude': new_place.longitude,
                'link': new_place.link}
        
        return jsonify({'place': response_place,'status': 201})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)
    
    
@place_bp.route('/update-place/<int:placeId>', methods=['POST'])
@token_required
def update_journey(current_user, placeId):
    try:
        place = request.get_json()
    except:
        return jsonify({'error': 'Unknown error'}, 400)
    
    old_place = db.get_or_404(PlaceToVisit, placeId)
    
    response, isValid = PlaceValidation.validate_place(place=place)
    
    if not isValid:
        return jsonify({'placeFormValues': response, 'status': 400})
        
    try:
         # Remove line breaks from the name
        clean_name = place['name']['value'].replace('\n', ' ').replace('\r', ' ')
        
        # Update the place
        db.session.execute(db.update(PlaceToVisit).where(PlaceToVisit.id == placeId).values(
            name=clean_name,
            description=place['description']['value'],
            visited=place['visited']['value'],
            favorite=place['favorite']['value'],
            latitude=place['latitude']['value'],
            longitude=place['longitude']['value'],
            link=place['link']['value'],
        ))
        db.session.commit()
        
        response_place = {'id': old_place.id,
                'countryId': old_place.custom_country_id,
                'name': place['name']['value'],
                'description': place['description']['value'],
                'visited': place['visited']['value'],
                'favorite': place['favorite']['value'],
                'latitude': place['latitude']['value'],
                'longitude': place['longitude']['value'],
                'link': place['link']['value'],
                }
        
        
        return jsonify({'place': response_place,'status': 200})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)
        
    
@place_bp.route('/toggle-favorite-place/<int:placeId>', methods=['POST'])
@token_required
def toggle_favorite_place(current_user, placeId):
    try:
        
        old_place = db.get_or_404(PlaceToVisit, placeId)
        
        # Update the place
        db.session.execute(db.update(PlaceToVisit).where(PlaceToVisit.id == placeId).values(
            favorite = not old_place.favorite
        ))
        db.session.commit()

        return jsonify({'status': 200})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)
    
    
@place_bp.route('/toggle-visited-place/<int:placeId>', methods=['POST'])
@token_required
def toggle_visited_place(current_user, placeId):
    try:
        old_place = db.get_or_404(PlaceToVisit, placeId)
        
        # Update the place
        db.session.execute(db.update(PlaceToVisit).where(PlaceToVisit.id == placeId).values(
            visited = not old_place.visited
        ))
        db.session.commit()
        return jsonify({'status': 200})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)

    
@place_bp.route('/delete-place/<int:placeId>', methods=['DELETE'])
@token_required
def delete_place(current_user, placeId):
    try:
        # Delete the place from the database
        place_to_visit = db.get_or_404(PlaceToVisit, placeId)
        db.session.delete(place_to_visit)
        db.session.commit()
        return jsonify({'status': 200})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)
    
    
@place_bp.route('/add-minor-stage-to-place/<string:name>/<int:minorStageId>', methods=['POST'])
@token_required
def add_minor_stage_to_place(current_user, name, minorStageId):
    try:
        old_place = db.session.execute(db.select(PlaceToVisit).filter_by(user_id=current_user, name=name)).scalars().first()
        old_place.minor_stage_id = minorStageId
        db.session.commit()

        return jsonify({'status': 200})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)
    
    
@place_bp.route('/remove-minor-stage-from-place/<string:name>', methods=['POST'])
@token_required
def remove_minor_stage_from_place(current_user, name):
    try:
        old_place = db.session.execute(db.select(PlaceToVisit).filter_by(user_id=current_user, name=name)).scalars().first()        
        old_place.minor_stage_id = None
        db.session.commit()

        return jsonify({'status': 200})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)