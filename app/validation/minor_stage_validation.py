from app.validation.validation import Validation

class MinorStageValidation(Validation):
  def __init__(self):
    super().__init__()
    
  
  @staticmethod
  def validate_minor_stage(minorStage, existing_minor_stages, existing_minor_stages_costs, major_stage_costs, assigned_titles, major_stage, old_minor_stage=None):
        errors = False
      
        for key, value in minorStage.items():
            if key != 'accommodation_name' and key != 'accommodation_place' and key != 'accommodation_costs' and key != 'accommodation_link' and key != 'accommodation_latitude' \
                and key != 'accommodation_longitude' and key != 'unconvertedAmount' and key != 'scheduled_start_time' and key != 'scheduled_end_time':
                if value['value'] == "" or value['value'] == None:
                    value['errors'].append('Input is required')
                    minorStage[key]['isValid'] = False
                 
        title_val = MinorStageValidation().validate_string(minorStage['title']['value'], min_length=3, max_length=50)
        if title_val:
            minorStage['title']['errors'].append(f", {title_val}")
            minorStage['title']['isValid'] = False
            
        assigned_title_val = MinorStageValidation().validate_title(minorStage['title']['value'], assigned_titles)
        if assigned_title_val and old_minor_stage and minorStage['title']['value'] != old_minor_stage.title:
            minorStage['title']['errors'].append(f", {assigned_title_val}")
            minorStage['title']['isValid'] = False
                      
        duration_days_raw = minorStage['duration_days']['value']
        duration_days_val = MinorStageValidation().validate_duration_days(duration_days_raw)
        if duration_days_val:
            minorStage['duration_days']['errors'].append(f", {duration_days_val}")
            minorStage['duration_days']['isValid'] = False  

        if not duration_days_val:
            duration_days = int(duration_days_raw)
            stage_duration_val = MinorStageValidation().validate_stage_duration(major_stage.duration_days, [minor_stage.duration_days for minor_stage in existing_minor_stages] + [duration_days])
            if stage_duration_val:
                minorStage['duration_days']['errors'].append(f", {stage_duration_val}")
                minorStage['duration_days']['isValid'] = False
                
        if minorStage['accommodation_place']['value'] != "":        
            acc_place_val = MinorStageValidation().validate_string(minorStage['accommodation_place']['value'], max_length=50)
            if acc_place_val:
                minorStage['accommodation_place']['errors'].append(f", {acc_place_val}")
                minorStage['accommodation_place']['isValid'] = False

        if minorStage['accommodation_link']['value'] != "":
            acc_link_val = MinorStageValidation().validate_hyperlink(minorStage['accommodation_link']['value'])
            if acc_link_val:
                minorStage['accommodation_link']['errors'].append(f", {acc_link_val}")
            minorStage['accommodation_link']['isValid'] = False
        
        if minorStage['accommodation_costs']['value'] != "":    
            acc_costs_val = MinorStageValidation().validate_amount(minorStage['accommodation_costs']['value'])
            if acc_costs_val:
                minorStage['accommodation_costs']['errors'].append(f", {acc_costs_val}")
                minorStage['accommodation_costs']['isValid'] = False
            
        money_val = MinorStageValidation().validate_amount(minorStage['budget']['value'])
        if money_val:
            minorStage['budget']['errors'].append(f", {money_val}")
            minorStage['budget']['isValid'] = False
            
        for key, value in minorStage.items():
            if value.get('errors'):
                errors = True
                break
                
        return minorStage, not errors