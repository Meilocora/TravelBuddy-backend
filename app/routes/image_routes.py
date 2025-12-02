from flask import Blueprint, request, jsonify
from app.routes.util import parseDateTime
from db import db
from app.routes.route_protection import token_required
from app.models import Images
from app.routes.db_util import fetch_images


image_bp = Blueprint('images', __name__)

@image_bp.route('/get-images', methods=['GET'])
@token_required
def get_images(current_user):
    images_list = fetch_images(current_user=current_user)
        
    if not isinstance(images_list, Exception):   
        return jsonify({'images': images_list, 'status': 200})
    else:
        return jsonify({'error': str(images_list)}, 500)


@image_bp.route('/add-image', methods=['POST'])
@token_required
def add_image(current_user):
    try:
        image = request.get_json()
         
    except:
        return jsonify({'error': 'Unknown error'}, 400)

    try:
        # Create a new image
        new_image = Images(
            url = image['url']['value'],
            favorite=image['favorite']['value'],
            latitude=image.get('latitude', {}).get('value', None),
            longitude=image.get('longitude', {}).get('value', None),
            timestamp=parseDateTime(image['timestamp']['value']),
            description=image['description']['value'],
            user_id=current_user,
            minor_stage_id=image.get('minorStageId', {}).get('value', None),
            place_to_visit_id=image.get('placeToVisitId', {}).get('value', None)
        )
         
        db.session.add(new_image)
        db.session.commit()
        
        return jsonify({'status': 201})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)
    

@image_bp.route('/update-image/<int:imageId>', methods=['POST'])
@token_required
def update_image(current_user, imageId):
    try:
        image = request.get_json()
         
    except:
        return jsonify({'error': 'Unknown error'}, 400)

    try:
        # Update Image
        db.session.execute(db.update(Images).where(Images.id == imageId).values(
            url = image['url']['value'],
            favorite=image['favorite']['value'],
            latitude=image['latitude']['value'],
            longitude=image['longitude']['value'],
            timestamp=parseDateTime(image['timestamp']['value']),
            description=image['description']['value'],
            minor_stage_id=image['minor_stage_id']['value'],
            place_to_visit_id=image['place_to_visit_id']['value']
        ))
        db.session.commit()
        
        return jsonify({'status': 201})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)
    
    
@image_bp.route('/delete-image/<int:imageId>', methods=['DELETE'])
@token_required
def delete_image(current_user, imageId):
    try:        
        image = db.get_or_404(Images, imageId)        
        # Delete the image from the database
        db.session.delete(image)
        db.session.commit()
        return jsonify({'status': 200})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)