import datetime
import pandas as pd

from flask import render_template, flash, Blueprint, redirect,url_for
from flask_login import login_required

from .forms import FindSimilarCase, AddCICForm # UpdateCICForm
from .utils import connect_db, execute_sql, cal_dates, select_sql, strptime_date
from .config import SQL_TYPE


cic_creating = Blueprint('cic_creating', __name__)


@cic_creating.route('/<int:case_id>/create_cic_case', methods=['GET', 'POST'])
@login_required
def create_cic_page(case_id):
    find_similar_case_form = FindSimilarCase()
    add_cic_form = AddCICForm()
    
    # ================== Load sub CIC cases ==================
    cursor, cnxn = connect_db()
    sql_get_cic_cases = f'''
        select CIC_Case_ID, CIC_Customer_ID, CIC_Customer_Name, Risk_Rating, Type, KYC_Refresh_Date, CIC_Case_Status,
        Comments from CIC_Cases where Case_ID = {case_id} and CIC_Case_Status <> 'Removed' '''
    cic_cases = pd.read_sql(sql_get_cic_cases, cnxn)
    cursor.close()
    cnxn.close()
    
    if find_similar_case_form.find_btn.data and find_similar_case_form.validate() and find_similar_case_form.customer_id.data:
        if SQL_TYPE == "sql server":
            sql_find_similar_case = f'''
                select top 1 CIC_Customer_ID, CIC_Customer_Name, Risk_Rating, Type, KYC_Refresh_Date, Comments from CIC_Cases 
                where CIC_Customer_ID = '{find_similar_case_form.customer_id.data.strip()}' order by CIC_Case_ID desc'''
        else:
            sql_find_similar_case = f'''
                select CIC_Customer_ID, CIC_Customer_Name, Risk_Rating, Type, KYC_Refresh_Date, Comments from CIC_Cases 
                where CIC_Customer_ID = '{find_similar_case_form.customer_id.data.strip()}' order by CIC_Case_ID desc limit 1'''
        similar_case = select_sql(sql_find_similar_case)
    
        if not similar_case:
            flash("Don't find similar case in Database! Please fill out fields manually.", "danger")
            return redirect(url_for("cic_creating.create_cic_page"))
        else:
            flash("Find similar case in Database! Prefill out fields.", "success")
            
            if SQL_TYPE == "sql server":
                add_cic_form.case_id.default = case_id
                add_cic_form.cic_customer_id.default = similar_case.CIC_Customer_ID
                add_cic_form.cic_customer_name.default = similar_case.CIC_Customer_Name
                add_cic_form.risk_rating.default = similar_case.Risk_Rating
                add_cic_form.kyc_refresh_date.default = similar_case.KYC_Refresh_Date
                add_cic_form.customer_type.default = similar_case.Type
                add_cic_form.comment.default = similar_case.Comments
            else:
                add_cic_form.case_id.default = case_id
                add_cic_form.cic_customer_id.default = similar_case["CIC_Customer_ID"]
                add_cic_form.cic_customer_name.default = similar_case["CIC_Customer_Name"]
                add_cic_form.risk_rating.default = similar_case["Risk_Rating"]
                add_cic_form.kyc_refresh_date.default = strptime_date(similar_case["KYC_Refresh_Date"])
                add_cic_form.customer_type.default = similar_case["Type"]
                add_cic_form.comment.default = similar_case["Comments"]
            add_cic_form.process()
            
            return render_template(
                'cic_create.html', case_id=case_id, cic_cases=cic_cases, find_similar_case_form=find_similar_case_form, add_cic_form=add_cic_form)
    
    if add_cic_form.create_cic_case.data and add_cic_form.validate():
        insert_cic_case = '''
        INSERT INTO CIC_Cases (
            Case_ID, CIC_Customer_ID, CIC_Customer_Name, Risk_Rating, Type, KYC_Refresh_Date, Comments, CIC_Case_Status) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?) '''
        insert_value_lst = (
            case_id, add_cic_form.cic_customer_id.data.strip(), add_cic_form.cic_customer_name.data.strip(), add_cic_form.risk_rating.data, 
            add_cic_form.customer_type.data, add_cic_form.kyc_refresh_date.data, add_cic_form.comment.data.strip(), "Open")
        execute_sql(insert_cic_case, insert_value_lst)
        
        flash("Create sub CIC case successfully!", 'success')
        return redirect(url_for("cic_creating.create_cic_page", case_id=case_id))
    
    add_cic_form.case_id.default = case_id
    add_cic_form.process()
    
    return render_template(
        'cic_create.html', case_id=case_id, cic_cases=cic_cases, find_similar_case_form=find_similar_case_form, add_cic_form=add_cic_form)
    
    
@cic_creating.route('/<int:case_id>/update_cic_case/<int:cic_case_id>', methods=['GET', 'POST'])
@login_required
def update_cic_page(case_id, cic_case_id):
    update_cic_case_form = AddCICForm()
            
    if update_cic_case_form.create_cic_case.data and update_cic_case_form.validate():
        update_sql = '''
            Update CIC_Cases set CIC_Customer_ID = ?, CIC_Customer_Name = ?, Risk_Rating = ?, 
            Type = ?, KYC_Refresh_Date = ?, Comments = ? where CIC_Case_ID = ?  and CIC_Case_Status <> 'Removed' '''
        execute_sql(update_sql, (
            update_cic_case_form.cic_customer_id.data, update_cic_case_form.cic_customer_name.data, update_cic_case_form.risk_rating.data,
            update_cic_case_form.customer_type.data, update_cic_case_form.kyc_refresh_date.data, update_cic_case_form.comment.data, cic_case_id
        ))
        
        flash("Update sub CIC case successfully!", 'success')
        return redirect(url_for("cic_creating.update_cic_page", case_id=case_id, cic_case_id=cic_case_id)) 
    
    if update_cic_case_form.remove_cic_case.data and update_cic_case_form.validate():
        remove_sql = f"Update CIC_Cases set CIC_Case_Status = 'Removed' where CIC_Case_ID = {cic_case_id}"
        execute_sql(remove_sql)
        
        flash("Remove sub CIC case successfully!", 'warning')
        return redirect(url_for("cic_creating.create_cic_page", case_id=case_id))
    
    # cursor, cnxn = connect_db()
    # sql_cic_case = f'''
    #     select CIC_Customer_ID, CIC_Customer_Name, Risk_Rating, Type, KYC_Refresh_Date, Comments from CIC_Cases 
    #     where CIC_Case_ID = {cic_case_id}'''
    # current_cic_case = cursor.execute(sql_cic_case).fetchone()
    # cursor.close()
    # cnxn.close()
    
    current_cic_case = select_sql(f'''
        select CIC_Customer_ID, CIC_Customer_Name, Risk_Rating, Type, KYC_Refresh_Date, Comments 
        from CIC_Cases where CIC_Case_ID = {cic_case_id}''')
    
    update_cic_case_form.create_cic_case.label.text = "Update sub CIC Case"
    update_cic_case_form.cic_case_id.default = cic_case_id
    update_cic_case_form.case_id.default = case_id
    if SQL_TYPE == "sql server":
        update_cic_case_form.cic_customer_id.default = current_cic_case.CIC_Customer_ID
        update_cic_case_form.cic_customer_name.default = current_cic_case.CIC_Customer_Name
        update_cic_case_form.risk_rating.default = current_cic_case.Risk_Rating
        update_cic_case_form.customer_type.default = current_cic_case.Type
        update_cic_case_form.kyc_refresh_date.default = current_cic_case.KYC_Refresh_Date
        update_cic_case_form.comment.default = current_cic_case.Comments
    else:
        update_cic_case_form.cic_customer_id.default = current_cic_case["CIC_Customer_ID"]
        update_cic_case_form.cic_customer_name.default = current_cic_case["CIC_Customer_Name"]
        update_cic_case_form.risk_rating.default = current_cic_case["Risk_Rating"]
        update_cic_case_form.customer_type.default = current_cic_case["Type"]
        update_cic_case_form.kyc_refresh_date.default = strptime_date(current_cic_case["KYC_Refresh_Date"])
        update_cic_case_form.comment.default = current_cic_case["Comments"]
    update_cic_case_form.process()
    
    # ================== Load sub CIC cases ==================
    cursor, cnxn = connect_db()
    sql_get_cic_cases = f'''
        select CIC_Case_ID, CIC_Customer_ID, CIC_Customer_Name, Risk_Rating, Type, KYC_Refresh_Date, CIC_Case_Status,
        Comments from CIC_Cases where Case_ID = {case_id}'''
    cic_cases = pd.read_sql(sql_get_cic_cases, cnxn)
    cursor.close()
    cnxn.close()
    
    return render_template(
        'cic_update.html', case_id=case_id, cic_case_id=cic_case_id, cic_cases=cic_cases, update_cic_case_form=update_cic_case_form)
