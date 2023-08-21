import os
import sqlite3
import pandas as pd
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.widgets import PasswordInput
from wtforms import (StringField, TextAreaField, IntegerField, PasswordField, SelectField, BooleanField,
                     DateField, SubmitField, EmailField, FloatField, SelectMultipleField, DateTimeLocalField,
                     validators, widgets)
from wtforms.validators import InputRequired, Length, NumberRange, Optional, Email, optional

from .utils import get_analyst_lst, get_filter_items, get_name
from .config import USER_ADMIN_PATH


class SignupForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    email = EmailField('Email address', 
                       validators=[InputRequired("Please enter your email address."), 
                                   Email("This field requires a valid email address")])
    # password = StringField('Password', validators=[InputRequired()])
    pwd1 = PasswordField('Password', [
        validators.DataRequired(), 
        validators.Length(min=8), 
        validators.Regexp(regex="^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$", message="Password must contain at least one uppercase letter, one lowercase letter, and one digit.")
    ])
    pwd2 = PasswordField('Confirm Password', [validators.DataRequired(), validators.EqualTo("pwd1", message="Passwords must match.")])
    
    signup_btn = SubmitField('Sign Up')
    back_btn = SubmitField('Back to Log In')


class ForgotForm(FlaskForm):
    email = EmailField('Email address', 
                       validators=[InputRequired("Please enter your email address."), 
                                   Email("This field requires a valid email address")])
    reset_btn = SubmitField('Send Email')


class VerificationForm(FlaskForm):
    verify_code = StringField('Verification Code', validators=[InputRequired()])
    confirm_btn = SubmitField('Confirm')


class ResetPWDForm(FlaskForm):
    pwd1 = PasswordField('Password', [
        validators.DataRequired(), 
        validators.Length(min=8), 
        validators.Regexp(regex="^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$", message="Password must contain at least one uppercase letter, one lowercase letter, and one digit.")
    ])
    pwd2 = PasswordField('Confirm Password', [validators.DataRequired(), validators.EqualTo("pwd1", message="Passwords must match.")])
    confirm_btn = SubmitField('Confirm')


class AdminManageForm(FlaskForm):
    
    conn = sqlite3.connect(USER_ADMIN_PATH)
    user_lst = pd.read_sql(f"SELECT Name from User_Info", conn)["Name"].tolist()
    conn.close()
    
    user_lst = sorted([get_name(user_name=name) for name in user_lst])
    
    username = SelectField(
        'Username', 
        choices=user_lst,
        validators=[InputRequired()])
    
    add_or_revoke = SelectField(
        'Action', 
        choices=['Add', 'Revoke', "Delete User"], default="Add",
        validators=[InputRequired()])
    
    permission_type = SelectField(
        'Type', 
        choices=[
            ('Edit_authority', "Edit Authority"), ('Data_analyst', "Data Analyst"), ('Research_analyst', "Research Analyst"), ('Report_analyst', "Report Analyst"), 
            ("RFI_analyst", "RFI Analyst"), ('KYC_analyst', "KYC Analyst"), ('QC_analyst', "QC Analyst"), ('FID_client', "FID Client"), ('FID_BSA_officer', "FID BSA Officer"), 
            ('EDD_head_approver', "EDD Head Approver"), ('Admin_manager', "Admin")
            ], default="Edit",
        validators=[InputRequired()])
    
    enter_btn = SubmitField('ENTER')


#============================= Case Form =====================================================
class FindSimilarCase(FlaskForm):
    customer_id = TextAreaField('Use Customer ID to find Similar Case', validators=[Optional()])
    find_btn = SubmitField('Search')


class NewCaseForm(FlaskForm):
    customer_id = TextAreaField('Customer ID', validators=[InputRequired()])
    customer_name = TextAreaField('Customer Name', validators=[InputRequired(), Length(min=1)])
    risk_rating = SelectField(
        'Risk Rating', choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')], validators=[InputRequired()])
    kyc_refresh_date = DateField('KYC Refresh Date', format='%Y-%m-%d', validators=[InputRequired()])
    
    customer_type = SelectField(
        'Customer Type', 
        choices=[('DCB', 'DCB'), ('FCB', 'FCB'), ('NBFI', 'NBFI'), ('NBFI-TSD', 'NBFI-TSD'), ('SPV', 'SPV')], validators=[InputRequired()])
    case_type = SelectField(
        'Case Type', 
        choices=[
            ('BAU Review', 'BAU Review'), ('Simplified Review', 'Simplified Review'), # RMB Review
            ('Special Review', 'Special Review'), ('Trigger Event', 'Trigger Event')], validators=[InputRequired()])
    category = StringField('Category', validators=[InputRequired(), Length(min=1, max=100)])
    comment = TextAreaField('Comment', validators=[Optional(), Length(min=0, max=2000)])
    create_case = SubmitField('Create New Case')


class NewRMBCaseForm(FlaskForm):
    customer_id = TextAreaField('Customer ID', validators=[InputRequired()])
    customer_name = TextAreaField('Customer Name', validators=[InputRequired(), Length(min=1)])
    risk_rating = SelectField(
        'Risk Rating', choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')], validators=[InputRequired()])
    # kyc_refresh_date = DateField('KYC Refresh Date', format='%Y-%m-%d', validators=[InputRequired()])
    
    sc_start_date = DateField('Scheduled Start', format='%Y-%m-%d', validators=[InputRequired()])
    sc_end_date = DateField('Scheduled End', format='%Y-%m-%d', validators=[InputRequired()])
    txn_start_date = DateField('Transaction Start', format='%Y-%m-%d', validators=[InputRequired()])
    txn_end_date = DateField('Transaction End', format='%Y-%m-%d', validators=[InputRequired()])
    
    customer_type = SelectField(
        'Customer Type', 
        choices=[('DCB', 'DCB'), ('FCB', 'FCB'), ('NBFI', 'NBFI'), ('NBFI-TSD', 'NBFI-TSD'), ('SPV', 'SPV')], validators=[InputRequired()])

    category = StringField('Category', validators=[InputRequired(), Length(min=1, max=100)])
    comment = TextAreaField('Comment', validators=[Optional(), Length(min=0, max=2000)])
    create_rmb_case = SubmitField('Create RMB Case')
    
    
class NewCICCaseForm(FlaskForm):
    customer_name = TextAreaField('Customer Name', validators=[InputRequired(), Length(min=1)], default="CIC Consolidation")
    sc_start_date = DateField('Scheduled Start', format='%Y-%m-%d', validators=[InputRequired()])
    sc_end_date = DateField('Scheduled End', format='%Y-%m-%d', validators=[InputRequired()])
    txn_start_date = DateField('Transaction Start', format='%Y-%m-%d', validators=[InputRequired()])
    txn_end_date = DateField('Transaction End', format='%Y-%m-%d', validators=[InputRequired()])
    category = StringField('Category', validators=[InputRequired(), Length(min=1, max=100)], default="CIC")
    case_type = SelectField(
        'Case Type', 
        choices=[
            ('BAU Review', 'BAU Review'), ('Simplified Review', 'Simplified Review'), # RMB Review
            ('Special Review', 'Special Review'), ('Trigger Event', 'Trigger Event')], validators=[InputRequired()])
    create_cic_case = SubmitField('Create CIC Case')
    

#============================= Create CIC Case Form =====================================================
class AddCICForm(FlaskForm):
    case_id = IntegerField('Case ID', validators=[Optional()], render_kw={"disabled": "disabled"})
    cic_case_id = IntegerField('CIC Case ID', validators=[Optional()], render_kw={"disabled": "disabled"})
    cic_customer_id = TextAreaField('CIC Customer ID', validators=[InputRequired()])
    cic_customer_name = TextAreaField('CIC Customer Name', validators=[InputRequired(), Length(min=1)])
    risk_rating = SelectField(
        'Risk Rating', choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')], validators=[InputRequired()])
    kyc_refresh_date = DateField('KYC Refresh Date', format='%Y-%m-%d', validators=[InputRequired()])
    customer_type = SelectField(
        'Customer Type', 
        choices=[('DCB', 'DCB'), ('FCB', 'FCB'), ('NBFI', 'NBFI'), ('NBFI-TSD', 'NBFI-TSD'), ('SPV', 'SPV')], validators=[InputRequired()])
    default_comment = '''It is part of the CIC relationship. A consolidated EDD review will be performed per calendar year. FID requires to re-align the KYC due dates to be in-line with the EDD report due dates.'''
    comment = TextAreaField('Comment', validators=[Optional(), Length(min=0, max=2000)], default=default_comment)
    create_cic_case = SubmitField('Create CIC-sub-case')
    remove_cic_case = SubmitField('Remove CIC-sub-case')


#============================= Preview Case Form =====================================================
class FilterCase(FlaskForm):
    case_id_lst, due_date_lst, customer_name_lst = get_filter_items("case")
    
    case_id_sel = SelectMultipleField('Case ID', choices=list(zip(case_id_lst, case_id_lst)), validators=[Optional()])
    case_due_date_sel = SelectMultipleField('Case Due Date', choices=list(zip(due_date_lst, due_date_lst)), validators=[Optional()])
    customer_name_sel = SelectMultipleField('Customer Name', choices=list(zip(customer_name_lst, customer_name_lst)), validators=[Optional()])
    case_status_sel = SelectMultipleField('Case Status', choices=[
        ('Initialized', 'Initialized'), ('Data', 'Data'), ('Research', 'Research'), ('Report', 'Report'), 
        ('Recommendation & Referral', 'Recommendation & Referral'), ('Closed', 'Closed'), ('Removed', 'Removed')], validators=[Optional()])
    filter_cases = SubmitField('Search')
    export_cases = SubmitField('Export')
    
    
#============================= Working Case Form =====================================================
class WorkingCaseForm(FlaskForm):
    customer_id = TextAreaField('Customer ID', validators=[InputRequired(), Length(min=1)])
    customer_name = TextAreaField('Customer Name', validators=[InputRequired(), Length(min=1)])
    customer_type = SelectField(
        'Customer Type', 
        choices=[('DCB', 'DCB'), ('FCB', 'FCB'), ('NBFI', 'NBFI'), ('NBFI-TSD', 'NBFI-TSD'), ('SPV', 'SPV')], 
        validators=[InputRequired()])
    
    category = StringField('Category', validators=[Length(min=0, max=100)])
    risk_rating = SelectField(
        'Risk Rating', choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')], validators=[InputRequired()])
    case_type = SelectField(
        'Case Type', 
        choices=['BAU Review', 'Simplified Review', 'Special Review', 'Trigger Event'], 
        validators=[InputRequired()])
    
    kyc_refresh_date = DateField('KYC Refresh Date', format='%Y-%m-%d', validators=[InputRequired()])
    sc_start_date = DateField('Scheduled Start Date', format='%Y-%m-%d', validators=[Optional()], render_kw={"disabled": "disabled"})
    sc_end_date = DateField('Scheduled End Date', format='%Y-%m-%d', validators=[Optional()], render_kw={"disabled": "disabled"})
    txn_start_date = DateField('Transaction Start Date', format='%Y-%m-%d', validators=[Optional()], render_kw={"disabled": "disabled"})
    txn_end_date = DateField('Transaction End Date', format='%Y-%m-%d', validators=[Optional()], render_kw={"disabled": "disabled"})
    case_status = StringField('Case Status', validators=[Optional()], render_kw={"disabled": "disabled"})
    
    comment = TextAreaField('Comment', validators=[Optional(), Length(min=0, max=2000)])
    
    update_btn = SubmitField('Update Case Info')
    work_btn = SubmitField('Work on Case')
    remove_btn = SubmitField('Remove Case')


class WorkingRMBCaseForm(FlaskForm):
    customer_id = TextAreaField('Customer ID', validators=[InputRequired(), Length(min=1)])
    customer_name = TextAreaField('Customer Name', validators=[InputRequired(), Length(min=1)])
    customer_type = SelectField(
        'Customer Type', 
        choices=[('DCB', 'DCB'), ('FCB', 'FCB'), ('NBFI', 'NBFI'), ('NBFI-TSD', 'NBFI-TSD'), ('SPV', 'SPV')], # RMB Review
        validators=[InputRequired()])
    
    category = StringField('Category', validators=[Length(min=0, max=100)])
    risk_rating = SelectField(
        'Risk Rating', choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')], validators=[InputRequired()])
    
    kyc_refresh_date = StringField('KYC Refresh Date', validators=[Optional()], render_kw={"disabled": "disabled"})
    sc_start_date = DateField('Scheduled Start Date', format='%Y-%m-%d', validators=[InputRequired()])
    sc_end_date = DateField('Scheduled End Date', format='%Y-%m-%d', validators=[InputRequired()])
    txn_start_date = DateField('Transaction Start Date', format='%Y-%m-%d', validators=[InputRequired()])
    txn_end_date = DateField('Transaction End Date', format='%Y-%m-%d', validators=[InputRequired()])
    case_type = StringField('Case Type', validators=[Optional()], render_kw={"disabled": "disabled"})
    case_status = StringField('Case Status', validators=[Optional()], render_kw={"disabled": "disabled"})
    
    comment = TextAreaField('Comment', validators=[Optional(), Length(min=0, max=2000)])
    
    update_rmb_btn = SubmitField('Update Case Info')
    work_rmb_btn = SubmitField('Work on Case')
    remove_rmb_btn = SubmitField('Remove Case')


class WorkingCICCaseForm(FlaskForm):
    customer_name = TextAreaField('Customer Name', validators=[InputRequired(), Length(min=1)])
    sc_start_date = DateField('Scheduled Start Date', format='%Y-%m-%d', validators=[InputRequired()])
    sc_end_date = DateField('Scheduled End Date', format='%Y-%m-%d', validators=[InputRequired()])
    txn_start_date = DateField('Transaction Start Date', format='%Y-%m-%d', validators=[InputRequired()])
    txn_end_date = DateField('Transaction End Date', format='%Y-%m-%d', validators=[InputRequired()])
    case_type = SelectField(
        'Case Type', 
        choices=[
            ('BAU Review', 'BAU Review'), ('Simplified Review', 'Simplified Review'), # RMB Review
            ('Special Review', 'Special Review'), ('Trigger Event', 'Trigger Event')], validators=[InputRequired()])
    comment = TextAreaField('Comment', validators=[Optional(), Length(min=0, max=2000)])
    
    case_status = StringField('Case Status', validators=[Optional()], render_kw={"disabled": "disabled"})
    category = StringField('Category', validators=[Optional(), Length(min=1, max=100)], default="CIC", render_kw={"disabled": "disabled"})
    
    update_cic_btn = SubmitField('Update CIC Case Info')
    add_sub_cic_btn = SubmitField('Add CIC-sub-case')
    work_cic_btn = SubmitField('Work on Case')
    remove_cic_btn = SubmitField('Remove Case')
    
    
class UpdateCaseStepForm(FlaskForm):    
    # Data
    data_date = DateField('Data Start Date', format='%Y-%m-%d', validators=[Optional()])
    analyst_lst = get_analyst_lst(role="Data_analyst")
    data_qc_analyst = SelectField(
        'Data QC Analyst', 
        choices=[(analyst, analyst) for analyst in analyst_lst] + [("", "")], default="",
        validators=[Optional()])
    
    # Data QC
    data_qc_complete_date = DateField('Data QC Complete Date', format='%Y-%m-%d', validators=[Optional()])
    analyst_lst = get_analyst_lst(role="Report_analyst")
    report_analyst = SelectField(
        'Report Analyst', 
        choices=[(analyst, analyst) for analyst in analyst_lst] + [("", "")], default="",
        validators=[Optional()])
    volume = IntegerField('Volume', validators=[Optional()])
    value = FloatField('Value', validators=[Optional()])
    currency = SelectField('Value Currency', choices=[('$', '$'), ('￥', '￥')], validators=[Optional()])
    sars_volume = IntegerField('SARs Volume', validators=[Optional()])
    high_risk_country_vol = FloatField('High Risk Country Vol%', validators=[Optional()])
    high_risk_country_val = FloatField('High Risk Country Val%', validators=[Optional()])
    
    # Research
    research_date = DateField('Research Start Date', format='%Y-%m-%d', validators=[Optional()])
    research_complete_date = DateField('Research Complete Date', format='%Y-%m-%d', validators=[Optional()])
    analyst_lst = get_analyst_lst(role="Research_analyst")
    research_qc_analyst = SelectField(
        'Research QC Analyst', 
        choices=[(analyst, analyst) for analyst in analyst_lst] + [("", "")], default="",
        validators=[Optional()])
    entity_volume = IntegerField('Entity Volume', validators=[Optional()])
    
    # Research QC
    research_qc_date = DateField('Research QC Start Date', format='%Y-%m-%d', validators=[Optional()])
    research_qc_complete_date = DateField('Research QC Complete Date', format='%Y-%m-%d', validators=[Optional()])
    
    # Report
    report_date = DateField('Report Start Date', format='%Y-%m-%d', validators=[Optional()])
    report_complete_date = DateField('Report Complete Date', format='%Y-%m-%d', validators=[Optional()])
    nested_value = FloatField('Nested Value', validators=[Optional()])
    nested_volume = IntegerField('Nested Volume', validators=[Optional()])
    
    # Report QC
    report_qc_date = DateField('Report QC Start Date', format='%Y-%m-%d', validators=[Optional()])
    report_qc_complete_date = DateField('Report QC Complete Date', format='%Y-%m-%d', validators=[Optional()])
    
    update_step_btn = SubmitField('Update Case Step Info')
    
#============================= Data Forms =====================================================
class DataStep(FlaskForm):
    data_date = DateField('Data Start Date', format='%Y-%m-%d', validators=[InputRequired()])
    data_btn = SubmitField('Data Started')
    

class SendDataQCStep(FlaskForm):
    analyst_lst = get_analyst_lst(role="Data_analyst")
    # 用了bootstrap模板后，似乎选择项中的""失效了
    data_qc_analyst = SelectField(
        'Data QC Analyst', 
        choices=[(analyst, analyst) for analyst in analyst_lst] + [("", "")], default="",
        validators=[InputRequired()])
    send_reminder_for_qc = SubmitField('Send Reminder for Data QC')    
    
    
#============================= Data QC Forms =====================================================
class DataQCCompleteStep(FlaskForm):
    data_qc_complete_date = DateField('Data QC Complete Date', format='%Y-%m-%d', validators=[InputRequired()])
    data_qc_complete_btn = SubmitField('Data QC Completed')
     
    
class SendResearchStep(FlaskForm):
    analyst_lst = get_analyst_lst(role="Report_analyst")
    report_analyst = SelectField(
        'Report Analyst', 
        choices=[(analyst, analyst) for analyst in analyst_lst] + [("", "")], default="",
        validators=[InputRequired()])
    
    volume = IntegerField('Volume', validators=[InputRequired()])
    value = FloatField('Value', validators=[InputRequired()])
    currency = SelectField('Value Currency', choices=[('$', '$'), ('￥', '￥')], validators=[InputRequired()])
    sars_volume = IntegerField('SARs Volume', validators=[InputRequired()])
    high_risk_country_vol = FloatField('High Risk Country Vol%', validators=[InputRequired()])
    high_risk_country_val = FloatField('High Risk Country Val%', validators=[InputRequired()])
    send_case_assignment = SubmitField('Send Case Assignment')


#============================= Research Forms =====================================================
class ResearchStep(FlaskForm):
    research_date = DateField('Research Start Date', format='%Y-%m-%d', validators=[InputRequired()])
    research_btn = SubmitField('Research Started')


class ResearchCompleteStep(FlaskForm):
    research_complete_date = DateField('Research Complete Date', format='%Y-%m-%d', validators=[InputRequired()])
    research_complete_btn = SubmitField('Research Completed')


class SendResearchQCStep(FlaskForm):
    analyst_lst = get_analyst_lst(role="Research_analyst")
    research_qc_analyst = SelectField(
        'Research QC Analyst', 
        choices=[(analyst, analyst) for analyst in analyst_lst] + [("", "")], default="",
        validators=[InputRequired()])
    entity_volume = IntegerField('Entity Volume', validators=[InputRequired()])
    send_reminder_for_qc = SubmitField('Send Reminder for Research QC')


#============================= Research QC Forms =====================================================
class ResearchQCStep(FlaskForm):
    research_qc_date = DateField('Research QC Start', format='%Y-%m-%d', validators=[InputRequired()])
    research_qc_btn = SubmitField('Research QC Started')


class ResearchQCCompleteStep(FlaskForm):
    research_qc_complete_date = DateField('Research QC Complete', format='%Y-%m-%d', validators=[InputRequired()])
    research_qc_complete_btn = SubmitField('Research QC Completed')
        
    
class SendReportStep(FlaskForm):
    remind_report_team = SubmitField('Remind Report Team')


#============================= Report Forms =====================================================
class ReportStep(FlaskForm):
    report_date = DateField('Report Start Date', format='%Y-%m-%d', validators=[InputRequired()])
    report_btn = SubmitField('Report Started')


class ReportCompleteStep(FlaskForm):
    report_complete_date = DateField('Report Complete Date', format='%Y-%m-%d', validators=[InputRequired()])
    report_complete_btn = SubmitField('Report Completed')
    

class SendReportQCStep(FlaskForm):
    nested_value = FloatField('Nested Value', validators=[InputRequired()])
    nested_volume = IntegerField('Nested Volume', validators=[InputRequired()])
    send_reminder_for_qc = SubmitField('Send Reminder for Report QC')


#============================= Report QC Forms =====================================================
class ReportQCStep(FlaskForm):
    report_qc_date = DateField('Report QC Start Date', format='%Y-%m-%d', validators=[InputRequired()])
    report_qc_btn = SubmitField('Report QC Started')
    
    
class ReportQCCompleteStep(FlaskForm):
    report_qc_complete_date = DateField('Report QC Complete Date', format='%Y-%m-%d', validators=[InputRequired()])
    report_qc_complete_btn = SubmitField('Report QC Completed')
    
     
class ReportApprovalStep(FlaskForm):
    report_for_approval_date = DateField('Sent Date', format='%Y-%m-%d', validators=[Optional()], render_kw={"disabled": "disabled"})
    report_for_approval = SubmitField('Report For Approval')
    approval_date = DateField('Approval Date', format='%Y-%m-%d', validators=[Optional()], render_kw={"disabled": "disabled"})
    approve_report_btn = SubmitField('Approve Report')


#============================= Upload Recommendation Forms =====================================================
class UploadWordReport(FlaskForm):
    word_report = FileField("Upload EDD Analysis Report", validators=[FileAllowed(['docx'], 'Docx only!')])
    upload_word_btn = SubmitField('Upload')


class UploadRecom(FlaskForm):
    add_recom_btn = SubmitField('ADD')
    check_recom_btn = SubmitField('Check')
    no_recom_btn = SubmitField('No Recomendation')
    finish_recom_btn = SubmitField('Finish')
    reopen_recom_btn = SubmitField('Reopen')
    clear_recom_btn = SubmitField('Clear')


class UploadSAR(FlaskForm):
    add_sar_btn = SubmitField('ADD')
    check_sar_btn = SubmitField('Check')
    no_sar_btn = SubmitField('No SAR Referral')
    finish_sar_btn = SubmitField('Finish')
    reopen_sar_btn = SubmitField('Reopen')
    clear_sar_btn = SubmitField('Clear')


class UploadSanc(FlaskForm):
    add_sanc_btn = SubmitField('ADD')
    check_sanc_btn = SubmitField('Check')
    no_sanc_btn = SubmitField('No Sanction Referral')
    finish_sanc_btn = SubmitField('Finish')
    reopen_sanc_btn = SubmitField('Reopen')
    clear_sanc_btn = SubmitField('Clear')
    
    
#============================= Working Recommendation Forms =====================================================
class FilterRecom(FlaskForm):
    recom_status = SelectField(
        'Status', 
        choices=[('ALL', 'ALL'), ('Open', 'Open'), ('Closed', 'Closed')], validators=[Optional()]) #('Removed', 'Removed')
    filter_recom = SubmitField('Search')
    export_recom = SubmitField("Export")
    add_recom = SubmitField("Add New")
    

class RecomendationForm(FlaskForm):
    from_section = StringField('From Section', validators=[Optional()])
    recom_or_esc = SelectField('Recommendation OR Escalation*', choices=[('Recommendation', 'Recommendation'), ('Escalation', 'Escalation')], validators=[InputRequired()])
    responsible_personnel = SelectField('Responsible Personnel*', choices=[('EDD Analyst', 'EDD Analyst'), ('FID', 'FID'), ('LCD SAR', 'LCD SAR')], validators=[InputRequired()])
    action_detail = TextAreaField('Action Details', validators=[Optional(), Length(min=1, max=2000)])
    escalation_type = StringField('Escalation Type', validators=[Optional()])
    escalation_to = StringField('Escalation To', validators=[Optional()])
    closure_detail = TextAreaField('Recommendation Closure Details', validators=[Optional(), Length(min=0, max=2000)])
    escalation_recom_detail = TextAreaField('Escalation Recommendation Details', validators=[Optional(), Length(min=0, max=2000)])
    followup_1_date = DateField('Followup Date 1st', format='%Y-%m-%d', validators=[Optional()])
    followup_2_date = DateField('Followup Date 2nd', format='%Y-%m-%d', validators=[Optional()])
    followup_last_date = DateField('Last Followup Date', format='%Y-%m-%d', validators=[Optional()])
    ack_action_date = DateField('Ack Action Date', format='%Y-%m-%d', validators=[Optional()])
    escalation_date = DateField('Escalation Date', format='%Y-%m-%d', validators=[Optional()])
    
    initiated_date = DateField('Initiated Date', format='%Y-%m-%d', validators=[Optional()], render_kw = {"disabled": "disabled"})
    closure_date = DateField('Closure Date', format='%Y-%m-%d', validators=[Optional()], render_kw = {"disabled": "disabled"})
    recom_status = StringField('Satatus', validators=[Optional()], render_kw = {"disabled": "disabled"})
    
    update_btn = SubmitField('Update')
    close_btn = SubmitField('Close')
    export_btn = SubmitField('Export')
    remove_btn = SubmitField('Remove')


class AddRecomendationForm(FlaskForm):
    from_section = StringField('From Section', validators=[Optional()])
    recom_or_esc = SelectField('Recommendation OR Escalation*', choices=[('Recommendation', 'Recommendation'), ('Escalation', 'Escalation')], validators=[InputRequired()])
    responsible_personnel = SelectField('Responsible Personnel*', choices=[('EDD Analyst', 'EDD Analyst'), ('FID', 'FID'), ('LCD SAR', 'LCD SAR')], validators=[InputRequired()])
    action_detail = TextAreaField('Action Details', validators=[Optional(), Length(min=1, max=2000)])
    escalation_type = StringField('Escalation Type', validators=[Optional()])
    escalation_to = StringField('Escalation To', validators=[Optional()])
    closure_detail = TextAreaField('Recommendation Closure Details', validators=[Optional(), Length(min=0, max=2000)])
    escalation_recom_detail = TextAreaField('Escalation Recommendation Details', validators=[Optional(), Length(min=0, max=2000)])
    followup_1_date = DateField('Followup Date 1st', format='%Y-%m-%d', validators=[Optional()])
    followup_2_date = DateField('Followup Date 2nd', format='%Y-%m-%d', validators=[Optional()])
    followup_last_date = DateField('Last Followup Date', format='%Y-%m-%d', validators=[Optional()])
    ack_action_date = DateField('Ack Action Date', format='%Y-%m-%d', validators=[Optional()])
    escalation_date = DateField('Escalation Date', format='%Y-%m-%d', validators=[Optional()])
    
    add_btn = SubmitField('Add')
    

#============================= Working SAR Referral Forms =====================================================
class FilterSAR(FlaskForm):
    sar_status = SelectField(
        'Status', 
        choices=[('ALL', 'ALL'), ('Open', 'Open'), ('Closed', 'Closed')], validators=[Optional()])
    filter_sar = SubmitField('Search')
    export_sar = SubmitField("Export")
    add_sar = SubmitField("Add New")
    

class SARForm(FlaskForm):
    
    subject_name = TextAreaField('Subject Name*', validators=[InputRequired(), Length(min=1)])
    # subject_acc_no = StringField("Subject Account NO", validators=[InputRequired(),validators.Regexp("^[0-9]+$", message="Account Number must only contain digits")])
    subject_acc_no = TextAreaField("Subject Account NO*", validators=[InputRequired()])
    amount = FloatField('Amount*', validators=[InputRequired()])
    currency = SelectField('Currency*', choices=[('$', '$'), ('￥', '￥')], validators=[InputRequired()])
    activity_start_date = DateField('Activity Start Date', format='%Y-%m-%d', validators=[Optional()])
    activity_end_date = DateField('Activity End Date', format='%Y-%m-%d', validators=[Optional()])
    
    reviewed_by_sar = SelectField('Reviewed by SAR*', choices=[('Yes', 'Yes'), ('No', 'No')], validators=[InputRequired()])
    referral_necessary = SelectField('Referral Necessary*', choices=[('Yes', 'Yes'), ('No', 'No')], validators=[InputRequired()])
    referral_warranted = SelectField('Referral Warranted*', choices=[('Yes', 'Yes'), ('No', 'No')], validators=[InputRequired()])
    ctrl = StringField("CTRL/CMT#", validators=[Optional()])
    
    referral_reason = TextAreaField('Referral Reason*', validators=[InputRequired(), Length(min=1)])
    sar_team_comment = TextAreaField('SAR Team Comment', validators=[Optional()])
    edd_team_comment = TextAreaField('EDD Team Comment', validators=[Optional()])
    
    initiated_date = DateField('Initiated Date', format='%Y-%m-%d', validators=[Optional()], render_kw = {"disabled": "disabled"})
    date_submitted = DateField('Date Submitted', format='%Y-%m-%d', validators=[Optional()])
    date_acknowledged = DateField('Date Acknowledged', format='%Y-%m-%d', validators=[Optional()], render_kw = {"disabled": "disabled"})
    sar_status = StringField('Status', validators=[Optional()], render_kw = {"disabled": "disabled"})
    
    update_btn = SubmitField('Update')
    close_btn = SubmitField('Close')
    export_btn = SubmitField('Export')
    remove_btn = SubmitField('Remove')


class AddSARForm(FlaskForm):
    
    subject_name = TextAreaField('Subject Name*', validators=[InputRequired(), Length(min=1)])
    # subject_acc_no = StringField("Subject Account NO", validators=[InputRequired(),validators.Regexp("^[0-9]+$", message="Account Number must only contain digits")])
    subject_acc_no = TextAreaField("Subject Account NO*", validators=[InputRequired()])
    amount = FloatField('Amount*', validators=[InputRequired()])
    currency = SelectField('Currency*', choices=[('$', '$'), ('￥', '￥')], validators=[InputRequired()])
    activity_start_date = DateField('Activity Start Date', format='%Y-%m-%d', validators=[Optional()])
    activity_end_date = DateField('Activity End Date', format='%Y-%m-%d', validators=[Optional()])
    reviewed_by_sar = SelectField('Reviewed by SAR*', choices=[('Yes', 'Yes'), ('No', 'No')], validators=[InputRequired()])
    referral_necessary = SelectField('Referral Necessary*', choices=[('Yes', 'Yes'), ('No', 'No')], validators=[InputRequired()])
    referral_warranted = SelectField('Referral Warranted*', choices=[('Yes', 'Yes'), ('No', 'No')], validators=[InputRequired()])
    ctrl = StringField("CTRL/CMT#", validators=[Optional()])
    
    referral_reason = TextAreaField('Referral Reason*', validators=[InputRequired(), Length(min=1)])
    sar_team_comment = TextAreaField('SAR Team Comment', validators=[Optional()])
    edd_team_comment = TextAreaField('EDD Team Comment', validators=[Optional()])
    
    add_btn = SubmitField('Add')
    
    
#============================= Working Sanction Referral Forms =====================================================
class FilterSanc(FlaskForm):
    sanc_status = SelectField(
        'Status', 
        choices=[('ALL', 'ALL'), ('Open', 'Open'), ('Closed', 'Closed')], validators=[Optional()])
    filter_sanc = SubmitField('Search')
    export_sanc = SubmitField("Export")
    add_sanc = SubmitField("Add New")
    

class SanctionForm(FlaskForm):
    subject_name = TextAreaField('Subject Name*', validators=[InputRequired()])
    amount = FloatField("Amount*", validators=[InputRequired()])
    currency = SelectField('Currency*', choices=[('$', '$'), ('￥', '￥')], validators=[InputRequired()])
    referral_reason = TextAreaField('Referral Reason', validators=[Optional()])
    additional_comment = TextAreaField('Additional Comment', validators=[Optional()])
    date_submitted = DateField('Date Submitted', format='%Y-%m-%d', validators=[Optional()])
    date_acknowledged = DateField('Date Acknowledged', format='%Y-%m-%d', validators=[Optional()])
    
    update_btn = SubmitField('Update')
    close_btn = SubmitField('Close')
    export_btn = SubmitField('Export')
    remove_btn = SubmitField('Remove')


class AddSanctionForm(FlaskForm):
    subject_name = TextAreaField('Subject Name*', validators=[InputRequired()])
    amount = FloatField("Amount*", validators=[InputRequired()])
    currency = SelectField('Currency*', choices=[('$', '$'), ('￥', '￥')], validators=[InputRequired()])
    referral_reason = TextAreaField('Referral Reason', validators=[Optional()])
    additional_comment = TextAreaField('Additional Comment', validators=[Optional()])
    date_submitted = DateField('Date Submitted', format='%Y-%m-%d', validators=[Optional()])
    add_btn = SubmitField('Add')


class RecomFilter(FlaskForm):
    case_id_lst, due_date_lst, submit_date_lst, customer_name_lst, recom_id_lst = get_filter_items("recom")
    
    case_id_sel = SelectMultipleField('Case ID', choices=list(zip(case_id_lst, case_id_lst)), validators=[Optional()])
    recom_id_sel = SelectMultipleField('Recommendation ID', choices=list(zip(recom_id_lst, recom_id_lst)), validators=[Optional()])
    case_due_date_sel = SelectMultipleField('Case Due Date', choices=list(zip(due_date_lst, due_date_lst)), validators=[Optional()])
    date_submit_sel = SelectMultipleField('Submitted Date', choices=list(zip(submit_date_lst, submit_date_lst)), validators=[Optional()])
    customer_name_sel = SelectMultipleField('Customer Name', choices=list(zip(customer_name_lst, customer_name_lst)), validators=[Optional()])
    filter_btn = SubmitField('Filter')
    export_btn = SubmitField('Export')
    
    
class SARFilter(FlaskForm):
    case_id_lst, due_date_lst, submit_date_lst, customer_name_lst = get_filter_items("sar")
    
    case_id_sel = SelectMultipleField('Case ID', choices=case_id_lst, validators=[Optional()])
    case_due_date_sel = SelectMultipleField('Case Due Date', choices=due_date_lst, validators=[Optional()])
    date_submit_sel = SelectMultipleField('Submitted Date', choices=submit_date_lst, validators=[Optional()])
    customer_name_sel = SelectMultipleField('Customer Name', choices=customer_name_lst, validators=[Optional()])
    filter_btn = SubmitField('Filter')
    export_btn = SubmitField('Export')
    
    
class SancFilter(FlaskForm):
    case_id_lst, due_date_lst, submit_date_lst, customer_name_lst = get_filter_items("sanc")
    
    case_id_sel = SelectMultipleField('Case ID', choices=case_id_lst, validators=[Optional()])
    case_due_date_sel = SelectMultipleField('Case Due Date', choices=due_date_lst, validators=[Optional()])
    date_submit_sel = SelectMultipleField('Submitted Date', choices=submit_date_lst, validators=[Optional()])
    customer_name_sel = SelectMultipleField('Customer Name', choices=customer_name_lst, validators=[Optional()])
    filter_btn = SubmitField('Filter')
    export_btn = SubmitField('Export')
    
    
class CICCasesFilter(FlaskForm):
    case_id_lst, due_date_lst, customer_name_lst = get_filter_items("cic")
    
    case_id_sel = SelectMultipleField('Case ID', choices=case_id_lst, validators=[Optional()])
    case_due_date_sel = SelectMultipleField('Case Due Date', choices=due_date_lst, validators=[Optional()])
    customer_name_sel = SelectMultipleField('CIC Customer Name', choices=customer_name_lst, validators=[Optional()])
    filter_btn = SubmitField('Filter')
    export_btn = SubmitField('Export')


#============================= EDD Tracking =====================================================
class DownloadFile1(FlaskForm):
    download_file1_btn = SubmitField('Download')


class DownloadFile2(FlaskForm):
    download_file2_btn = SubmitField('Download')


class DownloadFile3(FlaskForm):
    download_file3_btn = SubmitField('Download')
    
    
class StepOne(FlaskForm):
    rfi_report = FileField("KYC RFI Report", validators=[FileAllowed(['docx'], 'Docx only!'), InputRequired()])
    rfi_analyst = StringField('RFI Analyst', validators=[Optional()], render_kw={"disabled": "disabled"})
    rfi_init_date = DateField('RFI Initiation Date', format='%Y-%m-%d', validators=[Optional()], render_kw={"disabled": "disabled"})
    send_btn = SubmitField('Send')


class StepTwo(FlaskForm):
    case_received_date = DateField('Case Received Date', format='%Y-%m-%d', validators=[Optional()], render_kw={"disabled": "disabled"})
    fid_client = StringField('FID Client', validators=[Optional()], render_kw={"disabled": "disabled"})
    send_btn = SubmitField('Send')
    
    
class StepThree(FlaskForm):
    crr_draft = FileField("CRR Draft", validators=[FileAllowed(['xlsx'], 'xlsx only!'), InputRequired()])
    kyc_form = FileField("Kyc Form", validators=[FileAllowed(['xlsx'], 'xlsx only!'), InputRequired()])
    
    kyc_analyst_lst = get_analyst_lst(role="KYC_analyst")
    kyc_analyst = SelectField('KYC Analyst*', choices=kyc_analyst_lst, validators=[InputRequired()])
    
    qc_analyst_lst = get_analyst_lst(role="QC_analyst")
    qc_analyst = SelectField('QC Analyst*', choices=qc_analyst_lst, validators=[InputRequired()])
    step3_date = DateField('Pending QC Date', format='%Y-%m-%d', validators=[Optional()], render_kw={"disabled": "disabled"})
    send_btn = SubmitField('Send')


class StepFour(FlaskForm):
    fid_bsa_officer_lst = get_analyst_lst(role="FID_BSA_officer")
    fid_bsa_officer = SelectField('FID BSA Officer*', choices=fid_bsa_officer_lst, validators=[InputRequired()])
    
    crr_draft = FileField("CRR Draft", validators=[FileAllowed(['xlsx'], 'xlsx only!'), InputRequired()])
    submit_date = DateField('Submission Date', format='%Y-%m-%d', validators=[Optional()], render_kw={"disabled": "disabled"})
    send_btn = SubmitField('Send')


class StepFive(FlaskForm):
    approved_crr = FileField("Approved CRR", validators=[FileAllowed(['xlsx'], 'xlsx only!'), InputRequired()])
    approve_date = DateField('Approved Date', format='%Y-%m-%d', validators=[Optional()], render_kw={"disabled": "disabled"})
    approve_btn = SubmitField('Approve')


class StepSix(FlaskForm):
    step6_round = IntegerField('Round', validators=[Optional()], render_kw={"disabled": "disabled"})
    step6_latest_time = StringField('Send Date', validators=[Optional()], render_kw={"disabled": "disabled"})
    fid_client = StringField('FID Client', validators=[Optional()], render_kw={"disabled": "disabled"})
    
    kyc_refresh_review = FileField("KYC Refresh Review*", validators=[FileAllowed(['docx'], 'Docx only!'), InputRequired()])
    step6_comment = TextAreaField('Comment', validators=[Optional()])
    step6_send_btn = SubmitField('Send')
    

class StepSeven(FlaskForm):
    step7_round = IntegerField('Round', validators=[Optional()], render_kw={"disabled": "disabled"})
    step7_latest_time = StringField('Send Date', validators=[Optional()], render_kw={"disabled": "disabled"})
    qc_analyst = StringField('QC Analyst', validators=[Optional()], render_kw={"disabled": "disabled"})
    
    kyc_refresh_review = FileField("KYC Refresh Review*", validators=[FileAllowed(['docx'], 'Docx only!'), InputRequired()])
    step7_comment = TextAreaField('Comment', validators=[Optional()])
    step7_send_btn = SubmitField('Send')   
    

class StepEight(FlaskForm):
    finsih_date = DateField('Finish Date', format='%Y-%m-%d', validators=[Optional()], render_kw={"disabled": "disabled"})
    finish_analyst = StringField('Finish Review Analyst', validators=[Optional()], render_kw={"disabled": "disabled"})
    finish_btn = SubmitField('Finish')   


class StepNine(FlaskForm):
    step9_latest_time = StringField('Request Date', validators=[Optional()], render_kw={"disabled": "disabled"})
    step9_round = IntegerField('Round', validators=[Optional()], render_kw={"disabled": "disabled"})
    qc_analyst = StringField('QC Analyst', validators=[Optional()], render_kw={"disabled": "disabled"})
    
    review_for_approval = FileField("KYC EDD Review", validators=[FileAllowed(['docx'], 'Docx only!'), InputRequired()])
    new_risk_rating = SelectField(
        'New Risk Rating', choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')], validators=[InputRequired()])
    edd_head_approver_lst = get_analyst_lst(role="EDD_head_approver")
    edd_head_approver = SelectField('EDD Head', choices=edd_head_approver_lst, validators=[InputRequired()])
    step9_comment = TextAreaField('Comment', validators=[Optional()])
    send_btn = SubmitField('Send')  


class StepTen(FlaskForm):
    step10_latest_time = StringField('Action Date', validators=[Optional()], render_kw={"disabled": "disabled"})
    step10_round = IntegerField('Round', validators=[Optional()], render_kw={"disabled": "disabled"})
    approver = StringField('EDD Head', validators=[Optional()], render_kw={"disabled": "disabled"})
    
    approved_review = FileField("Approved Review", validators=[FileAllowed(['docx'], 'Docx only!'), Optional()])
    action = SelectField(
        'Action', choices=['Approve', 'Pending', 'Reject'], validators=[InputRequired()])
    step10_comment = TextAreaField('Comment', validators=[Optional()])
    send_btn = SubmitField('Send')  
    
    
