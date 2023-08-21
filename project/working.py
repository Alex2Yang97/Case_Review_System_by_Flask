import sqlite3
import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd

from flask import render_template, url_for, flash, redirect, Blueprint
from flask_login import login_required, current_user
from wtforms.validators import InputRequired, Optional

from .forms import (
    UpdateCaseStepForm, WorkingCaseForm, WorkingRMBCaseForm, WorkingCICCaseForm,
    DataStep, SendDataQCStep, 
    DataQCCompleteStep, SendResearchStep,
    ResearchStep, ResearchCompleteStep, SendResearchQCStep,
    ResearchQCStep, ResearchQCCompleteStep, SendReportStep,
    ReportStep, ReportCompleteStep, SendReportQCStep,
    ReportQCStep, ReportQCCompleteStep, ReportApprovalStep)
from .utils import (connect_db, execute_sql, select_sql, cal_dates, get_case, get_name, 
                    show_step_card, show_percent, get_analyst_lst, strptime_date)
from .models import get_user_info
from .emails import (send_data_email, send_data_qc_email, 
                     send_research_email, send_research_qc_email, 
                     send_report_email, send_approval_email)
from .config import EDD_DB_PATH, USER_ADMIN_PATH, NAME_DICT, SQL_TYPE


working = Blueprint('working', __name__)


@working.route('/<int:case_id>/work_on_case', methods=["GET", "POST"])
@login_required
def work_on_case_page(case_id):
    working_case_form = WorkingCaseForm()
    working_rmb_form = WorkingRMBCaseForm()
    working_cic_form = WorkingCICCaseForm()
    update_case_step_form = UpdateCaseStepForm()
    
    update_case_step_form.data_qc_analyst.choices = get_analyst_lst(role="Data_analyst")
    update_case_step_form.report_analyst.choices = get_analyst_lst(role="Report_analyst")
    update_case_step_form.research_qc_analyst.choices = get_analyst_lst(role="Research_analyst")
    
    # ============== Working on Other case ==============
    if (working_case_form.remove_btn.data and working_case_form.validate()) or (
            working_rmb_form.remove_rmb_btn.data and working_rmb_form.validate()) or (
                working_cic_form.remove_cic_btn.data and working_cic_form.validate()):
        flash("Remove current case!", 'warning')
        remove_sql = f"Update casetracking_local set Case_Status = 'Removed' where Case_ID = {case_id}"
        execute_sql(remove_sql)
        remove_sql = f"Update Recommendation_local set Status = 'Removed' where Case_ID = {case_id}"
        execute_sql(remove_sql)
        remove_sql = f"Update SARref_local set Status = 'Removed' where Case_ID = {case_id}"
        execute_sql(remove_sql)
        remove_sql = f"Update SanctionRef_local set Status = 'Removed' where Case_ID = {case_id}"
        execute_sql(remove_sql)
        remove_sql = f"Update CIC_Cases set CIC_Case_Status = 'Removed' where Case_ID = {case_id}"
        execute_sql(remove_sql)
        return redirect(url_for("working.work_on_case_page", case_id=case_id))
        
    if working_case_form.update_btn.data and working_case_form.validate():
        (refresh_date, planned_start_date, planned_end_date, txn_start_date, txn_end_date) = cal_dates(
            working_case_form.kyc_refresh_date.data, working_case_form.risk_rating.data)
        
        update_sql = '''
            Update casetracking_local set Customer_ID = ?, Customer_Name = ?, Type = ?, Category = ?, 
            Risk_Rating = ?, Case_Type = ?, FID_KYC_Refresh_Date = ?, Transaction_Start_Date = ?, Transaction_End_Date = ?, 
            Scheduled_Start_Date = ?, Scheduled_Due_Date = ?, Comment = ? where case_id = ?'''
        execute_sql(update_sql, (
            working_case_form.customer_id.data, working_case_form.customer_name.data, working_case_form.customer_type.data, 
            working_case_form.category.data, working_case_form.risk_rating.data, working_case_form.case_type.data,
            refresh_date, txn_start_date, txn_end_date, planned_start_date, planned_end_date, 
            working_case_form.comment.data, case_id))
        
        flash("Has updated Case info!", 'success')
        return redirect(url_for("working.work_on_case_page", case_id=case_id))
        
    if working_case_form.work_btn.data and working_case_form.validate():
        sql_select = f"select Case_Status from casetracking_local where case_id = {case_id}"
        case_status = select_sql(sql_select)["Case_Status"]
        
        if (case_status == "Data") or (case_status == "Initialized"):
            return redirect(url_for('working.data_page', case_id=case_id))
        elif case_status == "Data QC":
            return redirect(url_for('working.data_qc_page', case_id=case_id))
        elif case_status == "Research":
            return redirect(url_for('working.research_page', case_id=case_id))
        elif case_status == "Research QC":
            return redirect(url_for('working.research_qc_page', case_id=case_id))
        elif case_status == "Report":
            return redirect(url_for('working.report_page', case_id=case_id))
        elif (case_status == "Report QC") or (case_status == "Pending Approval"):
            return redirect(url_for('working.report_qc_page', case_id=case_id))
        elif case_status == "Recommendation & Referral":
            return redirect(url_for('recom_referral.upload_page', case_id=case_id))
        else:
            return redirect(url_for('working.data_page', case_id=case_id))
   
    # ============== Working on RMB case ==============
    if working_rmb_form.update_rmb_btn.data and working_rmb_form.validate():
        update_sql = '''
            Update casetracking_local set Customer_ID = ?, Customer_Name = ?, Type = ?, Category = ?, Risk_Rating = ?, 
            Transaction_Start_Date = ?, Transaction_End_Date = ?, Scheduled_Start_Date = ?, Scheduled_Due_Date = ?, 
            Comment = ? where case_id = ?'''
        execute_sql(update_sql, (
            working_rmb_form.customer_id.data, working_rmb_form.customer_name.data, working_rmb_form.customer_type.data, 
            working_rmb_form.category.data, working_rmb_form.risk_rating.data, 
            working_rmb_form.txn_start_date.data, working_rmb_form.txn_end_date.data, working_rmb_form.sc_start_date.data, working_rmb_form.sc_end_date.data,
            working_rmb_form.comment.data, case_id))
        
        flash("Has updated RMB Case info!", 'success')
        return redirect(url_for("working.work_on_case_page", case_id=case_id))
        
    if working_rmb_form.work_rmb_btn.data and working_rmb_form.validate():
        sql_select = f"select Case_Status from casetracking_local where case_id = {case_id}"
        case_status = select_sql(sql_select)["Case_Status"]
        
        if (case_status == "Data") or (case_status == "Initialized"):
            return redirect(url_for('working.data_page', case_id=case_id))
        elif case_status == "Data QC":
            return redirect(url_for('working.data_qc_page', case_id=case_id))
        elif case_status == "Research":
            return redirect(url_for('working.research_page', case_id=case_id))
        elif case_status == "Research QC":
            return redirect(url_for('working.research_qc_page', case_id=case_id))
        elif case_status == "Report":
            return redirect(url_for('working.report_page', case_id=case_id))
        elif (case_status == "Report QC") or (case_status == "Pending Approval"):
            return redirect(url_for('working.report_qc_page', case_id=case_id))
        elif case_status == "Recommendation & Referral":
            return redirect(url_for('recom_referral.upload_page', case_id=case_id))
        else:
            return redirect(url_for('working.data_page', case_id=case_id))
    
    # ============== Working on CIC case ==============
    if working_cic_form.add_sub_cic_btn.data and working_cic_form.validate():
        return redirect(url_for("cic_creating.create_cic_page", case_id=case_id))
        
    if working_cic_form.update_cic_btn.data and working_cic_form.validate():
        update_sql = '''
            Update casetracking_local set Customer_Name = ?, Case_Type = ?, Comment = ?,
            Transaction_Start_Date = ?, Transaction_End_Date = ?, Scheduled_Start_Date = ?, Scheduled_Due_Date = ? where case_id = ?'''
        execute_sql(update_sql, (
            working_cic_form.customer_name.data, working_cic_form.case_type.data, working_cic_form.comment.data,
            working_cic_form.txn_start_date.data, working_cic_form.txn_end_date.data, working_cic_form.sc_start_date.data, working_cic_form.sc_end_date.data,
            case_id))
        
        flash("Has updated CIC Case info!", 'success')
        return redirect(url_for("working.work_on_case_page", case_id=case_id))
        
    if working_cic_form.work_cic_btn.data and working_cic_form.validate():
        sql_select = f"select Case_Status from casetracking_local where case_id = {case_id}"
        case_status = select_sql(sql_select)["Case_Status"]
        
        if (case_status == "Data") or (case_status == "Initialized"):
            return redirect(url_for('working.data_page', case_id=case_id))
        elif case_status == "Data QC":
            return redirect(url_for('working.data_qc_page', case_id=case_id))
        elif case_status == "Research":
            return redirect(url_for('working.research_page', case_id=case_id))
        elif case_status == "Research QC":
            return redirect(url_for('working.research_qc_page', case_id=case_id))
        elif case_status == "Report":
            return redirect(url_for('working.report_page', case_id=case_id))
        elif (case_status == "Report QC") or (case_status == "Pending Approval"):
            return redirect(url_for('working.report_qc_page', case_id=case_id))
        elif case_status == "Recommendation & Referral":
            return redirect(url_for('recom_referral.upload_page', case_id=case_id))
        else:
            return redirect(url_for('working.data_page', case_id=case_id))
        
    # ============== Update Case Steps Info ==============
    if update_case_step_form.update_step_btn.data and update_case_step_form.validate_on_submit():

        if get_user_info(current_user.get_id()).data == 1:
            update_sql = '''
                Update casetracking_local set 
                Data_Start_Date = ?, Data_QC_Analyst = ?, Data_QC_Complete_Date = ?, Report_Analyst = ?, 
                Volume = ?, Value = ?, Currency = ?, Number_of_SARs = ?, High_Risk_Country_Vol_Percentage = ?, 
                High_Risk_Country_Val_Percentage = ? where case_id = ?'''
                
            execute_sql(update_sql, (
                update_case_step_form.data_date.data, update_case_step_form.data_qc_analyst.data, update_case_step_form.data_qc_complete_date.data, 
                update_case_step_form.report_analyst.data, update_case_step_form.volume.data, update_case_step_form.value.data, update_case_step_form.currency.data, 
                update_case_step_form.sars_volume.data, update_case_step_form.high_risk_country_vol.data, update_case_step_form.high_risk_country_val.data, 
                case_id))
            
        if get_user_info(current_user.get_id()).research == 1:
            update_sql = '''
                Update casetracking_local set 
                Research_Started_Date = ?, Research_Complete_Date = ?, 
                Research_QC_Analyst = ?, Research_Entities_Volume = ?, Research_QC_Start_Date = ?, Research_QC_Complete_Date = ?
                where case_id = ?'''
            execute_sql(update_sql, (
                update_case_step_form.research_date.data, update_case_step_form.research_complete_date.data, 
                update_case_step_form.research_qc_analyst.data, update_case_step_form.entity_volume.data, 
                update_case_step_form.research_qc_date.data, update_case_step_form.research_qc_complete_date.data, case_id))
            
        if get_user_info(current_user.get_id()).report == 1:
            update_sql = '''
                Update casetracking_local set 
                Report_Start_Date = ?, Report_Complete_Date = ?, Nested_Value = ?, Nested_Volume = ?, Report_QC_Start_Date = ?, Report_QC_Complete_Date = ?
                where case_id = ?'''
            execute_sql(update_sql, (
                update_case_step_form.report_date.data, update_case_step_form.report_complete_date.data, 
                update_case_step_form.nested_value.data, update_case_step_form.nested_volume.data, update_case_step_form.report_qc_date.data, 
                update_case_step_form.report_qc_complete_date.data, case_id))

        flash("Updated Steps Info!", "success")
        return redirect(url_for("working.work_on_case_page", case_id=case_id)) 
    
    
    # ============== Load Page ==============
    
    cursor, cnxn = connect_db()
    sql_get_cic_cases = f'''
        select CIC_Case_ID, CIC_Customer_ID, CIC_Customer_Name, Risk_Rating, Type, KYC_Refresh_Date, CIC_Case_Status,
        Comments from CIC_Cases where Case_ID = {case_id} and CIC_Case_Status <> 'Removed' '''
    cic_cases = pd.read_sql(sql_get_cic_cases, cnxn)
    cursor.close()
    cnxn.close()
    
    sql_select = f'''
        select Customer_ID, Customer_Name, Type, Category, Risk_Rating, Case_Type, FID_KYC_Refresh_Date, 
        Scheduled_Start_Date, Scheduled_Due_Date, Transaction_Start_Date, Transaction_End_Date, Case_Status, 
        Comment from casetracking_local where case_id = {case_id}'''
    case_info = select_sql(sql_select)

    if case_info["Case_Type"] != "RMB Review" and case_info["Category"] != "CIC":
        working_case_form.customer_id.default = case_info["Customer_ID"]
        working_case_form.customer_name.default = case_info["Customer_Name"]
        working_case_form.customer_type.default = case_info["Type"]
        working_case_form.category.default = case_info["Category"]
        working_case_form.risk_rating.default = case_info["Risk_Rating"]
        working_case_form.case_type.default = case_info["Case_Type"]
        working_case_form.kyc_refresh_date.default = strptime_date(case_info["FID_KYC_Refresh_Date"])
        working_case_form.sc_start_date.default = strptime_date(case_info["Scheduled_Start_Date"])
        working_case_form.sc_end_date.default = strptime_date(case_info["Scheduled_Due_Date"])
        working_case_form.txn_start_date.default = strptime_date(case_info["Transaction_Start_Date"])
        working_case_form.txn_end_date.default = strptime_date(case_info["Transaction_End_Date"])
        working_case_form.case_status.default = case_info["Case_Status"]
        working_case_form.comment.default = case_info["Comment"]
        working_case_form.process()
        
        working_rmb_form.update_rmb_btn.render_kw = {"disabled": "disabled"}
        working_rmb_form.work_rmb_btn.render_kw = {"disabled": "disabled"}
        working_rmb_form.remove_rmb_btn.render_kw = {"disabled": "disabled"}
        working_cic_form.update_cic_btn.render_kw = {"disabled": "disabled"}
        working_cic_form.add_sub_cic_btn.render_kw = {"disabled": "disabled"}
        working_cic_form.work_cic_btn.render_kw = {"disabled": "disabled"}
        working_cic_form.remove_cic_btn.render_kw = {"disabled": "disabled"}
        
        if case_info["Case_Status"] == "Removed":
            working_case_form.update_btn.render_kw = {"disabled": "disabled"}
            working_case_form.work_btn.render_kw = {"disabled": "disabled"}
            working_case_form.remove_btn.render_kw = {"disabled": "disabled"}
        
        if get_user_info(current_user.get_id()).edit_auth != 1 or case_info["Case_Status"] == "Removed":
            
            # If validator is InputRequired(), then "disabled" will make form.validate() always False
            for myform_field in working_case_form:
                validators = myform_field.validators
                for i, validator in enumerate(validators):
                    if isinstance(validator, InputRequired):
                        validators[i] = Optional()
                        
            working_case_form.customer_id.render_kw = {"disabled": "disabled"}
            working_case_form.customer_name.render_kw = {"disabled": "disabled"}
            working_case_form.customer_type.render_kw = {"disabled": "disabled"}
            working_case_form.category.render_kw = {"disabled": "disabled"}
            working_case_form.risk_rating.render_kw = {"disabled": "disabled"}
            working_case_form.case_type.render_kw = {"disabled": "disabled"}
            working_case_form.kyc_refresh_date.render_kw = {"disabled": "disabled"}
            working_case_form.comment.render_kw = {"disabled": "disabled"}
            working_case_form.update_btn.render_kw = {"disabled": "disabled"}      
    
    # RMB Review 
    if case_info["Case_Type"] == "RMB Review" : 
        working_rmb_form.customer_id.default = case_info["Customer_ID"]
        working_rmb_form.customer_name.default = case_info["Customer_Name"]
        working_rmb_form.customer_type.default = case_info["Type"]
        working_rmb_form.category.default = case_info["Category"]
        working_rmb_form.risk_rating.default = case_info["Risk_Rating"]
        working_rmb_form.sc_start_date.default = strptime_date(case_info["Scheduled_Start_Date"])
        working_rmb_form.sc_end_date.default = strptime_date(case_info["Scheduled_Due_Date"])
        working_rmb_form.txn_start_date.default = strptime_date(case_info["Transaction_Start_Date"])
        working_rmb_form.txn_end_date.default = strptime_date(case_info["Transaction_End_Date"])
        working_rmb_form.case_status.default = case_info["Case_Status"]
        working_rmb_form.comment.default = case_info["Comment"]
        working_rmb_form.process()
        
        working_case_form.update_btn.render_kw = {"disabled": "disabled"}
        working_case_form.work_btn.render_kw = {"disabled": "disabled"}
        working_case_form.remove_btn.render_kw = {"disabled": "disabled"}
        working_cic_form.update_cic_btn.render_kw = {"disabled": "disabled"}
        working_cic_form.add_sub_cic_btn.render_kw = {"disabled": "disabled"}
        working_cic_form.work_cic_btn.render_kw = {"disabled": "disabled"}
        working_cic_form.remove_cic_btn.render_kw = {"disabled": "disabled"}
        
        if case_info["Case_Status"] == "Removed":
            working_rmb_form.update_rmb_btn.render_kw = {"disabled": "disabled"}
            working_rmb_form.work_rmb_btn.render_kw = {"disabled": "disabled"}
            working_rmb_form.remove_rmb_btn.render_kw = {"disabled": "disabled"}
        
        if get_user_info(current_user.get_id()).edit_auth != 1 or case_info["Case_Status"] == "Removed":
            
            # If validator is InputRequired(), then "disabled" will make form.validate() always False
            for myform_field in working_rmb_form:
                validators = myform_field.validators
                for i, validator in enumerate(validators):
                    if isinstance(validator, InputRequired):
                        validators[i] = Optional()
                        
            working_rmb_form.customer_id.render_kw = {"disabled": "disabled"}
            working_rmb_form.customer_name.render_kw = {"disabled": "disabled"}
            working_rmb_form.customer_type.render_kw = {"disabled": "disabled"}
            working_rmb_form.category.render_kw = {"disabled": "disabled"}
            working_rmb_form.risk_rating.render_kw = {"disabled": "disabled"}
            working_rmb_form.txn_start_date.render_kw = {"disabled": "disabled"}
            working_rmb_form.txn_end_date.render_kw = {"disabled": "disabled"}
            working_rmb_form.sc_start_date.render_kw = {"disabled": "disabled"}
            working_rmb_form.sc_end_date.render_kw = {"disabled": "disabled"}
            working_rmb_form.comment.render_kw = {"disabled": "disabled"}
            working_rmb_form.update_rmb_btn.render_kw = {"disabled": "disabled"}

    if case_info["Category"] == "CIC":
        working_cic_form.customer_name.default = case_info["Customer_Name"]
        working_cic_form.sc_start_date.default = strptime_date(case_info["Scheduled_Start_Date"])
        working_cic_form.sc_end_date.default = strptime_date(case_info["Scheduled_Due_Date"])
        working_cic_form.txn_start_date.default = strptime_date(case_info["Transaction_Start_Date"])
        working_cic_form.txn_end_date.default = strptime_date(case_info["Transaction_End_Date"])
        working_cic_form.case_type.default = case_info["Case_Type"]
        working_cic_form.comment.default = case_info["Comment"]
        working_cic_form.case_status.default = case_info["Case_Status"]
        working_cic_form.process()
        
        working_case_form.update_btn.render_kw = {"disabled": "disabled"}
        working_case_form.work_btn.render_kw = {"disabled": "disabled"}
        working_case_form.remove_btn.render_kw = {"disabled": "disabled"}
        working_rmb_form.update_rmb_btn.render_kw = {"disabled": "disabled"}
        working_rmb_form.work_rmb_btn.render_kw = {"disabled": "disabled"}
        working_rmb_form.remove_rmb_btn.render_kw = {"disabled": "disabled"}
        
        if case_info["Case_Status"] == "Removed":
            working_cic_form.update_cic_btn.render_kw = {"disabled": "disabled"}
            working_cic_form.add_sub_cic_btn.render_kw = {"disabled": "disabled"}
            working_cic_form.work_cic_btn.render_kw = {"disabled": "disabled"}
            working_cic_form.remove_cic_btn.render_kw = {"disabled": "disabled"}
        
        if get_user_info(current_user.get_id()).edit_auth != 1 or case_info["Case_Status"] == "Removed":
            
            # If validator is InputRequired(), then "disabled" will make form.validate() always False
            for myform_field in working_cic_form:
                validators = myform_field.validators
                for i, validator in enumerate(validators):
                    if isinstance(validator, InputRequired):
                        validators[i] = Optional()
                        
            working_cic_form.customer_name.render_kw = {"disabled": "disabled"}
            working_cic_form.case_type.render_kw = {"disabled": "disabled"}
            working_cic_form.txn_start_date.render_kw = {"disabled": "disabled"}
            working_cic_form.txn_end_date.render_kw = {"disabled": "disabled"}
            working_cic_form.sc_start_date.render_kw = {"disabled": "disabled"}
            working_cic_form.sc_end_date.render_kw = {"disabled": "disabled"}
            working_cic_form.comment.render_kw = {"disabled": "disabled"}
            working_cic_form.update_cic_btn.render_kw = {"disabled": "disabled"}

    # Update Steps Information
    sql_get_step_info = f'''
        select Data_Start_Date, Data_QC_Analyst, Data_QC_Complete_Date, Report_Analyst, 
        Volume, Value, Currency, Number_of_SARs, High_Risk_Country_Vol_Percentage, High_Risk_Country_Val_Percentage,
        Research_Started_Date, Research_Complete_Date, 
        Research_QC_Analyst, Research_Entities_Volume, Research_QC_Start_Date, Research_QC_Complete_Date,
        Report_Start_Date, Report_Complete_Date, Nested_Value, Nested_Volume, Report_QC_Start_Date, Report_QC_Complete_Date
        from casetracking_local where case_id = {case_id}'''
    step_info_data = select_sql(sql_get_step_info)
    
    update_case_step_form.data_date.default = strptime_date(step_info_data["Data_Start_Date"])
    update_case_step_form.data_qc_analyst.default = step_info_data["Data_QC_Analyst"]
    update_case_step_form.data_qc_complete_date.default = strptime_date(step_info_data["Data_QC_Complete_Date"])
    update_case_step_form.report_analyst.default = step_info_data["Report_Analyst"]
    update_case_step_form.volume.default = step_info_data["Volume"]
    update_case_step_form.value.default = step_info_data["Value"]
    update_case_step_form.currency.default = step_info_data["Currency"]
    update_case_step_form.sars_volume.default = step_info_data["Number_of_SARs"]
    update_case_step_form.high_risk_country_vol.default = step_info_data["High_Risk_Country_Vol_Percentage"]
    update_case_step_form.high_risk_country_val.default = step_info_data["High_Risk_Country_Val_Percentage"]
    
    update_case_step_form.research_date.default = strptime_date(step_info_data["Research_Started_Date"]) 
    update_case_step_form.research_complete_date.default = strptime_date(step_info_data["Research_Complete_Date"])
    update_case_step_form.research_qc_analyst.default = step_info_data["Research_QC_Analyst"]
    update_case_step_form.entity_volume.default = step_info_data["Research_Entities_Volume"]
    update_case_step_form.research_qc_date.default = strptime_date(step_info_data["Research_QC_Start_Date"]) 
    update_case_step_form.research_qc_complete_date.default = strptime_date(step_info_data["Research_QC_Complete_Date"]) 
    
    update_case_step_form.report_date.default = strptime_date(step_info_data["Report_Start_Date"])
    update_case_step_form.report_complete_date.default = strptime_date(step_info_data["Report_Complete_Date"])
    update_case_step_form.nested_value.default = step_info_data["Nested_Value"]
    update_case_step_form.nested_volume.default = step_info_data["Nested_Volume"]
    update_case_step_form.report_qc_date.default = strptime_date(step_info_data["Report_QC_Start_Date"])
    update_case_step_form.report_qc_complete_date.default = strptime_date(step_info_data["Report_QC_Complete_Date"])
    update_case_step_form.process()
    
    # 最开始我本来想先把所有的 fields.render_kw = {"disabled": True}
    # 然后再根据用户的权限，将对应的 fields.render_kw = {"disabled": False}
    # 但我试过很多种方法后，发现一旦先将fields disabled掉之后，不管用什么办法 enabled
    # 都会导致 form.validate() == False，对应的错误为
    # Error in field "CSRF Token": The CSRF token is missing.
    # 所以我只能选择用 render_kw = {"disabled": "disabled"}
    if get_user_info(current_user.get_id()).data != 1:
        update_case_step_form.data_date.render_kw = {"disabled": "disabled"}
        update_case_step_form.data_qc_analyst.render_kw = {"disabled": "disabled"}
        update_case_step_form.data_qc_complete_date.render_kw = {"disabled": "disabled"}
        update_case_step_form.report_analyst.render_kw = {"disabled": "disabled"}
        update_case_step_form.volume.render_kw = {"disabled": "disabled"}
        update_case_step_form.value.render_kw = {"disabled": "disabled"}
        update_case_step_form.currency.render_kw = {"disabled": "disabled"}
        update_case_step_form.sars_volume.render_kw = {"disabled": "disabled"}
        update_case_step_form.high_risk_country_vol.render_kw = {"disabled": "disabled"}
        update_case_step_form.high_risk_country_val.render_kw = {"disabled": "disabled"}
    if get_user_info(current_user.get_id()).research != 1:
        update_case_step_form.research_date.render_kw = {"disabled": "disabled"}
        update_case_step_form.research_complete_date.render_kw = {"disabled": "disabled"}
        update_case_step_form.research_qc_analyst.render_kw = {"disabled": "disabled"}
        update_case_step_form.entity_volume.render_kw = {"disabled": "disabled"}
        update_case_step_form.research_qc_date.render_kw = {"disabled": "disabled"}
        update_case_step_form.research_qc_complete_date.render_kw = {"disabled": "disabled"}
    if get_user_info(current_user.get_id()).report != 1:
        update_case_step_form.report_date.render_kw = {"disabled": "disabled"}
        update_case_step_form.report_complete_date.render_kw = {"disabled": "disabled"}
        update_case_step_form.nested_value.render_kw = {"disabled": "disabled"}
        update_case_step_form.nested_volume.render_kw = {"disabled": "disabled"}
        update_case_step_form.report_qc_date.render_kw = {"disabled": "disabled"}
        update_case_step_form.report_qc_complete_date.render_kw = {"disabled": "disabled"}
    
    return render_template(
            'working_case.html', case_id=case_id,
            working_case_form=working_case_form, working_rmb_form=working_rmb_form, working_cic_form=working_cic_form, 
            cic_cases=cic_cases, update_case_step_form=update_case_step_form)


#============================= Data Forms =====================================================
@working.route('/<int:case_id>/data', methods=["GET", "POST"])
@login_required
def data_page(case_id):
    user_name = get_user_info(current_user.get_id()).name
    show_name = get_name(user_name=user_name)
    user_email = get_user_info(current_user.get_id()).email
    
    data_form = DataStep()
    send_data_qc_form = SendDataQCStep()
    # 当admin更新用户权限后，这一步可以对form的选项进行刷新
    # 从而让服务器不需要重启的情况下，form的选项也能够根据自动刷新
    send_data_qc_form.data_qc_analyst.choices = get_analyst_lst(role="Data_analyst")
    
    if data_form.data_btn.data and data_form.validate():
        case_status = "Data"
        sub_status = "Data Started"
        sql_update = "update casetracking_local set Data_Analyst = ?, Data_Start_Date = ?, Case_Status = ?, Sub_Status = ? where case_id = ?"
        execute_sql(sql_update, (show_name, data_form.data_date.data, case_status, sub_status, case_id))
        
        return redirect(url_for("working.data_page", case_id=case_id))
    
    if send_data_qc_form.send_reminder_for_qc.data and send_data_qc_form.validate() and send_data_qc_form.data_qc_analyst.data:
        case_status = "Data QC"
        sub_status = "Data Reminder Sent"
        sql_update = "update casetracking_local set Sub_Status = ?, Case_Status = ?, Data_QC_Analyst = ? where case_id = ?"        
        execute_sql(sql_update, [sub_status, case_status, send_data_qc_form.data_qc_analyst.data, case_id])
            
        # Send email
        case_info = select_sql(f"select Customer_ID, Customer_Name, Scheduled_Due_Date from casetracking_local where Case_ID = {case_id}")
        show_name_data_qc_analyst = get_name(show_name=send_data_qc_form.data_qc_analyst.data)
        data_qc_email = select_sql(
            "SELECT Email from User_Info where Name = (?)",
            [show_name_data_qc_analyst],
            db_path=USER_ADMIN_PATH)["Email"]
        message = send_data_email(data_info=case_info, user_name=show_name, user_email=[user_email, data_qc_email])
        flash(message, "success")
        
        return redirect(url_for("working.data_page", case_id=case_id))
    
    if get_user_info(current_user.get_id()).data != 1:
        for filed in data_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in send_data_qc_form:
            filed.render_kw = {"disabled": "disabled"}
    
    # 将form内容进行预填写
    # 并根据case status对相应的fields进行disabled
    sql_select = f"select Case_Status, Sub_Status, Data_Start_Date, Data_QC_Analyst from casetracking_local where case_id = {case_id}"
    case_info_default = select_sql(sql_select)
    
    data_form.data_date.default = strptime_date(case_info_default["Data_Start_Date"])
    data_form.process()
    send_data_qc_form.data_qc_analyst.default = case_info_default["Data_QC_Analyst"]
    send_data_qc_form.process()
    
    if case_info_default["Sub_Status"] == "Initialized":
        percent = 30
        for filed in send_data_qc_form:
            filed.render_kw = {"disabled": "disabled"}
            
    elif case_info_default["Sub_Status"] == "Data Started":
        percent = 60
        for filed in data_form:
            filed.render_kw = {"disabled": "disabled"}
    else:
        percent = show_percent("Data", case_info_default["Case_Status"])
        for filed in data_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in send_data_qc_form:
            filed.render_kw = {"disabled": "disabled"}
    
    # Work Flow Chart
    steps = show_step_card(case_id, case_info_default["Case_Status"])
    
    return render_template(
        'data.html', case_id=case_id, case=get_case(case_id), 
        sub_status=case_info_default["Sub_Status"], 
        data_form=data_form, send_data_qc_form=send_data_qc_form, steps=steps, percent=percent)


#============================= Data QC Forms =====================================================
@working.route('/<int:case_id>/data_qc', methods=["GET", "POST"])
@login_required
def data_qc_page(case_id):
    user_name = get_user_info(current_user.get_id()).name
    show_name = get_name(user_name=user_name)
    user_email = get_user_info(current_user.get_id()).email
    
    data_qc_complete_form = DataQCCompleteStep()
    send_research_form = SendResearchStep()
    send_research_form.report_analyst.choices = get_analyst_lst(role="Report_analyst") 
    
    if data_qc_complete_form.data_qc_complete_btn.data and data_qc_complete_form.validate():        
        sql_select = f'''select Data_Start_Date from casetracking_local where case_id = {case_id}'''
        data_start_date = (
            select_sql(sql_select)["Data_Start_Date"] if SQL_TYPE == "sql server" 
            else strptime_date(select_sql(sql_select)["Data_Start_Date"]).date())
        
        if data_qc_complete_form.data_qc_complete_date.data < data_start_date:
            flash(f"Data QC Complete Date can't be earlier than {data_start_date}", "danger")
        else:
            sub_status = "Data QC Completed"
            sql_update = "update casetracking_local set Data_QC_Complete_Date = ?, Sub_Status = ? where case_id = ?"
            execute_sql(sql_update, (data_qc_complete_form.data_qc_complete_date.data, sub_status, case_id))
            
        return redirect(url_for('working.data_qc_page', case_id=case_id))
    
    if send_research_form.send_case_assignment.data and send_research_form.validate() and send_research_form.report_analyst.data:
        sub_status = "Data Received"
        case_status = "Research"
        sql_update = ("update casetracking_local set Sub_Status = ?, Case_Status = ?, Case_Assigned_Date = ?, "
                       "Report_Analyst = ?, Volume = ?, Value = ?, Currency = ?, Number_of_SARs = ?, "
                       "High_Risk_Country_Vol_Percentage = ?, High_Risk_Country_Val_Percentage = ? where case_id = ?")
        execute_sql(
            sql_update, (sub_status, case_status, datetime.datetime.now().date(), send_research_form.report_analyst.data, 
                         send_research_form.volume.data, send_research_form.value.data, send_research_form.currency.data, 
                         send_research_form.sars_volume.data, send_research_form.high_risk_country_vol.data, 
                         send_research_form.high_risk_country_val.data, case_id))
        # Send email
        case_info = select_sql(
            f'''select Case_Type, Customer_ID, Customer_Name, Risk_Rating, Volume, Value, Transaction_Start_Date, Scheduled_Due_Date, 
            Report_Analyst, Category, Type from casetracking_local where Case_ID = {case_id}''')
        message = send_data_qc_email(case_info, show_name, user_email)
        flash(message, "success")
        
        return redirect(url_for('working.data_qc_page', case_id=case_id))
    
    if get_user_info(current_user.get_id()).data != 1:
        for filed in data_qc_complete_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in send_research_form:
            filed.render_kw = {"disabled": "disabled"}
    
    # 将form内容进行预填写
    # 并根据case status对相应的fields进行disabled
    sql_select = f'''
        select Case_Status, Sub_Status, Data_QC_Complete_Date, Report_Analyst, Volume, Value, Currency, 
        Number_of_SARs, High_Risk_Country_Vol_Percentage, High_Risk_Country_Val_Percentage 
        from casetracking_local where case_id = {case_id}'''
    case_info_default = select_sql(sql_select)
    
    data_qc_complete_form.data_qc_complete_date.default = strptime_date(case_info_default["Data_QC_Complete_Date"])
    data_qc_complete_form.process()
    send_research_form.volume.default = case_info_default["Volume"]
    send_research_form.value.default = case_info_default["Value"]
    send_research_form.currency.default = case_info_default["Currency"]
    send_research_form.sars_volume.default = case_info_default["Number_of_SARs"]
    send_research_form.high_risk_country_vol.default = case_info_default["High_Risk_Country_Vol_Percentage"]
    send_research_form.high_risk_country_val.default = case_info_default["High_Risk_Country_Val_Percentage"]
    send_research_form.report_analyst.default = case_info_default["Report_Analyst"]
    send_research_form.process()
        
    if case_info_default["Sub_Status"] == "Data Reminder Sent":
        percent = 30
        for filed in send_research_form:
            filed.render_kw = {"disabled": "disabled"}
    elif case_info_default["Sub_Status"] == "Data QC Completed":
        percent = 60
        for filed in data_qc_complete_form:
            filed.render_kw = {"disabled": "disabled"}
    else:
        percent = show_percent("Data QC", case_info_default["Case_Status"])
        for filed in data_qc_complete_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in send_research_form:
            filed.render_kw = {"disabled": "disabled"}
            
    # Work Flow Chart
    steps = show_step_card(case_id, case_info_default["Case_Status"])
    
    return render_template(
        'data_qc.html', case_id=case_id, case=get_case(case_id),
        sub_status=case_info_default["Sub_Status"], 
        data_qc_complete_form=data_qc_complete_form, send_research_form=send_research_form,
        steps=steps, percent=percent)


#============================= Research Forms =====================================================
@working.route('/<int:case_id>/research', methods=["GET", "POST"])
@login_required
def research_page(case_id):
    user_name = get_user_info(current_user.get_id()).name
    show_name = get_name(user_name=user_name)
    user_email = get_user_info(current_user.get_id()).email
    
    research_form = ResearchStep()
    research_complete_form = ResearchCompleteStep()
    send_research_qc_form = SendResearchQCStep()
    send_research_qc_form.research_qc_analyst.choices = get_analyst_lst(role="Research_analyst")
    
    if research_form.research_btn.data and research_form.validate():
        sql_select = f'''select Data_QC_Complete_Date from casetracking_local where case_id = {case_id}'''
        data_qc_complete_date = (
            select_sql(sql_select)["Data_QC_Complete_Date"] if SQL_TYPE == "sql server" 
            else strptime_date(select_sql(sql_select)["Data_QC_Complete_Date"]).date())
        
        if research_form.research_date.data < data_qc_complete_date:
            flash(f"Research Start Date can't be earlier than {data_qc_complete_date}", "danger")
        else:
            sub_status = "Research Started"
            sql_update = (
                "update casetracking_local set Research_Analyst = ?, Research_Started_Date = ?, Research_Anticipated_Complete_Date = ?, "
                "Research_QC_Anticipated_Complete_Date = ?, Sub_Status = ? where case_id = ?")
            execute_sql(sql_update, (
                show_name, research_form.research_date.data, research_form.research_date.data + datetime.timedelta(days=2),
                research_form.research_date.data + datetime.timedelta(days=10), sub_status, case_id))
        return redirect(url_for('working.research_page', case_id=case_id))
    
    if research_complete_form.research_complete_btn.data and research_complete_form.validate():
        sql_select = f'''select Research_Started_Date from casetracking_local where case_id = {case_id}'''
        research_started_date = (
            select_sql(sql_select)["Research_Started_Date"] if SQL_TYPE == "sql server" 
            else strptime_date(select_sql(sql_select)["Research_Started_Date"]).date())
        
        if research_complete_form.research_complete_date.data < research_started_date:
            flash(f"Research Complete Date can't be earlier than {research_started_date}", "danger")
        else:
            sub_status = "Research Completed"
            sql_update = "update casetracking_local set Research_Analyst = ?, Research_Complete_Date = ?, Sub_Status = ? where case_id = ?"
            execute_sql(sql_update, (show_name, research_complete_form.research_complete_date.data, sub_status, case_id))
        return redirect(url_for('working.research_page', case_id=case_id))
    
    if send_research_qc_form.send_reminder_for_qc.data and send_research_qc_form.validate():
        case_status = "Research QC"
        sub_status = "Research Reminder Sent"
        sql_update = "update casetracking_local set Research_Entities_Volume = ?, Research_QC_Analyst = ?, Case_Status = ?, Sub_Status = ? where case_id = ?"
        execute_sql(sql_update, (send_research_qc_form.entity_volume.data, send_research_qc_form.research_qc_analyst.data, case_status, sub_status, case_id))
        
        # Send email
        case_info = select_sql(
            f'''select Customer_ID, Customer_Name, Scheduled_Due_Date from casetracking_local where Case_ID = {case_id}''')
        show_name_research_qc_analyst = get_name(show_name=send_research_qc_form.research_qc_analyst.data)
        research_qc_email = select_sql(
            "SELECT Email from User_Info where Name = (?)",
            [show_name_research_qc_analyst],
            db_path=USER_ADMIN_PATH)["Email"]
        message = send_research_email(data_info=case_info, user_name=show_name, user_email=[user_email, research_qc_email])
        
        flash(message, "success")
        return redirect(url_for('working.research_page', case_id=case_id))
    
    if get_user_info(current_user.get_id()).research != 1:
        for filed in research_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in research_complete_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in send_research_qc_form:
            filed.render_kw = {"disabled": "disabled"}
    
    sql_select = f'''
        select Case_Status, Sub_Status, Research_Started_Date, Research_Complete_Date, Research_Entities_Volume, 
        Research_QC_Analyst from casetracking_local where case_id = {case_id}'''
    case_info_default = select_sql(sql_select)
    
    research_form.research_date.default = strptime_date(case_info_default["Research_Started_Date"])
    research_form.process()
    research_complete_form.research_complete_date.default = strptime_date(case_info_default["Research_Complete_Date"])
    research_complete_form.process()
    send_research_qc_form.entity_volume.default = case_info_default["Research_Entities_Volume"]
    send_research_qc_form.research_qc_analyst.default = case_info_default["Research_QC_Analyst"]
    send_research_qc_form.process()
        
    if case_info_default["Sub_Status"] == "Data Received":
        percent = 25
        for filed in research_complete_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in send_research_qc_form:
            filed.render_kw = {"disabled": "disabled"}
        
    elif case_info_default["Sub_Status"] == "Research Started":
        percent = 50
        for filed in research_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in send_research_qc_form:
            filed.render_kw = {"disabled": "disabled"}
        
    elif case_info_default["Sub_Status"] == "Research Completed":
        percent = 75
        for filed in research_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in research_complete_form:
            filed.render_kw = {"disabled": "disabled"}
            
    else:
        percent = show_percent("Research", case_info_default["Case_Status"])
        for filed in research_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in research_complete_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in send_research_qc_form:
            filed.render_kw = {"disabled": "disabled"}
    
    # Work Flow Chart
    steps = show_step_card(case_id, case_info_default["Case_Status"])
    
    return render_template(
        'research.html', case_id=case_id, case=get_case(case_id), 
        sub_status=case_info_default["Sub_Status"], 
        research_form=research_form, research_complete_form=research_complete_form, send_research_qc_form=send_research_qc_form, 
        steps=steps, percent=percent
        )


#============================= Research QC Forms =====================================================
@working.route('/<int:case_id>/research_qc', methods=["GET", "POST"])
@login_required
def research_qc_page(case_id):
    user_name = get_user_info(current_user.get_id()).name
    show_name = get_name(user_name=user_name)
    user_email = get_user_info(current_user.get_id()).email
    
    research_qc_form = ResearchQCStep()
    research_qc_complete_form = ResearchQCCompleteStep()
    send_report_form = SendReportStep()
        
    if research_qc_form.research_qc_btn.data and research_qc_form.validate():
        sql_select = f'''select Research_Complete_Date from casetracking_local where case_id = {case_id}'''
        research_complete_date = (
            select_sql(sql_select)["Research_Complete_Date"] if SQL_TYPE == "sql server" 
            else strptime_date(select_sql(sql_select)["Research_Complete_Date"]).date())
        
        if research_qc_form.research_qc_date.data < research_complete_date:
            flash(f"Research QC Start Date can't be earlier than {research_complete_date}", "danger")
        else:
            sub_status = "Research QC Started"
            sql_update = "update casetracking_local set Research_QC_Start_Date = ?, Sub_Status = ? where case_id = ?"
            execute_sql(sql_update, (research_qc_form.research_qc_date.data, sub_status, case_id))
        return redirect(url_for('working.research_qc_page', case_id=case_id))
    
    if research_qc_complete_form.research_qc_complete_btn.data and research_qc_complete_form.validate():
        sql_select = f'''select Research_QC_Start_Date from casetracking_local where case_id = {case_id}'''
        research_qc_start_date = (
            select_sql(sql_select)["Research_QC_Start_Date"] if SQL_TYPE == "sql server" 
            else strptime_date(select_sql(sql_select)["Research_QC_Start_Date"]).date())
        
        if research_qc_complete_form.research_qc_complete_date.data < research_qc_start_date:
            flash(f"Reearch QC Complete Date can't be earlier than {research_qc_start_date}", "danger")
        else:
            sub_status = "Research QC Completed"
            sql_update = "update casetracking_local set Research_QC_Complete_Date = ?, Sub_Status = ? where case_id = ?"
            execute_sql(sql_update, (research_qc_complete_form.research_qc_complete_date.data, sub_status, case_id))
        return redirect(url_for('working.research_qc_page', case_id=case_id))
    
    if send_report_form.remind_report_team.data and send_report_form.validate():
        sub_status = "Research Received"
        case_status = "Report"
        sql_update = "update casetracking_local set Sub_Status = ?, Case_Status = ? where case_id = ?"
        execute_sql(sql_update, (sub_status, case_status, case_id))

        # Send email
        case_info = select_sql(
            f'''select Customer_ID, Customer_Name, Scheduled_Due_Date from casetracking_local where Case_ID = {case_id}''')
        message = send_research_qc_email(case_info, show_name, user_email)
        flash(message, "success")
        return redirect(url_for('working.research_qc_page', case_id=case_id))
    
    if get_user_info(current_user.get_id()).research != 1:
        for filed in research_qc_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in research_qc_complete_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in send_report_form:
            filed.render_kw = {"disabled": "disabled"}      
    
    sql_select = f'''
        select Case_Status, Sub_Status, Research_QC_Start_Date, Research_QC_Complete_Date 
        from casetracking_local where case_id = {case_id}'''
    case_info_default = select_sql(sql_select)
    
    research_qc_form.research_qc_date.default = strptime_date(case_info_default["Research_QC_Start_Date"])
    research_qc_form.process()    
    research_qc_complete_form.research_qc_complete_date.default = strptime_date(case_info_default["Research_QC_Complete_Date"])
    research_qc_complete_form.process()
    
    if case_info_default["Sub_Status"] == "Research Reminder Sent":
        percent = 25
        for filed in research_qc_complete_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in send_report_form:
            filed.render_kw = {"disabled": "disabled"}
            
    elif case_info_default["Sub_Status"] == "Research QC Started":
        percent = 50
        
        for filed in research_qc_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in send_report_form:
            filed.render_kw = {"disabled": "disabled"}
    elif case_info_default["Sub_Status"] == "Research QC Completed":
        percent = 75
        
        for filed in research_qc_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in research_qc_complete_form:
            filed.render_kw = {"disabled": "disabled"}
    else:
        percent = show_percent("Research QC", case_info_default["Case_Status"])
        
        for filed in research_qc_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in research_qc_complete_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in send_report_form:
            filed.render_kw = {"disabled": "disabled"}
    
    # Work Flow Chart
    steps = show_step_card(case_id, case_info_default["Case_Status"])
    
    return render_template(
        'research_qc.html', case_id=case_id, case=get_case(case_id), 
        sub_status=case_info_default["Sub_Status"], 
        research_qc_form=research_qc_form, research_qc_complete_form=research_qc_complete_form, send_report_form=send_report_form,
        steps=steps, percent=percent)


#============================= Report Forms =====================================================
@working.route('/<int:case_id>/report', methods=["GET", "POST"])
@login_required
def report_page(case_id):
    user_name = get_user_info(current_user.get_id()).name
    show_name = get_name(user_name=user_name)
    user_email = get_user_info(current_user.get_id()).email
    
    report_form = ReportStep()
    report_complete_form = ReportCompleteStep()
    send_report_form = SendReportQCStep()
    
    if report_form.report_btn.data and report_form.validate():
        # Report Start Date can be earlier than the Research Complete Date and Research QC Complete Date 
        sub_status = "Report Started"
        sql_update = "update casetracking_local set Report_Start_Date = ?, Sub_Status = ? where case_id = ?"
        execute_sql(sql_update, (report_form.report_date.data, sub_status, case_id))
        return redirect(url_for('working.report_page', case_id=case_id))
    
    if report_complete_form.report_complete_btn.data and report_complete_form.validate():
        # Report Complete Date cannot be earlier than the Research Complete Date, Research QC Complete Date, Report Start Date        
        sql_select = f'''select Research_QC_Complete_Date, Report_Start_Date from casetracking_local where case_id = {case_id}'''
        (research_qc_complete_date, report_start_date) = select_sql(sql_select).values()
        
        if SQL_TYPE == "sqlite":
            research_qc_complete_date = strptime_date(research_qc_complete_date).date()
            report_start_date = strptime_date(report_start_date).date()
        
        if report_complete_form.report_complete_date.data < research_qc_complete_date:
            flash(f"Report Complete Date can't be earlier than Research QC Complete {research_qc_complete_date}", "danger")
        elif report_complete_form.report_complete_date.data < report_start_date:
            flash(f"Report Complete Date can't be earlier than Report Start {report_start_date}", "danger")
        else:
            sub_status = "Report Completed"
            sql_update = "update casetracking_local set Report_Complete_Date = ?, Sub_Status = ? where case_id = ?"
            execute_sql(sql_update, (report_complete_form.report_complete_date.data, sub_status, case_id))
        return redirect(url_for('working.report_page', case_id=case_id))
       
    if send_report_form.send_reminder_for_qc.data and send_report_form.validate():
        case_status = "Report QC"
        sub_status = "Report Reminder Sent"
        sql_update = "update casetracking_local set Nested_Volume = ?, Nested_Value = ?, Case_Status = ?, Sub_Status = ? where case_id = ?"
        execute_sql(sql_update, (send_report_form.nested_volume.data, send_report_form.nested_value.data, case_status, sub_status, case_id))
        
        # Send email
        case_info = select_sql(f'''select Customer_ID, Customer_Name, Scheduled_Due_Date from casetracking_local where Case_ID = {case_id}''')
        message = send_report_email(case_info, show_name, user_email)
        flash(message, "success")
        
        return redirect(url_for('working.report_page', case_id=case_id))
    
    if get_user_info(current_user.get_id()).report != 1:
        for filed in report_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in report_complete_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in send_report_form:
            filed.render_kw = {"disabled": "disabled"}  
    
    sql_select = f'''
        select Case_Status, Sub_Status, Report_Start_Date, Report_Complete_Date, Nested_Value, Nested_Volume 
        from casetracking_local where case_id = {case_id}'''
    case_info_default = select_sql(sql_select)
    
    report_form.report_date.default = strptime_date(case_info_default["Report_Start_Date"])
    report_form.process()
    report_complete_form.report_complete_date.default = strptime_date(case_info_default["Report_Complete_Date"])
    report_complete_form.process()
    send_report_form.nested_value.default = case_info_default["Nested_Value"]
    send_report_form.nested_volume.default = case_info_default["Nested_Volume"]
    send_report_form.process()
        
    if case_info_default["Sub_Status"] == "Research Received":
        percent = 10
        for filed in report_complete_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in send_report_form:
            filed.render_kw = {"disabled": "disabled"}
    elif case_info_default["Sub_Status"] == "Report Started":
        percent = 30
        for filed in report_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in send_report_form:
            filed.render_kw = {"disabled": "disabled"}
    elif case_info_default["Sub_Status"] == "Report Completed":
        percent = 90
        for filed in report_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in report_complete_form:
            filed.render_kw = {"disabled": "disabled"}
    else:
        percent = show_percent("Report", case_info_default["Case_Status"])
        for filed in report_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in report_complete_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in send_report_form:
            filed.render_kw = {"disabled": "disabled"}
            
    # Work Flow Chart
    steps = show_step_card(case_id, case_info_default["Case_Status"])
    
    return render_template(
        'report.html', case_id=case_id, case=get_case(case_id), 
        sub_status=case_info_default["Sub_Status"], 
        report_form=report_form, report_complete_form=report_complete_form, send_report_form=send_report_form,
        steps=steps, percent=percent
        )

#============================= Close Trigger Case =====================================================
# Case_Type为Trigger Event的Case不需要Rec/Ref
def close_trigger_case(case_id):
    sql_select = f'''select Case_Type from casetracking_local where case_id = {case_id}'''
    case_type = select_sql(sql_select)["Case_Type"]
    
    if case_type == "Trigger Event":
        sql_update = f'''
        update CaseTracking_local SET Case_Status = 'Closed', Escal_Recom_Status = 'Closed', SAR_Referral_Status = 'Closed', 
        Sanction_Referral_Status = 'Closed', Has_Recommendation = 'No', Has_SAR_Referral = 'No', Has_Sanction_Referral = 'No' where Case_ID = {case_id}'''
        execute_sql(sql_update)
        flash("All steps has been completed!", "success")
    return

#============================= Report QC Forms =====================================================
@working.route('/<int:case_id>/report_qc', methods=["GET", "POST"])
@login_required
def report_qc_page(case_id):
    user_name = get_user_info(current_user.get_id()).name
    show_name = get_name(user_name=user_name)
    user_email = get_user_info(current_user.get_id()).email
    
    report_qc_form = ReportQCStep()
    report_qc_complete_form = ReportQCCompleteStep()
    report_approve_form = ReportApprovalStep()
    
    if report_qc_form.report_qc_btn.data and report_qc_form.validate():
        sql_select = f"select Report_Complete_Date from casetracking_local where case_id = {case_id}"
        report_complete_date = (
            select_sql(sql_select)["Report_Complete_Date"] if SQL_TYPE == "sql server" 
            else strptime_date(select_sql(sql_select)["Report_Complete_Date"]).date())
        
        if report_qc_form.report_qc_date.data < report_complete_date:
            flash(f"Data QC Start Date can't be earlier than {report_complete_date}", "danger")
        else:
            sub_status = "Report QC Started"
            sql_update = "update casetracking_local set Report_QC_Analyst = ?, Report_QC_Start_Date = ?, Sub_Status = ? where case_id = ?"
            execute_sql(sql_update, (show_name, report_qc_form.report_qc_date.data, sub_status, case_id))
        return redirect(url_for('working.report_qc_page', case_id=case_id))
    
    if report_qc_complete_form.report_qc_complete_btn.data and report_qc_complete_form.validate():        
        sql_select = f"select Report_QC_Start_Date from casetracking_local where case_id = {case_id}"
        report_qc_start_date = (
            select_sql(sql_select)["Report_QC_Start_Date"] if SQL_TYPE == "sql server" 
            else strptime_date(select_sql(sql_select)["Report_QC_Start_Date"]).date())
        
        if report_qc_complete_form.report_qc_complete_date.data < report_qc_start_date:
            flash(f"Data QC Start Date can't be earlier than {report_qc_start_date}", "danger")
        else:
            sub_status = "Report QC Completed"
            sql_update = "update casetracking_local set Report_QC_Complete_Date = ?, Sub_Status = ? where case_id = ?"
            execute_sql(sql_update, (report_qc_complete_form.report_qc_complete_date.data, sub_status, case_id))
        return redirect(url_for('working.report_qc_page', case_id=case_id))
    
    if report_approve_form.report_for_approval.data and report_approve_form.validate():
        sub_status = "Report Pending Approval"
        sql_update = "update casetracking_local set Sub_Status = ?, Report_for_Approval_Date = ? where case_id = ?"
        execute_sql(sql_update, (sub_status, datetime.datetime.now().date(), case_id))
        
        # Send email
        case_info = select_sql(f'''select Customer_ID, Customer_Name, Scheduled_Due_Date from casetracking_local where Case_ID = {case_id}''')
        message = send_approval_email(case_info, show_name, user_email)
        flash(message, "success")
        
        return redirect(url_for('working.report_qc_page', case_id=case_id))
        
    if report_approve_form.approve_report_btn.data and report_approve_form.validate():
        sub_status = "Approved"
        case_status = "Recommendation & Referral"
        sql_update = "update casetracking_local set Report_Approved_Date = ?, Sub_Status = ?, Case_Status = ? where case_id = ?"
        execute_sql(sql_update, (datetime.datetime.now().date(), sub_status, case_status, case_id))
        close_trigger_case(case_id)
        return redirect(url_for("working.report_qc_page", case_id=case_id))
    
    if get_user_info(current_user.get_id()).report != 1:
        for filed in report_qc_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in report_qc_complete_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in report_approve_form:
            filed.render_kw = {"disabled": "disabled"}    
    
    sql_select = f'''
        select Case_Status, Sub_Status, Report_QC_Start_Date, Report_QC_Complete_Date, Report_for_Approval_Date, Report_Approved_Date
        from casetracking_local where case_id = {case_id}'''
    case_info_default = select_sql(sql_select)
    
    report_qc_form.report_qc_date.default = strptime_date(case_info_default["Report_QC_Start_Date"])
    report_qc_form.process()
    report_qc_complete_form.report_qc_complete_date.default = strptime_date(case_info_default["Report_QC_Complete_Date"])
    report_qc_complete_form.process()
    report_approve_form.report_for_approval_date.default = strptime_date(case_info_default["Report_for_Approval_Date"])
    report_approve_form.approval_date.default = strptime_date(case_info_default["Report_Approved_Date"])
    report_approve_form.process()
    
    if case_info_default["Sub_Status"] == "Report Reminder Sent":
        percent = 10
        for filed in report_qc_complete_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in report_approve_form:
            filed.render_kw = {"disabled": "disabled"}
    elif case_info_default["Sub_Status"] == "Report QC Started":
        percent = 30
        for filed in report_qc_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in report_approve_form:
            filed.render_kw = {"disabled": "disabled"}
            
    elif case_info_default["Sub_Status"] == "Report QC Completed":
        percent = 60
        for filed in report_qc_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in report_qc_complete_form:
            filed.render_kw = {"disabled": "disabled"}
            
    elif case_info_default["Sub_Status"] == "Report Pending Approval":
        percent = 90
        for filed in report_qc_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in report_qc_complete_form:
            filed.render_kw = {"disabled": "disabled"}
        report_approve_form.report_for_approval.render_kw = {"disabled": "disabled"}
        
    else:
        percent = show_percent("Report QC", case_info_default["Case_Status"])
        for filed in report_qc_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in report_qc_complete_form:
            filed.render_kw = {"disabled": "disabled"}
        for filed in report_approve_form:
            filed.render_kw = {"disabled": "disabled"}
            
    # Work Flow Chart
    steps = show_step_card(case_id, case_info_default["Case_Status"])
    
    return render_template(
        'report_qc.html', case_id=case_id, case=get_case(case_id), 
        sub_status=case_info_default["Sub_Status"], 
        report_qc_form=report_qc_form, report_qc_complete_form=report_qc_complete_form, 
        report_approve_form=report_approve_form,
        steps=steps, percent=percent)




