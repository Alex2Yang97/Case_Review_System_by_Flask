import datetime

from flask import render_template, flash, Blueprint, redirect,url_for
from flask_login import login_required

from .forms import NewCaseForm, NewRMBCaseForm, NewCICCaseForm, FindSimilarCase
from .utils import connect_db, execute_sql, select_sql, cal_dates, strptime_date
from .config import SQL_TYPE


create = Blueprint('create', __name__)


@create.route('/create_case', methods=['GET', 'POST'])
@login_required
def create_case_page():
    find_similar_case_form = FindSimilarCase()
    new_case_form = NewCaseForm()
    new_rmb_form = NewRMBCaseForm()
    new_cic_form = NewCICCaseForm()
    
    # create_date = datetime.datetime.now().strftime("%m/%d/%Y")
    create_date = datetime.datetime.now().date()
    default_comment = f"This Case was created on {create_date}."
    
    if find_similar_case_form.find_btn.data and find_similar_case_form.validate() and find_similar_case_form.customer_id.data:
        if SQL_TYPE == "sql server":
            sql_find_similar_case = f'''
                select top 1 Customer_ID, Customer_Name, Risk_Rating, FID_KYC_Refresh_Date, Type, 
                Scheduled_Start_Date, Scheduled_Due_Date, Transaction_Start_Date, Transaction_End_Date,            
                Category, Case_Type, Comment from CaseTracking_local 
                where Customer_ID = '{find_similar_case_form.customer_id.data.strip()}' order by Case_ID desc'''
        else:
            sql_find_similar_case = f'''
                select Customer_ID, Customer_Name, Risk_Rating, FID_KYC_Refresh_Date, Type, 
                Scheduled_Start_Date, Scheduled_Due_Date, Transaction_Start_Date, Transaction_End_Date,            
                Category, Case_Type, Comment from CaseTracking_local 
                where Customer_ID = '{find_similar_case_form.customer_id.data.strip()}' order by Case_ID desc limit 1'''
        similar_case = select_sql(sql_find_similar_case)
        
        if not similar_case:
            flash("Don't find similar case in Database! Please fill out fields manually.", "danger")
            return redirect(url_for("create.create_case_page"))
        else:
            flash("Find similar case in Database! Prefill out fields.", "success")
            
            new_case_form.customer_id.default = similar_case["Customer_ID"]
            new_case_form.customer_name.default = similar_case["Customer_Name"]
            new_case_form.risk_rating.default = similar_case["Risk_Rating"]
            new_case_form.kyc_refresh_date.default = strptime_date(similar_case["FID_KYC_Refresh_Date"])
            new_case_form.case_type.default = similar_case["Case_Type"]
            new_case_form.customer_type.default = similar_case["Type"]
            new_case_form.category.default = similar_case["Category"]
            new_case_form.comment.default = default_comment
            new_case_form.process()
            
            new_rmb_form.customer_id.default = similar_case["Customer_ID"]
            new_rmb_form.customer_name.default = similar_case["Customer_Name"]
            new_rmb_form.risk_rating.default = similar_case["Risk_Rating"]
            new_rmb_form.sc_start_date.default = strptime_date(similar_case["Scheduled_Start_Date"])
            new_rmb_form.sc_end_date.default = strptime_date(similar_case["Scheduled_Due_Date"])
            new_rmb_form.txn_start_date.default = strptime_date(similar_case["Transaction_Start_Date"])
            new_rmb_form.txn_end_date.default = strptime_date(similar_case["Transaction_End_Date"])
            new_rmb_form.customer_type.default = similar_case["Type"]
            new_rmb_form.category.default = similar_case["Category"]
            new_rmb_form.comment.default = default_comment
            new_rmb_form.process()
            
            return render_template(
                'create_case.html', find_similar_case_form=find_similar_case_form, 
                new_case_form=new_case_form, new_rmb_form=new_rmb_form, new_cic_form=new_cic_form)
        
    if new_case_form.create_case.data and new_case_form.validate():
        refresh_date, scheduled_start_date, scheduled_end_date, txn_start_date, txn_end_date = cal_dates(
            new_case_form.kyc_refresh_date.data, new_case_form.risk_rating.data)
        comment = new_case_form.comment.data
        
        insert_case = '''
        INSERT INTO CaseTracking_local (
            Customer_ID, Customer_Name, Risk_Rating, FID_KYC_Refresh_Date, Type, Category, 
            Transaction_Start_Date, Transaction_End_Date, Scheduled_Start_Date, Scheduled_Due_Date, 
            Case_Status, Sub_Status, Case_Type, Comment) VALUES (
                ?, ?, ?, ?, ?, ?, 
                ?, ?, ?, ?, 
                ?, ?, ?, ?) '''
        insert_value_lst = (
            new_case_form.customer_id.data.strip(), new_case_form.customer_name.data.strip(), new_case_form.risk_rating.data, refresh_date, 
            new_case_form.customer_type.data, new_case_form.category.data.strip(), 
            txn_start_date, txn_end_date, scheduled_start_date, scheduled_end_date, 
            "Initialized", "Initialized", new_case_form.case_type.data, comment.strip())
        execute_sql(insert_case, insert_value_lst)
        
        flash("Create case successfully!", 'success')
        return redirect(url_for("create.create_case_page"))
    
    if new_rmb_form.create_rmb_case.data and new_rmb_form.validate():
        comment = new_case_form.comment.data
        
        insert_rmb_case = '''
        INSERT INTO CaseTracking_local (
            Customer_ID, Customer_Name, Risk_Rating, Type, Category, 
            Transaction_Start_Date, Transaction_End_Date, Scheduled_Start_Date, Scheduled_Due_Date, 
            Case_Status, Sub_Status, Case_Type, Comment) VALUES (
                ?, ?, ?, ?, ?, 
                ?, ?, ?, ?, 
                ?, ?, ?, ?) '''
        insert_value_lst = (
            new_rmb_form.customer_id.data.strip(), new_rmb_form.customer_name.data.strip(), new_rmb_form.risk_rating.data, 
            new_rmb_form.customer_type.data, new_rmb_form.category.data.strip(), 
            new_rmb_form.txn_start_date.data, new_rmb_form.txn_end_date.data, new_rmb_form.sc_start_date.data, new_rmb_form.sc_end_date.data, 
            "Initialized", "Initialized", "RMB Review", comment.strip())
        execute_sql(insert_rmb_case, insert_value_lst)
        
        flash("Create RMB case successfully!", 'success')
        return redirect(url_for("create.create_case_page"))
    
    if new_cic_form.create_cic_case.data and new_cic_form.validate():
        insert_cic_case = '''
        INSERT INTO CaseTracking_local (
            Customer_Name, Category, Case_Type,
            Transaction_Start_Date, Transaction_End_Date, Scheduled_Start_Date, Scheduled_Due_Date, 
            Case_Status, Sub_Status) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?) '''
        insert_value_lst = (
            new_cic_form.customer_name.data.strip(), new_cic_form.category.data.strip(), new_cic_form.case_type.data.strip(), 
            new_cic_form.txn_start_date.data, new_cic_form.txn_end_date.data, new_cic_form.sc_start_date.data, new_cic_form.sc_end_date.data, 
            "Initialized", "Initialized")
        execute_sql(insert_cic_case, insert_value_lst)
        
        flash("Create CIC case successfully!", 'success')
        
        cursor, cnxn = connect_db()
        if SQL_TYPE == "sql server":
            sql_case_id = f'''
                select top 1 Case_ID from CaseTracking_local where Customer_Name = ? and Category = ? and Case_Type = ? and
                Transaction_Start_Date = ? and Transaction_End_Date = ? and Scheduled_Start_Date = ? and Scheduled_Due_Date = ? 
                order by Case_ID desc'''
            case_id = cursor.execute(
                sql_case_id, 
                (new_cic_form.customer_name.data.strip(), new_cic_form.category.data.strip(), new_cic_form.case_type.data.strip(), 
                new_cic_form.txn_start_date.data, new_cic_form.txn_end_date.data, 
                new_cic_form.sc_start_date.data, new_cic_form.sc_end_date.data)).fetchone().Case_ID
        else:
            sql_case_id = f'''
                select Case_ID from CaseTracking_local where Customer_Name = ? and Category = ? and Case_Type = ? and
                Transaction_Start_Date = ? and Transaction_End_Date = ? and Scheduled_Start_Date = ? and Scheduled_Due_Date = ? 
                order by Case_ID desc limit 1'''
            case_id = cursor.execute(
                sql_case_id, 
                (new_cic_form.customer_name.data.strip(), new_cic_form.category.data.strip(), new_cic_form.case_type.data.strip(), 
                new_cic_form.txn_start_date.data, new_cic_form.txn_end_date.data, 
                new_cic_form.sc_start_date.data, new_cic_form.sc_end_date.data)).fetchone()["Case_ID"]
        cursor.close()
        cnxn.close()
        
        return redirect(url_for("cic_creating.create_cic_page", case_id=case_id))
    
    new_case_form.comment.default = default_comment
    new_case_form.process()
    
    return render_template(
        'create_case.html', find_similar_case_form=find_similar_case_form, 
        new_case_form=new_case_form, new_rmb_form=new_rmb_form, new_cic_form=new_cic_form)
