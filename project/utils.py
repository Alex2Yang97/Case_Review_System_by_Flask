import os
import datetime
import pyodbc
import random
import string
import sqlite3
from uuid import uuid4
import urllib
from sqlalchemy import create_engine
import calendar
from dateutil.relativedelta import relativedelta
import pandas as pd

from .config import (SQL_TYPE, SQL_SERVER_NAME, SQL_SERVER_PWD, 
                     EDD_DB_PATH, DEVELOPERS, USER_ADMIN_PATH, TEST, NAME_DICT)


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def connect_db(db_path=EDD_DB_PATH, sql_type=SQL_TYPE):
    if sql_type == "sql server":
        cnxn_str = (
                "Driver={SQL Server Native Client 11.0};"
                "Server=22.232.1.190;"
                "Database=DB_Alex;"
                f"UID={SQL_SERVER_NAME};"
                f"PWD={SQL_SERVER_PWD};")
        cnxn = pyodbc.connect(cnxn_str)
        cursor = cnxn.cursor()
        
    elif sql_type == "sqlite":
        cnxn = sqlite3.connect(db_path) 
        cnxn.row_factory = dict_factory
        cursor = cnxn.cursor()
    else:
        raise Exception("Please specify sql server or sqlite.") 
    return cursor, cnxn


def execute_sql(sql_str, *params, db_path=EDD_DB_PATH, sql_type=SQL_TYPE):
    cursor, cnxn = connect_db(db_path=db_path, sql_type=sql_type)
    cursor.execute(sql_str, *params)
    cnxn.commit()
    cursor.close()
    cnxn.close()


def select_sql(sql_str, *params, single=True, db_path=EDD_DB_PATH, sql_type=SQL_TYPE):
    cursor, cnxn = connect_db(db_path, sql_type)
    if single:
        res = cursor.execute(sql_str, *params).fetchone()
        
        if sql_type == "sql server":
            columns = [column[0] for column in cursor.description]
            res = dict(zip(columns, res))
    else:
        res = cursor.execute(sql_str, *params).fetchall()
        
        if sql_type == "sql server":
            columns = [column[0] for column in cursor.description]
            results = []
            for row in res:
                results.append(dict(zip(columns, row)))
            res = results
            
    cursor.close()
    cnxn.close()
    return res


def get_db_engine():
    params = urllib.parse.quote_plus(
        r"DRIVER={SQL Server Native Client 11.0};"
        "SERVER=22.232.1.190;"
        "DATABASE=DB_Alex;"
        f"UID={SQL_SERVER_NAME};"
        f"PWD={SQL_SERVER_PWD};")

    conn_str = 'mssql+pyodbc:///?odbc_connect={}'.format(params)
    engine = create_engine(conn_str)
    return engine


def get_name(user_name=None, show_name=None, name_dict=NAME_DICT):
    if user_name:
        show_name = name_dict[user_name] if user_name in name_dict else user_name
        return show_name
    
    if show_name:
        show_name_dict = {}
        for key, value in name_dict.items():
            show_name_dict[value] = key
        user_name = show_name_dict[show_name] if show_name in show_name_dict else show_name
        return user_name



def get_analyst_lst(role="Data_analyst", test=TEST):
    conn = sqlite3.connect(USER_ADMIN_PATH)
    analyst_lst = pd.read_sql(f"SELECT Name from User_Info where {role} = 1", conn)["Name"].tolist()
    if not test:
        # admin_manager = pd.read_sql(f"SELECT Name from User_Info where Name in {DEVELOPERS} ", conn)["Name"].tolist()
        analyst_lst = [name for name in analyst_lst if name not in DEVELOPERS]
        
    analyst_lst = [NAME_DICT[name] if name in NAME_DICT else name for name in analyst_lst]
    conn.close()
    return analyst_lst

    
def rand_pass(size=10):
        
    # Takes random choices from
    # ascii_letters and digits
    generate_pass = ''.join([random.choice( string.ascii_uppercase +
                                            string.ascii_lowercase +
                                            string.digits)
                                            for n in range(size)])
                            
    return generate_pass


def make_unique(string):
    ident = uuid4().__str__()
    return f"{ident}-{string}"


def cal_dates(refresh_date, risk_rating):
    scheduled_start_date = (refresh_date - relativedelta(months=4)).replace(day=1)
    
    scheduled_end_date = (refresh_date - relativedelta(months=3))
    scheduled_end_date = scheduled_end_date.replace(day=calendar.monthrange(scheduled_end_date.year, scheduled_end_date.month)[-1])
    
    txn_end_date = scheduled_start_date - relativedelta(days=1)

    if risk_rating == "High":
        txn_start_date = txn_end_date - relativedelta(years=1) + relativedelta(days=1)
    elif risk_rating == "Medium":
        txn_start_date = txn_end_date - relativedelta(years=2) + relativedelta(days=1)
    else:
        txn_start_date = txn_end_date - relativedelta(years=3) + relativedelta(days=1)
    
    return (refresh_date, scheduled_start_date, scheduled_end_date, 
            txn_start_date, txn_end_date)
    
    
def get_case(case_id):
    case = select_sql(f'''
        select Case_Status, Customer_ID, Customer_Name, Risk_Rating, Category, Type, 
        FID_KYC_Refresh_Date, Volume, Nested_Volume, Number_of_SARs, 
        Scheduled_Start_Date, Scheduled_Due_Date, Transaction_Start_Date, Transaction_End_Date, 
        Nested_Value, Value, High_Risk_Country_Vol_Percentage, High_Risk_Country_Val_Percentage, 
        Research_Entities_Volume, Comment, Case_ID 
        from casetracking_local where case_id = {case_id}''')
    return case


def strptime_date(date_value, date_format='%Y-%m-%d', sql_type=SQL_TYPE):
    if sql_type == "sql server":
        return date_value
    else:
        if not date_format:
            raise Exception("Please specify date format.") 
            
        return datetime.datetime.strptime(date_value, date_format) if date_value else ""
        

def show_step_card(case_id, case_status):
    full_step_lst = [
        "Data", "Data QC", "Research", "Research QC", "Report", "Report QC", "Recommendation & Referral"
    ]
    step_name_lst = [
        "Data", "DataQC", "Research", "ResearchQC", "Report", "ReportQC", "Rec/Ref"
    ]
    
    if case_status not in full_step_lst:
        return get_step_info(case_id, case_status)
    else:
        step_name = step_name_lst[full_step_lst.index(case_status)]
        return get_step_info(case_id, step_name)


def get_step_info(case_id, step_name):
    cursor, cnxn = connect_db()
    case_step_info = cursor.execute(f'''
        select Data_Analyst, Data_Start_Date, 
        Data_QC_Analyst, Data_QC_Complete_Date, 
        Research_Analyst, Research_Started_Date, Research_Complete_Date, 
        Research_QC_Analyst, Research_QC_Start_Date, Research_QC_Complete_Date, 
        Report_Analyst, Report_Start_Date, Report_Complete_Date, 
        Report_QC_Analyst, Report_QC_Start_Date, Report_QC_Complete_Date 
        from casetracking_local where case_id = {case_id}''').fetchone()
    cursor.close()
    cnxn.close()
    if SQL_TYPE == "sql server":
        steps = [
            {"name": "Data", "description": "Pending", "status": "not_started", 
            "analyst": case_step_info.Data_Analyst, 
            "start": "...",
            "end": case_step_info.Data_Start_Date.strftime('%Y-%m-%d') if case_step_info.Data_Start_Date else ""},
            {"name": "DataQC", "description": "Pending", "status": "not_started",
            "analyst": case_step_info.Data_QC_Analyst, 
            "start": "...", 
            "end": case_step_info.Data_QC_Complete_Date.strftime('%Y-%m-%d') if case_step_info.Data_QC_Complete_Date else ""},
            {"name": "Research", "description": "Pending", "status": "not_started",
            "analyst": case_step_info.Research_Analyst, 
            "start": case_step_info.Research_Started_Date.strftime('%Y-%m-%d') if case_step_info.Research_Started_Date else "", 
            "end": case_step_info.Research_Complete_Date.strftime('%Y-%m-%d') if case_step_info.Research_Complete_Date else ""},
            {"name": "ResearchQC", "description": "Pending", "status": "not_started",
            "analyst": case_step_info.Research_QC_Analyst, 
            "start": case_step_info.Research_QC_Start_Date.strftime('%Y-%m-%d') if case_step_info.Research_QC_Start_Date else "", 
            "end": case_step_info.Research_QC_Complete_Date.strftime('%Y-%m-%d') if case_step_info.Research_QC_Complete_Date else ""},
            {"name": "Report", "description": "Pending", "status": "not_started",
            "analyst": case_step_info.Report_Analyst, 
            "start": case_step_info.Report_Start_Date.strftime('%Y-%m-%d') if case_step_info.Report_Start_Date else "", 
            "end": case_step_info.Report_Complete_Date.strftime('%Y-%m-%d') if case_step_info.Report_Complete_Date else ""},
            {"name": "ReportQC", "description": "Pending", "status": "not_started",
            "analyst": case_step_info.Report_QC_Analyst, 
            "start": case_step_info.Report_QC_Start_Date.strftime('%Y-%m-%d') if case_step_info.Report_QC_Start_Date else "", 
            "end": case_step_info.Report_QC_Complete_Date.strftime('%Y-%m-%d') if case_step_info.Report_QC_Complete_Date else ""},
            {"name": "Rec/Ref", "description": "Pending", "status": "not_started",
            "analyst": "", 
            "start": "", 
            "end": ""}
        ]
    else:
        steps = [
            {"name": "Data", "description": "Pending", "status": "not_started", 
            "analyst": case_step_info["Data_Analyst"], 
            "start": "...",
            "end": case_step_info["Data_Start_Date"] if case_step_info["Data_Start_Date"] else ""},
            {"name": "DataQC", "description": "Pending", "status": "not_started",
            "analyst": case_step_info["Data_QC_Analyst"], 
            "start": "...", 
            "end": case_step_info["Data_QC_Complete_Date"] if case_step_info["Data_QC_Complete_Date"] else ""},
            {"name": "Research", "description": "Pending", "status": "not_started",
            "analyst": case_step_info["Research_Analyst"], 
            "start": case_step_info["Research_Started_Date"] if case_step_info["Research_Started_Date"] else "", 
            "end": case_step_info["Research_Complete_Date"] if case_step_info["Research_Complete_Date"] else ""},
            {"name": "ResearchQC", "description": "Pending", "status": "not_started",
            "analyst": case_step_info["Research_QC_Analyst"], 
            "start": case_step_info["Research_QC_Start_Date"] if case_step_info["Research_QC_Start_Date"] else "", 
            "end": case_step_info["Research_QC_Complete_Date"] if case_step_info["Research_QC_Complete_Date"] else ""},
            {"name": "Report", "description": "Pending", "status": "not_started",
            "analyst": case_step_info["Report_Analyst"], 
            "start": case_step_info["Report_Start_Date"] if case_step_info["Report_Start_Date"] else "", 
            "end": case_step_info["Report_Complete_Date"] if case_step_info["Report_Complete_Date"] else ""},
            {"name": "ReportQC", "description": "Pending", "status": "not_started",
            "analyst": case_step_info["Report_QC_Analyst"], 
            "start": case_step_info["Report_QC_Start_Date"] if case_step_info["Report_QC_Start_Date"] else "", 
            "end": case_step_info["Report_QC_Complete_Date"] if case_step_info["Report_QC_Complete_Date"] else ""},
            {"name": "Rec/Ref", "description": "Pending", "status": "not_started",
            "analyst": "", 
            "start": "", 
            "end": ""}
        ]
        
    if (step_name == "Initialized") or (step_name == "Created"):
        return steps
    
    for step in steps:
        if step["name"] == step_name:
            step["description"] = "In Progress"
            step["status"] = "in_progress"
            break
        else:
            step["description"] = "Completed"
            step["status"] = "finished"
            
    return steps


def show_percent(current_status, case_status):
    full_step_lst = [
        "Data", "Data QC", "Research", "Research QC", "Report", "Report QC", "Recommendation & Referral", "Closed"
    ]
    
    if (current_status == "Initialized") or (current_status == "Created") or (case_status == "Initialized") or (case_status == "Created"):
        return 0
    
    current_ind = full_step_lst.index(current_status)
    case_status_ind = full_step_lst.index(case_status)

    if current_ind <= case_status_ind:
        return 100
    else:
        return 0


def get_filter_items(db_name="recom", sql_type=SQL_TYPE):
    cursor, cnxn = connect_db()
    if db_name == "recom":
        sql_filter_items = '''
            select distinct Recommendation_ID, Closure_Date as submit_date, 
            recommendation_local.case_id as Case_ID, Customer_Name, Scheduled_Due_Date
            from recommendation_local, casetracking_local where recommendation_local.case_id = casetracking_local.case_id 
            and Case_Status <> 'Removed' and Status <> 'Removed' '''
    elif db_name == "sar":
        sql_filter_items = '''
            select distinct Date_Acknowledged as submit_date, 
            SARref_local.case_id as Case_ID, Customer_Name, Scheduled_Due_Date
            from SARref_local, casetracking_local where SARref_local.case_id = casetracking_local.case_id 
            and Case_Status <> 'Removed' and Status <> 'Removed' '''
    elif db_name == "sanc":
        sql_filter_items = '''
            select distinct Acknowledged_Date as submit_date, 
            SanctionRef_local.case_id as Case_ID, Customer_Name, Scheduled_Due_Date 
            from SanctionRef_local, casetracking_local where SanctionRef_local.case_id = casetracking_local.case_id 
            and Case_Status <> 'Removed' and Status <> 'Removed' '''
    elif db_name == "cic":
        sql_filter_items = '''
            select distinct CIC_Cases.case_id as Case_ID, CIC_Customer_Name, Scheduled_Due_Date 
            from CIC_Cases, casetracking_local where CIC_Cases.case_id = casetracking_local.case_id 
            and Case_Status <> 'Removed' and CIC_Case_Status <> 'Removed' '''
    else:
        sql_filter_items = '''
            SELECT Case_ID, Customer_Name, Scheduled_Due_Date 
            FROM casetracking_local where Case_Status <> 'Removed' '''
        
    filter_res = pd.read_sql(sql_filter_items, cnxn)
    if sql_type == "sqlite":
        filter_res["Scheduled_Due_Date"] = pd.to_datetime(filter_res["Scheduled_Due_Date"])
    cursor.close()
    cnxn.close()
    
    if db_name == "cic":
        customer_name_lst = sorted(filter_res["CIC_Customer_Name"].unique().tolist())
    else:
        customer_name_lst = sorted(filter_res["Customer_Name"].unique().tolist())
    case_id_lst = sorted(filter_res["Case_ID"].unique().tolist())
    case_id_lst = [str(case_id) for case_id in case_id_lst]
    
    if (db_name == "recom") or (db_name == "sar") or (db_name == "sanc"):
        if sql_type == "sqlite":
            filter_res["submit_date"] = pd.to_datetime(filter_res["submit_date"])
            
        submit_date_df = filter_res.dropna(subset=["submit_date"]).drop_duplicates(subset=["submit_date"]).sort_values(by=["submit_date"])
        if submit_date_df.empty:
            submit_date_lst = []
        else:
            submit_date_df["submit_date_str"] = submit_date_df["submit_date"].apply(lambda x: str(x.year) + "-" + str(x.month))
            submit_date_lst = submit_date_df["submit_date_str"].unique().tolist()
    
    due_date_df = filter_res.dropna(subset=["Scheduled_Due_Date"]).drop_duplicates(subset=["Scheduled_Due_Date"]).sort_values(by=["Scheduled_Due_Date"])
    if due_date_df.empty:
        due_date_lst = []
    else:
        due_date_df["due_date"] = due_date_df["Scheduled_Due_Date"].apply(lambda x: str(x.year) + "-" + str(x.month))
        due_date_lst = due_date_df["due_date"].unique().tolist()
        
    if db_name == "recom":
        recom_id_lst = filter_res["Recommendation_ID"].astype(str).unique().tolist()
        return case_id_lst, due_date_lst, submit_date_lst, customer_name_lst, recom_id_lst
    elif (db_name == "case") or (db_name == "cic"):
        return case_id_lst, due_date_lst, customer_name_lst
    else:
        return case_id_lst, due_date_lst, submit_date_lst, customer_name_lst
