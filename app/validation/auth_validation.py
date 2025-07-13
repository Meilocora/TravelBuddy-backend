from app.models import User 
from app.validation.validation import Validation
import bcrypt

class AuthValidation(Validation):
  def __init__(self):
    super().__init__()
    
     
  @staticmethod
  def validate_signUp(signUpData):
        errors = False
    
        for key, value in signUpData.items():
            try: 
                if value['value'] == "" or value['value'] == None:
                    signUpData[key]['errors'].append(f'Input is required')
                    signUpData[key]['isValid'] = False
            except KeyError:
                signUpData['username']['errors'].append(f", Inputs is required")
                signUpData['username']['isValid'] = False
                errors = True
                return signUpData, not errors
        
        userNameInvalid = AuthValidation().validate_string(signUpData['username']['value'], min_length=3, max_length=20)
        if userNameInvalid:
            signUpData['username']['errors'].append(f", {userNameInvalid}")
            signUpData['username']['isValid'] = False
                
        # emailInvalid = AuthValidation().validate_email(signUpData['email']['value'])
        # if emailInvalid:
            # signUpData['email']['errors'].append(f", {emailInvalid}")
            # signUpData['email']['isValid'] = False
            
        # passwordInvalid = AuthValidation().validate_password(signUpData['password']['value'], min_length=6, max_length=20)
        # if passwordInvalid:
        #     print(passwordInvalid.split(', '))
        #     signUpData['password']['errors'] += passwordInvalid.split(', ')
        #     signUpData['password']['isValid'] = False
                
        for key, value in signUpData.items():
            if 'errors' in value and value['errors']:
                errors = True
                break
        
        return signUpData, not errors
    
    
  @staticmethod
  def validate_change_username(nameChangeData, currentUserData):
        errors = False
    
        for key, value in nameChangeData.items():
            try: 
                if value['value'] == "" or value['value'] == None:
                    nameChangeData[key]['errors'].append(f'Input is required')
                    nameChangeData[key]['isValid'] = False
            except KeyError:
                nameChangeData['username']['errors'].append(f", Inputs is required")
                nameChangeData['username']['isValid'] = False
                errors = True
                return nameChangeData, not errors

        existing_user = User.query.filter_by(username=nameChangeData['newUsername']['value']).first()
        if existing_user:
            nameChangeData['newUsername']['errors'].append("Username is already taken")
            nameChangeData['newUsername']['isValid'] = False
            errors = True

        userNameInvalid = AuthValidation().validate_string(nameChangeData['newUsername']['value'], min_length=3, max_length=20)
        if userNameInvalid:
            nameChangeData['newUsername']['errors'].append(f", {userNameInvalid}")
            nameChangeData['newUsername']['isValid'] = False
            
        passwordValid = bcrypt.checkpw(nameChangeData['password']['value'].encode('utf-8'), currentUserData.password.encode('utf-8'))
        if not passwordValid:
            nameChangeData['password']['errors'].append("Password is incorrect")
            nameChangeData['password']['isValid'] = False
            errors = True

        for key, value in nameChangeData.items():
            if 'errors' in value and value['errors']:
                errors = True
                break

        return nameChangeData, not errors
    
    
  @staticmethod
  def validate_change_password(passwordChangeData, currentUserData):
        errors = False

        for key, value in passwordChangeData.items():
            try:
                if value['value'] == "" or value['value'] == None:
                    passwordChangeData[key]['errors'].append(f'Input is required')
                    passwordChangeData[key]['isValid'] = False
            except KeyError:
                passwordChangeData['currentPassword']['errors'].append(f", Inputs is required")
                passwordChangeData['currentPassword']['isValid'] = False
                errors = True
                return passwordChangeData, not errors

        if passwordChangeData['newPassword']['value'] != passwordChangeData['confirmPassword']['value']:
            passwordChangeData['confirmPassword']['errors'].append("Passwords do not match")
            passwordChangeData['confirmPassword']['isValid'] = False
            errors = True

        # newPasswordInvalid = AuthValidation().validate_password(passwordChangeData['newPassword']['value'], min_length=6, max_length=20)
        # if passwordInvalid:
        #     passwordChangeData['newPassword']['errors'] += passwordInvalid.split(', ')
        #     passwordChangeData['newPassword']['isValid'] = False

        passwordValid = bcrypt.checkpw(passwordChangeData['oldPassword']['value'].encode('utf-8'), currentUserData.password)        
       
        if not passwordValid:
            passwordChangeData['oldPassword']['errors'].append("Password is incorrect")
            passwordChangeData['oldPassword']['isValid'] = False
            errors = True

        for key, value in passwordChangeData.items():
            if 'errors' in value and value['errors']:
                errors = True
                break

        return passwordChangeData, not errors
     
        
     
