from datetime import datetime
import locale
from db import db
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
  def validate_major_stage(majorStage, existing_major_stages, existing_major_stages_costs, journey_costs, assigned_titles):
        errors = False
      
        for key, value in majorStage.items():
            if key != 'additional_info':
                if value['value'] == "" or value['value'] == None:
                    majorStage[key]['errors'].append(f'Input is required')
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
            majorStage['additional_info']['errors'].append(f", {title_val}")
            majorStage['additional_info']['isValid'] = False
        
        # TODO: Das entfernen oder es soll nur eine Warnung geben
        # for existing_major_stage in existing_major_stages:
        #     start_val = MajorStageValidation().check_for_overlap(majorStage['scheduled_start_time']['value'], existing_major_stage.scheduled_start_time, existing_major_stage.scheduled_end_time, existing_major_stage.title)
        #     if start_val:   
        #         majorStage['scheduled_start_time']['errors'].append(f", {start_val}")             
        #         majorStage['scheduled_start_time']['isValid'] = False
                
        #     end_val = MajorStageValidation().check_for_overlap(majorStage['scheduled_end_time']['value'], existing_major_stage.scheduled_start_time, existing_major_stage.scheduled_end_time, existing_major_stage.title)
        #     if end_val:
        #         majorStage['scheduled_end_time']['errors'].append(f", {end_val}")
        #         majorStage['scheduled_end_time']['isValid'] = False
        
          
        start_val = MajorStageValidation().validate_date(majorStage['scheduled_start_time']['value'])
        if start_val:
            majorStage['scheduled_start_time']['errors'].append(f", {start_val}")
            majorStage['scheduled_start_time']['isValid'] = False
        
        end_val = MajorStageValidation().validate_date(majorStage['scheduled_end_time']['value'])
        if end_val:
            majorStage['scheduled_end_time']['errors'].append(f", {end_val}")
            majorStage['scheduled_end_time']['isValid'] = False
            
        start_end_val = MajorStageValidation().compare_dates(majorStage['scheduled_start_time']['value'], majorStage['scheduled_end_time']['value'])
        if start_end_val:
            majorStage['scheduled_start_time']['errors'].append(f", {start_end_val}")
            majorStage['scheduled_start_time']['isValid'] = False
            
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
            if 'errors' in value and value['errors']:
                errors = True
                break
        
     
        return majorStage, not errors
     
  
  @staticmethod
  def validate_major_stage_update(majorStage, existing_major_stages, existing_major_stages_costs, journey_costs, minor_stages, assigned_titles, old_major_stage):
        errors = False
      
        for key, value in majorStage.items():
            if key != 'additional_info':
                if value['value'] == "" or value['value'] == None:
                    majorStage[key]['errors'].append(f'Input is required')
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
        
        # TODO: Das entfernen oder es soll nur eine Warnung geben
        # for existing_major_stage in existing_major_stages:
        #     start_val = MajorStageValidation().check_for_overlap(majorStage['scheduled_start_time']['value'], existing_major_stage.scheduled_start_time, existing_major_stage.scheduled_end_time, existing_major_stage.title)
        #     if start_val:   
        #         majorStage['scheduled_start_time']['errors'].append(f", {start_val}")             
        #         majorStage['scheduled_start_time']['isValid'] = False
                
        #     end_val = MajorStageValidation().check_for_overlap(majorStage['scheduled_end_time']['value'], existing_major_stage.scheduled_start_time, existing_major_stage.scheduled_end_time, existing_major_stage.title)
        #     if end_val:
        #         majorStage['scheduled_end_time']['errors'].append(f", {end_val}")
        #         majorStage['scheduled_end_time']['isValid'] = False
                
        # for minor_stage in minor_stages:
        #     start_val = MajorStageValidation().check_for_inferior_collision(majorStage['scheduled_start_time']['value'], minor_stage.scheduled_start_time, minor_stage.scheduled_end_time, minor_stage.title)
        #     if start_val:   
        #         majorStage['scheduled_start_time']['errors'].append(f", {start_val}")             
        #         majorStage['scheduled_start_time']['isValid'] = False
                
        #     end_val = MajorStageValidation().check_for_inferior_collision(majorStage['scheduled_end_time']['value'], minor_stage.scheduled_start_time, minor_stage.scheduled_end_time, minor_stage.title)
        #     if end_val:
        #         majorStage['scheduled_end_time']['errors'].append(f", {end_val}")
        #         majorStage['scheduled_end_time']['isValid'] = False
            
            
        start_val = MajorStageValidation().validate_date(majorStage['scheduled_start_time']['value'])
        if start_val:
            majorStage['scheduled_start_time']['errors'].append(f", {start_val}")
            majorStage['scheduled_start_time']['isValid'] = False
        
        end_val = MajorStageValidation().validate_date(majorStage['scheduled_end_time']['value'])
        if end_val:
            majorStage['scheduled_end_time']['errors'].append(f", {end_val}")
            majorStage['scheduled_end_time']['isValid'] = False
            
        start_end_val = MajorStageValidation().compare_dates(majorStage['scheduled_start_time']['value'], majorStage['scheduled_end_time']['value'])
        if start_end_val:
            majorStage['scheduled_start_time']['errors'].append(f", {start_end_val}")
            majorStage['scheduled_start_time']['isValid'] = False
            
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
            if 'errors' in value and value['errors']:
                errors = True
                break
        
     
        return majorStage, not errors