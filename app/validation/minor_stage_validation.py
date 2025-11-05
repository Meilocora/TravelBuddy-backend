from datetime import datetime
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

class MinorStageValidation(Validation):
  def __init__(self):
    super().__init__()
    
  
  @staticmethod
  def validate_minor_stage(minorStage, existing_minor_stages, existing_minor_stages_costs, major_stage_costs, assigned_titles, old_minor_stage=None):
        errors = False
      
        for key, value in minorStage.items():
            if key != 'accommodation_name' and key != 'accommodation_place' and key != 'accommodation_costs' and key != 'accommodation_link' and key != 'accommodation_latitude' and key != 'accommodation_longitude' and key != 'unconvertedAmount':
                if value['value'] == "" or value['value'] == None:
                    minorStage[key]['errors'].append(f'Input is required')
                    minorStage[key]['isValid'] = False
                 
        title_val = MinorStageValidation().validate_string(minorStage['title']['value'], min_length=3, max_length=50)
        if title_val:
            minorStage['title']['errors'].append(f", {title_val}")
            minorStage['title']['isValid'] = False
            
        assigned_title_val = MinorStageValidation().validate_title(minorStage['title']['value'], assigned_titles)
        if assigned_title_val and old_minor_stage and minorStage['title']['value'] != old_minor_stage.title:
            minorStage['title']['errors'].append(f", {assigned_title_val}")
            minorStage['title']['isValid'] = False

        # TODO: Das entfernen oder es soll nur eine Warnung geben
        # for existing_minor_stage in existing_minor_stages:
        #     start_val = MinorStageValidation().check_for_overlap(minorStage['scheduled_start_time']['value'], existing_minor_stage.scheduled_start_time, existing_minor_stage.scheduled_end_time, existing_minor_stage.title)
        #     if start_val:   
        #         minorStage['scheduled_start_time']['errors'].append(f", {start_val}")             
        #         minorStage['scheduled_start_time']['isValid'] = False
                
        #     end_val = MinorStageValidation().check_for_overlap(minorStage['scheduled_end_time']['value'], existing_minor_stage.scheduled_start_time, existing_minor_stage.scheduled_end_time, existing_minor_stage.title)
        #     if end_val:
        #         minorStage['scheduled_end_time']['errors'].append(f", {end_val}")
        #         minorStage['scheduled_end_time']['isValid'] = False
            
        # start_val = MinorStageValidation().validate_date(minorStage['scheduled_start_time']['value'])
        # if start_val:
        #     minorStage['scheduled_start_time']['errors'].append(f", {start_val}")
        #     minorStage['scheduled_start_time']['isValid'] = False
        
        # end_val = MinorStageValidation().validate_date(minorStage['scheduled_end_time']['value'])
        # if end_val:
        #     minorStage['scheduled_end_time']['errors'].append(f", {end_val}")
        #     minorStage['scheduled_end_time']['isValid'] = False
            
        # start_end_val = MinorStageValidation().compare_dates(minorStage['scheduled_start_time']['value'], minorStage['scheduled_end_time']['value'])
        # if start_end_val:
        #     minorStage['scheduled_start_time']['errors'].append(f", {start_end_val}")
        #     minorStage['scheduled_start_time']['isValid'] = False
        
        # if minorStage['accommodation_place']['value'] != "":        
        #     acc_place_val = MinorStageValidation().validate_string(minorStage['accommodation_place']['value'], max_length=50)
        #     if acc_place_val:
        #         minorStage['accommodation_place']['errors'].append(f", {acc_place_val}")
        #         minorStage['accommodation_place']['isValid'] = False

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
        else:
            minor_stages_budget = float(minorStage['budget']['value'])
            major_stage_budget = major_stage_costs.budget
            
            if existing_minor_stages_costs and existing_minor_stages_costs[0] != None:
                for existing_minor_stage_costs in existing_minor_stages_costs:
                    minor_stages_budget += existing_minor_stage_costs.budget
            if minor_stages_budget > major_stage_budget:
                max_available_money = major_stage_budget - minor_stages_budget + float(minorStage['budget']['value'])
                max_available_money_str = locale.currency(max_available_money, grouping=True)
                minorStage['budget']['errors'].append(f", Max available amount for major stage: {max_available_money_str}")
                minorStage['budget']['isValid'] = False
            
        for key, value in minorStage.items():
            if 'errors' in value and value['errors']:
                errors = True
                break
                
        return minorStage, not errors