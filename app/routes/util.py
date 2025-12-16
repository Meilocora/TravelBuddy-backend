from datetime import datetime
from geopy.geocoders import Nominatim
from countryinfo import CountryInfo
from currency_converter import CurrencyConverter
from timezonefinder import TimezoneFinder
import pytz
from db import db
from app.models import Journey, Costs, Spendings, Transportation, MajorStage, MinorStage, Accommodation, Activity, Currency


def parseDate(dateString: str): 
    return datetime.strptime(dateString, '%d.%m.%Y')


def parseDateTime(dateTimeString: str):
    return datetime.strptime(dateTimeString, '%d.%m.%Y %H:%M')


def formatDateToString(date: datetime):
    return datetime.strftime(date, '%d.%m.%Y')


def formatDateTimeToString(dateTime: datetime):
    return datetime.strftime(dateTime, '%d.%m.%Y %H:%M')


def calculate_minor_stage_costs(minor_stage_costs):
    spent_money = 0
    
    transportation = db.session.execute(db.select(Transportation).filter_by(minor_stage_id=minor_stage_costs.minor_stage_id)).scalars().first()
    if transportation:
        spent_money += transportation.transportation_costs
    
    accommodation = db.session.execute(db.select(Accommodation).filter_by(minor_stage_id=minor_stage_costs.minor_stage_id)).scalars().first()
    spent_money += accommodation.costs
    
    activities = db.session.execute(db.select(Activity).filter_by(minor_stage_id=minor_stage_costs.minor_stage_id)).scalars().all()
    for activity in activities:
        spent_money += activity.costs
    
    spendings = db.session.execute(db.select(Spendings).filter_by(costs_id=minor_stage_costs.id)).scalars().all()
    for spending in spendings:
        spent_money += spending.amount
  
    minor_stage_costs.spent_money = spent_money
    minor_stage_costs.money_exceeded = minor_stage_costs.spent_money > minor_stage_costs.budget
    db.session.commit()
    return minor_stage_costs

def calculate_major_stage_costs(major_stage_costs):
    spent_money = 0
    
    transportation = db.session.execute(db.select(Transportation).filter_by(major_stage_id=major_stage_costs.major_stage_id)).scalars().first()
    if transportation:
        spent_money += transportation.transportation_costs
    
    spendings = db.session.execute(db.select(Spendings).filter_by(costs_id=major_stage_costs.id)).scalars().all()
    for spending in spendings:      
        spent_money += spending.amount
       
    minor_stages = db.session.execute(db.select(MinorStage).filter_by(major_stage_id=major_stage_costs.major_stage_id)).scalars().all()
    for minor_stage in minor_stages:
        minor_stage_costs = db.session.execute(db.select(Costs).filter_by(minor_stage_id=minor_stage.id)).scalars().first()
        updated_minor_stage_costs = calculate_minor_stage_costs(minor_stage_costs)
        spent_money += updated_minor_stage_costs.spent_money
  
    major_stage_costs.spent_money = spent_money
    major_stage_costs.money_exceeded = major_stage_costs.spent_money > major_stage_costs.budget
    db.session.commit()
    return major_stage_costs
    

def calculate_journey_costs(journey_costs):
    spent_money = 0
    
    major_stages = db.session.execute(db.select(MajorStage).filter_by(journey_id=journey_costs.journey_id)).scalars().all()
    for major_stage in major_stages:
        major_stage_costs = db.session.execute(db.select(Costs).filter_by(major_stage_id=major_stage.id)).scalars().first()
        updated_major_stage_cost = calculate_major_stage_costs(major_stage_costs)        
        spent_money += updated_major_stage_cost.spent_money
  
    journey_costs.spent_money = spent_money
    journey_costs.money_exceeded = journey_costs.spent_money > journey_costs.budget
    return db.session.commit()

tf = TimezoneFinder()

def calculate_time_zone_offset(lat, lng):
    target_timezone_str = tf.timezone_at(lng=lng, lat=lat)
    if not target_timezone_str:
        raise ValueError("Could not determine timezone for coordinates.")
    
    target_tz = pytz.timezone(target_timezone_str)
    now_utc = datetime.utcnow()
    
    # Get the offset of the target timezone from UTC at the current time
    target_offset = target_tz.utcoffset(now_utc)
    
    diff_hours = target_offset.total_seconds() / 3600

    return diff_hours
    
    
def get_local_currency(lat, lng):
    # Get country name by reverse geocoding
    geolocator = Nominatim(user_agent="travelbuddy")
    location = geolocator.reverse((lat, lng), language='en')
    if not location or 'country' not in location.raw['address']:
        return None

    country_name = location.raw['address']['country']

    # Get currency using CountryInfo
    try:
        country_info = CountryInfo(country_name)
        currency = country_info.currencies()[0]  # returns a list, take the first
    except Exception:
        currency = None

    currency_info = get_currency_info(currency) if currency else {'code': None, 'name': None, 'symbol': None}
    conversion_rate = get_conversion_rate(currency_info['code']) if currency_info['code'] else None
    if conversion_rate is not None:  
        return {'code': currency_info['code'], 'name': currency_info['name'], 'symbol': currency_info['symbol'], 'conversion_rate': conversion_rate}
    else:
        return {'code': None, 'name': None, 'symbol': None, 'conversion_rate': None}


c = CurrencyConverter()

from babel.numbers import get_currency_name, get_currency_symbol
from babel import Locale

def get_currency_info(currency_code, locale_str='en_US'):
    try:
        name = get_currency_name(currency_code, locale=locale_str)
        symbol = get_currency_symbol(currency_code, locale=locale_str)
        
        return {
            'code': currency_code,
            'name': name,
            'symbol': symbol
        }
    except Exception as e:
        return {
            'code': currency_code,
            'name': currency_code,
            'symbol': currency_code
        }


def get_all_currencies(current_user):
    try:
        currency_list = []
        
        # Get currencies from database for current user
        user_currencies = db.session.execute(db.select(Currency).filter_by(user_id=current_user)).scalars().all()
        for currency in user_currencies:
            currency_list.append({
                'id': currency.id,
                'code': currency.code,
                'name': currency.name,
                'symbol': currency.symbol,
                'conversionRate': currency.conversion_rate
            })
        
        # Get currencies from CurrencyConverter
        currencies = c.currencies
        
        for currency_code in sorted(currencies):
            # Check if currency already exists in list
            if not any(c['code'] == currency_code for c in currency_list):
                info = get_currency_info(currency_code)
                conversion_rate = get_conversion_rate(currency_code)
                
                if conversion_rate is not None:
                    currency_list.append({
                        'code': info['code'],
                        'name': info['name'],
                        'symbol': info['symbol'],
                        'conversionRate': conversion_rate
                    })
        
        return currency_list
    except Exception as e:
        print(f"Error fetching currencies: {e}")
        return None


def get_conversion_rate(currency_code, base_currency='EUR'):
    try:
        rate = c.convert(1, base_currency, currency_code)
        return rate
    except Exception as e:
        return None


def safe_countryinfo_attr(obj, attr, join=False):
    try:
        value = getattr(obj, attr)
        if callable(value):
            value = value()
        # Only use if not a dictionary
        if value and not isinstance(value, dict):
            if join and isinstance(value, (list, tuple)):
                return ', '.join(str(v) for v in value)
            return value
    except Exception:
        return None
    return None


def get_users_stages_titles(current_user):
    assigned_titles = []
    
    journeys = db.session.execute(db.select(Journey).filter_by(user_id=current_user)).scalars().all()
    for journey in journeys:
        assigned_titles.append(journey.name)
        major_stages = db.session.execute(db.select(MajorStage).filter_by(journey_id=journey.id)).scalars().all()
        for major_stage in major_stages:
            assigned_titles.append(major_stage.title)
            minor_stages = db.session.execute(db.select(MinorStage).filter_by(major_stage_id=major_stage.id)).scalars().all()
            for minor_stage in minor_stages:
                assigned_titles.append(minor_stage.title)

    return assigned_titles