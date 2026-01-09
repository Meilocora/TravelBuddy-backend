from flask import Blueprint, request, jsonify
from app.routes.util import parseDateTime
from db import db
from app.routes.route_protection import token_required
from app.models import Medium
from app.routes.db_util import fetch_media


medium_bp = Blueprint('medium', __name__)

@medium_bp.route('/get-media', methods=['GET'])
@token_required
def get_media(current_user):
    media_list = fetch_media(current_user=current_user)
        
    if not isinstance(media_list, Exception):   
        return jsonify({'media': media_list, 'status': 200})
    else:
        return jsonify({'error': str(media_list)}, 500)


@medium_bp.route('/add-medium', methods=['POST'])
@token_required
def add_media(current_user):
    try:
        mediumData = request.get_json()
    except:
        return jsonify({'error': 'Unknown error'}, 400)
    
    try:
        # Create a new medium
        new_medium = Medium(
            medium_type = mediumData['mediumType'],
            url = mediumData['url']['value'],
            thumbnail_url = mediumData.get('thumbnailUrl', None),
            favorite=mediumData['favorite']['value'],
            latitude=mediumData.get('latitude', {}).get('value', None),
            longitude=mediumData.get('longitude', {}).get('value', None),
            timestamp=parseDateTime(mediumData['timestamp']['value']),
            description=mediumData['description']['value'],
            duration=mediumData.get('duration', {}).get('value', None),
            user_id=current_user,
            minor_stage_id=mediumData.get('minorStageId', {}).get('value', None),
            place_to_visit_id=mediumData.get('placeToVisitId', {}).get('value', None),
        )
         
        db.session.add(new_medium)
        db.session.commit()

        return jsonify({'status': 201})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)
    

@medium_bp.route('/update-medium/<int:mediumId>', methods=['POST'])
@token_required
def update_medium(current_user, mediumId):
    try:
        medium = request.get_json()
        old_medium = db.get_or_404(Medium, mediumId)
    except:
        return jsonify({'error': 'Unknown error'}, 400)

    try:
        # Update Medium
        db.session.execute(db.update(Medium).where(Medium.id == mediumId).values(
            medium_type = old_medium.medium_type,
            url = old_medium.url,
            thumbnail_url = old_medium.thumbnail_url,
            favorite=medium['favorite']['value'],
            latitude=medium.get('latitude', {}).get('value', None),
            longitude=medium.get('longitude', {}).get('value', None),
            timestamp=parseDateTime(medium['timestamp']['value']),
            description=medium['description']['value'],
            minor_stage_id=medium.get('minorStageId', {}).get('value', None),
            place_to_visit_id=medium.get('placeToVisitId', {}).get('value', None),
            duration=old_medium.duration
        ))
        db.session.commit()
                
        return jsonify({'status': 200})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)
    
    
@medium_bp.route('/delete-medium/<int:mediumId>', methods=['DELETE'])
@token_required
def delete_medium(current_user, mediumId):
    try:        
        medium = db.get_or_404(Medium, mediumId)        
        # Delete the medium from the database
        db.session.delete(medium)
        db.session.commit()
        return jsonify({'status': 200})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)
    

@medium_bp.route('/delete-media', methods=['DELETE'])
@token_required
def delete_media(current_user):
    try:
        data = request.get_json()        
        mediumIds = data if isinstance(data, list) else data.get('ids', [])
                
        if not isinstance(mediumIds, list) or len(mediumIds) == 0:
            return jsonify({'error': 'Invalid or empty ids list'}), 400
        
        for mediumId in mediumIds:       
            medium = db.session.query(Medium).filter(Medium.id == mediumId).first()
            if not medium:
                return jsonify({'error': f'Medium with id {mediumId} not found'}), 404
            db.session.delete(medium)
                    
        db.session.commit()
                
        return jsonify({'status': 200}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500