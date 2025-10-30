from flask import Blueprint, request, jsonify
from db import db
from app.routes.route_protection import token_required
from app.routes.util import parseDate, formatDateToString, get_users_stages_titles
from app.models import Journey, Costs, Spendings, MajorStage,  CustomCountry, JourneysCustomCountriesLink
from app.validation.journey_validation import JourneyValidation
from app.routes.db_util import fetch_journeys
from app.routes.util import calculate_time_zone_offset, get_local_currency

journey_bp = Blueprint('journey', __name__)

@journey_bp.route('/get-stages-data', methods=['GET'])
@token_required
def get_stages_data(current_user):
    journeys_list = fetch_journeys(current_user=current_user)
        
    if not isinstance(journeys_list, Exception):   
        return jsonify({'journeys': journeys_list, 'status': 200})
    else:
        return jsonify({'error': str(journeys_list)}, 500)
        
    
@journey_bp.route('/create-journey', methods=['POST'])
@token_required
def create_journey(current_user):
    try:
        journey = request.get_json()
        result = db.session.execute(db.select(Journey).filter_by(user_id=current_user))
        existing_journeys = result.scalars().all()
        assigned_titles = get_users_stages_titles(current_user)
         
    except:
        return jsonify({'error': 'Unknown error'}, 400)

    response, isValid = JourneyValidation.validate_journey(journey, existing_journeys, assigned_titles)

    if not isValid:
        return jsonify({'journeyFormValues': response, 'status': 400})
    
    
    try:
        # Create a new journey
        new_journey = Journey(
            name=journey['name']['value'],
            description=journey['description']['value'],
            scheduled_start_time=parseDate(journey['scheduled_start_time']['value']),
            scheduled_end_time=parseDate(journey['scheduled_end_time']['value']),
            countries=journey['countries']['value'],
            user_id=current_user
        )
         
        db.session.add(new_journey)
        db.session.commit()
         
        # Create a new costs for the journey
        costs = Costs(
            journey_id=new_journey.id,
            budget=journey['budget']['value'],
            spent_money=0,
            money_exceeded=False
        )
        
        db.session.add(costs)
        db.session.commit()
        
        # Add connection between journey and custom countries to the link table
        added_countries = journey['countries']['value'].split(', ')
        for country in added_countries:
            result = db.session.execute(db.select(CustomCountry).filter_by(name=country, user_id=current_user))
            custom_country = result.scalars().first()
            
            if custom_country:
                new_link = JourneysCustomCountriesLink(
                    journey_id=new_journey.id,
                    custom_country_id=custom_country.id
                )
                db.session.add(new_link)
                db.session.commit()
        
        # build response journey object for the frontend
        response_journey = {'id': new_journey.id,
                'name': new_journey.name,
                'description': new_journey.description,
                'costs': {
                    'budget': costs.budget,
                    'spent_money': costs.spent_money,
                    'money_exceeded': costs.money_exceeded,
                },
                'scheduled_start_time': formatDateToString(new_journey.scheduled_start_time),
                'scheduled_end_time': formatDateToString(new_journey.scheduled_end_time),
                'countries': new_journey.countries,
                'majorStagesIds': []}
        
        return jsonify({'journey': response_journey,'status': 201})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)
    
    
@journey_bp.route('/update-journey/<int:journeyId>', methods=['POST'])
@token_required
def update_journey(current_user, journeyId):
    try:
        journey = request.get_json()
        result = db.session.execute(db.select(Journey).filter(Journey.id != journeyId, Journey.user_id==current_user))
        major_stages = db.session.execute(db.select(MajorStage).filter_by(journey_id=journeyId)).scalars().all()
        existing_journeys = result.scalars().all()
        assigned_titles = get_users_stages_titles(current_user)
        old_journey = db.get_or_404(Journey, journeyId)
    except:
        return jsonify({'error': 'Unknown error'}, 400)
    
    response, isValid = JourneyValidation.validate_journey_update(journey, existing_journeys, major_stages, assigned_titles, old_journey)
        
    if not isValid:
        return jsonify({'journeyFormValues': response, 'status': 400})
    
    
    

    money_exceeded = float(response['budget']['value']) < float(response['spent_money']['value'])

    majorStages_result = db.session.execute(db.select(MajorStage).filter_by(journey_id=journeyId))
    majorStages = majorStages_result.scalars().all()
    majorStagesIds = [majorStage.id for majorStage in majorStages]
    
    try:
        # Delete major stages that are not in the new journey, if former countries are not in the new countries
        current_countries = set(journey['countries']['value'].split(', '))
        former_countries = set(old_journey.countries.split(', '))
    
        if not former_countries.issubset(current_countries):
            missing_countries = former_countries - current_countries
            for delete_country in missing_countries:
                db.session.execute(db.delete(MajorStage).where(MajorStage.country == delete_country))
                db.session.commit()
                
                # Delete the connected entries from the link table
                result = db.session.execute(db.select(CustomCountry).filter_by(name=delete_country, user_id=current_user))
                delete_country_result = result.scalars().first()
                db.session.execute(db.delete(JourneysCustomCountriesLink).where(JourneysCustomCountriesLink.custom_country_id == delete_country_result.id))
                db.session.commit()
        
        # Add new countries to the link table
        added_countries = current_countries - former_countries
        for country in added_countries:
            result = db.session.execute(db.select(CustomCountry).filter_by(name=country, user_id=current_user))
            custom_country = result.scalars().first()
            
            if custom_country:
                new_link = JourneysCustomCountriesLink(
                    journey_id=journeyId,
                    custom_country_id=custom_country.id
                )
                db.session.add(new_link)
                db.session.commit()
            
        # Update the journey
        db.session.execute(db.update(Journey).where(Journey.id == journeyId).values(
            name=journey['name']['value'],
            description=journey['description']['value'],
            scheduled_start_time=parseDate(journey['scheduled_start_time']['value']),
            scheduled_end_time=parseDate(journey['scheduled_end_time']['value']),
            countries=journey['countries']['value'],
        ))
        db.session.commit()
        
        # Update the costs for the journey
        db.session.execute(db.update(Costs).where(Costs.journey_id == journeyId).values(
            budget=journey['budget']['value'],
            spent_money=journey['spent_money']['value'],
            money_exceeded=money_exceeded
        ))
        db.session.commit()
        
        journey_spendings = db.session.execute(db.select(Spendings).join(Costs).filter(Costs.journey_id == journeyId)).scalars().all()
            
        response_journey = {'id': journeyId,
                'name': journey['name']['value'],
                'description': journey['description']['value'],
                'costs': {
                    'budget': journey['budget']['value'],
                    'spent_money': journey['spent_money']['value'],
                    'money_exceeded': money_exceeded,
                },
                'scheduled_start_time': journey['scheduled_start_time']['value'],
                'scheduled_end_time': journey['scheduled_end_time']['value'],
                'countries': journey['countries']['value'],
                'majorStagesIds': majorStagesIds}
        
        if journey_spendings:
            response_journey['costs']['spendings'] = [{'id': spending.id, 'name': spending.name, 'amount': spending.amount, 'date': formatDateToString(spending.date), 'category': spending.category} for spending in journey_spendings]
        
        return jsonify({'journey': response_journey,'status': 200})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)
        
    
    
@journey_bp.route('/delete-journey/<int:journeyId>', methods=['DELETE'])
@token_required
def delete_journey(current_user, journeyId):
    try:        
        # Delete connected entries in the link table
        journey = db.get_or_404(Journey, journeyId)
        countries = journey.countries.split(', ')
        for country in countries:
            result = db.session.execute(db.select(CustomCountry).filter_by(name=country, user_id=current_user))
            custom_country = result.scalars().first()
            
            if custom_country:
                db.session.execute(db.delete(JourneysCustomCountriesLink).where(JourneysCustomCountriesLink.journey_id == journeyId))
                db.session.commit()
        
        # Delete the journey from the database
        db.session.delete(journey)
        db.session.commit()
        return jsonify({'status': 200})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)
        