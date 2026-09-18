import locale

from app.validation.validation import Validation

# Set German locale with fallback for different operating systems
try:
    # Try Windows German locale first
    locale.setlocale(locale.LC_ALL, 'German_Germany.1252')
except locale.Error:
    try:
        # Try Unix/Linux German locale
        locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
    except locale.Error:
        try:
            # Try shorter German locale
            locale.setlocale(locale.LC_ALL, 'de_DE')
        except locale.Error:
            # Fall back to system default
            locale.setlocale(locale.LC_ALL, '')

class MajorStageValidation(Validation):
  def __init__(self):
    super().__init__()
    
  
  @staticmethod
  def validate_major_stage(majorStage, existing_major_stages, existing_major_stages_costs, journey_costs, assigned_titles, journey):
        errors = False
      
        for key, value in majorStage.items():
            if key != 'additional_info' and key != 'scheduled_start_time' and key != 'scheduled_end_time':
                if value['value'] == "" or value['value'] == None:
                    value['errors'].append('Input is required')
                    majorStage[key]['isValid'] = False
            
                 
        title_val = MajorStageValidation().validate_string(majorStage['title']['value'], min_length=3, max_length=50)
        if title_val:
            majorStage['title']['errors'].append(f", {title_val}")
            majorStage['title']['isValid'] = False

        assigned_title_val = MajorStageValidation().validate_title(majorStage['title']['value'], assigned_titles)
        if assigned_title_val:
            majorStage['title']['errors'].append(f", {assigned_title_val}")
            majorStage['title']['isValid'] = False


        info_val = MajorStageValidation().validate_string(majorStage['additional_info']['value'], min_length=0, max_length=1000)
        if info_val:
            majorStage['additional_info']['errors'].append(f", {info_val}")
            majorStage['additional_info']['isValid'] = False
            
        duration_days_val = MajorStageValidation().validate_duration_days(majorStage['duration_days']['value'])
        if duration_days_val:
            majorStage['duration_days']['errors'].append(f", {duration_days_val}")
            majorStage['duration_days']['isValid'] = False
          
        stage_duration_val = MajorStageValidation().validate_stage_duration(journey.duration_days, [major_stage.duration_days for major_stage in existing_major_stages] + [majorStage['duration_days']['value']])
        if stage_duration_val:
            majorStage['duration_days']['errors'].append(f", {stage_duration_val}")
            majorStage['duration_days']['isValid'] = False

        money_val = MajorStageValidation().validate_amount(majorStage['budget']['value'])
        if money_val:
            majorStage['budget']['errors'].append(f", {money_val}")
            majorStage['budget']['isValid'] = False
        else: 
            major_stages_budget = float(majorStage['budget']['value'])
            journey_budget = journey_costs.budget
            for existing_major_stage_costs in existing_major_stages_costs:
                if existing_major_stage_costs == None:
                    continue
                major_stages_budget += existing_major_stage_costs.budget
            if major_stages_budget > journey_budget:
                max_available_money = journey_budget - major_stages_budget + float(majorStage['budget']['value'])
                max_available_money_str = locale.currency(max_available_money, grouping=True)
                majorStage['budget']['errors'].append(f", Max available amount for journey: {max_available_money_str}")
                majorStage['budget']['isValid'] = False
            
        for key, value in majorStage.items():
            if value.get('errors'):
                errors = True
                break
        
     
        return majorStage, not errors
     
  
  @staticmethod
  def validate_major_stage_update(majorStage, existing_major_stages, existing_major_stages_costs, journey_costs, minor_stages, assigned_titles, old_major_stage, journey):
        errors = False
      
        for key, value in majorStage.items():
            if key != 'additional_info' and key != 'scheduled_start_time' and key != 'scheduled_end_time':
                if value['value'] == "" or value['value'] == None:
                    value['errors'].append('Input is required')
                    majorStage[key]['isValid'] = False
            
                 
        title_val = MajorStageValidation().validate_string(majorStage['title']['value'], min_length=3, max_length=50)
        if title_val:
            majorStage['title']['errors'].append(f", {title_val}")
            majorStage['title']['isValid'] = False
            
        assigned_title_val = MajorStageValidation().validate_title(majorStage['title']['value'], assigned_titles)
        if assigned_title_val and majorStage['title']['value'] != old_major_stage.title:
            majorStage['title']['errors'].append(f", {assigned_title_val}")
            majorStage['title']['isValid'] = False
            
           
        info_val = MajorStageValidation().validate_string(majorStage['additional_info']['value'], min_length=0, max_length=1000)
        if info_val:
            majorStage['additional_info']['errors'].append(f", {title_val}")
            majorStage['additional_info']['isValid'] = False            
                      
        duration_days_val = MajorStageValidation().validate_duration_days(majorStage['duration_days']['value'])
        if duration_days_val:
            majorStage['duration_days']['errors'].append(f", {duration_days_val}")
            majorStage['duration_days']['isValid'] = False
            
        stage_duration_val = MajorStageValidation().validate_stage_duration(journey.duration_days, [major_stage.duration_days for major_stage in existing_major_stages] + [majorStage['duration_days']['value']])
        if stage_duration_val:
            majorStage['duration_days']['errors'].append(f", {stage_duration_val}")
            majorStage['duration_days']['isValid'] = False
                    
        minor_duration_val = MajorStageValidation().validate_stage_duration(majorStage['duration_days']['value'],[minor_stage.duration_days for minor_stage in minor_stages])
        if minor_duration_val:
            majorStage['duration_days']['errors'].append(f", {minor_duration_val}")
            majorStage['duration_days']['isValid'] = False
                    
        money_val = MajorStageValidation().validate_amount(majorStage['budget']['value'])
        if money_val:
            majorStage['budget']['errors'].append(f", {money_val}")
            majorStage['budget']['isValid'] = False
        else:    
            major_stages_budget = float(majorStage['budget']['value'])
            journey_budget = journey_costs.budget
            for existing_major_stage_costs in existing_major_stages_costs:
                major_stages_budget += existing_major_stage_costs.budget
            if major_stages_budget > journey_budget:
                max_available_money = journey_budget - major_stages_budget + float(majorStage['budget']['value'])
                max_available_money_str = locale.currency(max_available_money, grouping=True)
                majorStage['budget']['errors'].append(f", Max available amount for journey: {max_available_money_str}")
                majorStage['budget']['isValid'] = False
            
        for key, value in majorStage.items():
            if value.get('errors'):
                errors = True
                break
        
     
        return majorStage, not errors