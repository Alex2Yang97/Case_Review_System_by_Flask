import io
import datetime
import pandas as pd

from flask import render_template, request, url_for, redirect, Blueprint, make_response, Response
from flask_login import login_required

from .forms import FilterCase, RecomFilter, SARFilter, SancFilter, CICCasesFilter
from .utils import connect_db, get_filter_items
from .config import SQL_TYPE

preview = Blueprint('preview', __name__)


def apply_filter(filter_form, all_df, db_name, sql_type=SQL_TYPE):    
    if filter_form.case_id_sel.data:
        case_id_lst = [int(case_id) for case_id in filter_form.case_id_sel.data]
        all_df = all_df[all_df["Case_ID"].isin(case_id_lst)]
    
    if filter_form.case_due_date_sel.data:
        if sql_type == "sqlite":
            all_df['Scheduled_Due_Date_dt'] = pd.to_datetime(all_df['Scheduled_Due_Date'])
        all_df["case_due_select"] = all_df["Scheduled_Due_Date_dt"].apply(lambda x: str(x.year) + "-" + str(x.month))
        all_df = all_df[all_df["case_due_select"].isin(filter_form.case_due_date_sel.data)]
        all_df = all_df.drop(columns=["Scheduled_Due_Date_dt", "case_due_select"])
    
    if db_name == "cic":
        if filter_form.customer_name_sel.data:
            all_df = all_df[all_df["CIC_Customer_Name"].isin(filter_form.customer_name_sel.data)]
    else:
        if filter_form.customer_name_sel.data:
            all_df = all_df[all_df["Customer_Name"].isin(filter_form.customer_name_sel.data)]
    
    if db_name == "recom":
        if filter_form.recom_id_sel.data:
            recom_id_lst = [int(case_id) for case_id in filter_form.recom_id_sel.data]
            all_df = all_df[all_df["Recommendation_ID"].isin(recom_id_lst)]
            
    if (db_name == "recom") or (db_name == "sar") or (db_name == "sanc"):
    
        if db_name == "recom":
            submit_date_name = "Closure_Date"
        if db_name == "sar":
            submit_date_name = "Date_Acknowledged"
        if db_name == "sanc":
            submit_date_name = "Acknowledged_Date"
            
        if filter_form.date_submit_sel.data:
            all_df = all_df.dropna(subset=[submit_date_name])
            if sql_type == "sqlite":
                all_df['Closure_Date_dt'] = pd.to_datetime(all_df[submit_date_name])
            all_df["date_submit_select"] = all_df["Closure_Date_dt"].apply(lambda x: str(x.year) + "-" + str(x.month))
            all_df = all_df[all_df["date_submit_select"].isin(filter_form.date_submit_sel.data)]
            all_df = all_df.drop(columns=["Closure_Date_dt", "date_submit_select"])
            
    if (db_name == "case"):
        if filter_form.case_status_sel.data:
            all_df = all_df[all_df["Case_Status"].isin(filter_form.case_status_sel.data)]
            
    return all_df


@preview.route('/preview_case', methods=['GET', 'POST'])
@login_required
def preview_case_page():
    filter_case_form = FilterCase()
    
    # 因为用户会更改scheduled date，所以导致 due_date_lst 会更新
    # 如果不加下面的几句，选项不能实时更新（因为 form 已经被实例化，不能重新运行在 FilterCase类中的 get_filter_items 函数）
    case_id_lst, due_date_lst, customer_name_lst = get_filter_items("case")
    filter_case_form.case_id_sel.choices = case_id_lst
    filter_case_form.case_due_date_sel.choices = due_date_lst
    filter_case_form.customer_name_sel.choices = customer_name_lst
    
    cursor, cnxn = connect_db()
    sql_get_cases = '''
        SELECT Case_ID, Case_Status, Case_Type, Risk_Rating, FID_KYC_Refresh_Date, Volume, Category, 
        Customer_ID, Customer_Name, Type, Nested_Volume, Scheduled_Start_Date, Scheduled_Due_Date, Number_of_SARs, Comment 
        FROM casetracking_local where Case_Status <> 'Removed' '''
    cases = pd.read_sql(sql_get_cases, cnxn)
    cases[["Number_of_SARs", "Nested_Volume", "Volume"]] = cases[["Number_of_SARs", "Nested_Volume", "Volume"]].fillna(0)
    cases[["Number_of_SARs", "Nested_Volume", "Volume"]] = cases[["Number_of_SARs", "Nested_Volume", "Volume"]].astype(int)
    if not cases.empty:
        if SQL_TYPE == "sql server":
            today = pd.to_datetime('today').date()
            cases['Days_Over_Due'] = (today - cases['Scheduled_Due_Date']).dt.days
        else:
            today = pd.to_datetime('today')
            cases['Days_Over_Due'] = (today - pd.to_datetime(cases['Scheduled_Due_Date'])).dt.days
        cases['Days_Over_Due'] = cases['Days_Over_Due'].apply(lambda x: 0 if x <= 0 else x)
    cursor.close()
    cnxn.close()
    
    if filter_case_form.filter_cases.data and filter_case_form.validate():
        cases = apply_filter(filter_case_form, cases, db_name="case")
        return render_template('preview_case.html', cases=cases, filter_case_form=filter_case_form)
    
    if filter_case_form.export_cases.data and filter_case_form.validate():
        cases = apply_filter(filter_case_form, cases, db_name="case")
        
        # case_df = pd.read_sql(sql_filter_case, cnxn)
        # resp = make_response(case_df.to_csv(index=False))
        # resp.headers["Content-Disposition"] = f"attachment; filename=Cases-Start_{filter_start_date}-End_{filter_end_date}.csv"
        # resp.headers["Content-Type"] = "text/csv"
        # return resp
        
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        buffer = io.BytesIO()
        cases.to_excel(buffer, index=False)
        headers = {
            'Content-Disposition': f'attachment; filename=Cases-{date_str}.xlsx',
            'Content-type': 'application/vnd.ms-excel'
        }
        return Response(buffer.getvalue(), mimetype='application/vnd.ms-excel', headers=headers)


    return render_template('preview_case.html', cases=cases, filter_case_form=filter_case_form)


@preview.route('/preview_case_for_tracking', methods=['GET', 'POST'])
@login_required
def preview_case_for_tracking():
    filter_case_form = FilterCase()
    case_id_lst, due_date_lst, customer_name_lst = get_filter_items("case")
    filter_case_form.case_id_sel.choices = case_id_lst
    filter_case_form.case_due_date_sel.choices = due_date_lst
    filter_case_form.customer_name_sel.choices = customer_name_lst
    
    cursor, cnxn = connect_db()
    sql_get_cases = '''SELECT * FROM casetracking_local where Case_Status <> 'Removed' '''
    cases = pd.read_sql(sql_get_cases, cnxn)
    cases[["Number_of_SARs", "Nested_Volume", "Volume"]] = cases[["Number_of_SARs", "Nested_Volume", "Volume"]].fillna(0)
    cases[["Number_of_SARs", "Nested_Volume", "Volume"]] = cases[["Number_of_SARs", "Nested_Volume", "Volume"]].astype(int)
    if not cases.empty:
        if SQL_TYPE == "sql server":
            today = pd.to_datetime('today').date()
            cases['Days_Over_Due'] = (today - cases['Scheduled_Due_Date']).dt.days
        else:
            today = pd.to_datetime('today')
            cases['Days_Over_Due'] = (today - pd.to_datetime(cases['Scheduled_Due_Date'])).dt.days
        cases['Days_Over_Due'] = cases['Days_Over_Due'].apply(lambda x: 0 if x <= 0 else x)
    cursor.close()
    cnxn.close()
    
    # EDD Tracking only for Event Triggers and Periodic Refresh (Over 90 days)
    trigger_event_cases = cases[cases["Case_Type"] == "Trigger Event"]
    
    if SQL_TYPE == "sql server":
        today = pd.to_datetime('today').date()
        cases['after_report_qc'] = (today - cases['Report_QC_Complete_Date']).dt.days
    else:
        today = pd.to_datetime('today')
        cases['after_report_qc'] = (today - pd.to_datetime(cases['Report_QC_Complete_Date'])).dt.days
    periodic_refresh_cases = cases[
        (cases['after_report_qc'] >= 90) & (cases["Case_Type"] != "Trigger Event")]
    
    cases = pd.concat([trigger_event_cases, periodic_refresh_cases])
    cases = cases.sort_values(by="Case_ID").reset_index(drop=True)

    if filter_case_form.filter_cases.data and filter_case_form.validate():
        cases = apply_filter(filter_case_form, cases, db_name="case")
        return render_template('preview_case_for_tracking.html', cases=cases, filter_case_form=filter_case_form)
    
    if filter_case_form.export_cases.data and filter_case_form.validate():
        cases = apply_filter(filter_case_form, cases, db_name="case")
        
        # case_df = pd.read_sql(sql_filter_case, cnxn)
        # resp = make_response(case_df.to_csv(index=False))
        # resp.headers["Content-Disposition"] = f"attachment; filename=Cases-Start_{filter_start_date}-End_{filter_end_date}.csv"
        # resp.headers["Content-Type"] = "text/csv"
        # return resp
        
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        buffer = io.BytesIO()
        cases.to_excel(buffer, index=False)
        headers = {
            'Content-Disposition': f'attachment; filename=Cases-{date_str}.xlsx',
            'Content-type': 'application/vnd.ms-excel'
        }
        return Response(buffer.getvalue(), mimetype='application/vnd.ms-excel', headers=headers)

    return render_template('preview_case_for_tracking.html', cases=cases, filter_case_form=filter_case_form)


@preview.route('/recommendations', methods=['GET', 'POST'])
@login_required
def recom_page():
    recom_filter_form = RecomFilter()

    case_id_lst, due_date_lst, submit_date_lst, customer_name_lst, recom_id_lst = get_filter_items("recom")
    recom_filter_form.case_id_sel.choices = case_id_lst
    recom_filter_form.case_due_date_sel.choices = due_date_lst
    recom_filter_form.date_submit_sel.choices = submit_date_lst
    recom_filter_form.customer_name_sel.choices = customer_name_lst
    recom_filter_form.recom_id_sel.choices = recom_id_lst
    
    cursor, cnxn = connect_db()
    sql_get_recoms = (
        "select Recommendation_local.Case_ID as Case_ID, Recommendation_ID, Status, Scheduled_Due_Date, Closure_Date, Customer_Name, From_Section, "
        "Initiated_Date, Ack_Action_Date, Recomm_or_Escal, Responsible_Personnel, Action_Details, Followup_Date_1st, Followup_Date_2nd, Last_Followup_Date, "
        "Escalation_Date, Escalation_Type, Escalated_To, Recommendation_Closure_Details, Escal_Recomm_Details "
        "from Recommendation_local, CaseTracking_local where Recommendation_local.Case_ID = CaseTracking_local.Case_ID and Status <> 'Removed' ")
    recoms = pd.read_sql(sql_get_recoms, cnxn)
    if not recoms.empty:
        if SQL_TYPE == "sql server":
            today = pd.to_datetime('today').date()
            recoms['Days_Over_Due'] = (today - recoms['Scheduled_Due_Date']).dt.days
        else:
            today = pd.to_datetime('today')
            recoms['Days_Over_Due'] = (today - pd.to_datetime(recoms['Scheduled_Due_Date'])).dt.days
        recoms['Days_Over_Due'] = recoms['Days_Over_Due'].apply(lambda x: 0 if x <= 0 else x)
    cursor.close()
    cnxn.close()
    
    # for field, errors in recom_filter_form.errors.items():
    #     for error in errors:
    #         print(f'Error in field "{getattr(recom_filter_form, field).label.text}": {error}')
    
    if recom_filter_form.filter_btn.data and recom_filter_form.validate():
        recoms = apply_filter(recom_filter_form, recoms, db_name="recom")
            
        return render_template('recommendations.html', recom_filter_form=recom_filter_form, recoms=recoms)
    
    if recom_filter_form.export_btn.data and recom_filter_form.validate():
        recoms = apply_filter(recom_filter_form, recoms, db_name="recom")
        
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        buffer = io.BytesIO()
        recoms.to_excel(buffer, index=False)
        headers = {
            'Content-Disposition': f'attachment; filename=Recommendations-{date_str}.xlsx',
            'Content-type': 'application/vnd.ms-excel'
        }
        return Response(buffer.getvalue(), mimetype='application/vnd.ms-excel', headers=headers)
    
    return render_template('recommendations.html', recom_filter_form=recom_filter_form, recoms=recoms)


@preview.route('/sar_referrals', methods=['GET', 'POST'])
@login_required
def sar_page():
    sar_filter_form = SARFilter()
    
    case_id_lst, due_date_lst, submit_date_lst, customer_name_lst = get_filter_items("sar")
    sar_filter_form.case_id_sel.choices = case_id_lst
    sar_filter_form.case_due_date_sel.choices = due_date_lst
    sar_filter_form.date_submit_sel.choices = submit_date_lst
    sar_filter_form.customer_name_sel.choices = customer_name_lst
    
    cursor, cnxn = connect_db()
    sql_get_sars = '''
        select SARref_local.Case_ID as Case_ID, SAR_Referral_ID, Status, Customer_ID, Customer_Name, Scheduled_Due_Date, Subject_Name, 
        Activity_Start_Date, Activity_End_Date, Amount, Subject_Account_NO, Referral_Reason, Reviewed_By_SAR, Referral_Necessary, SAR_Team_Comment, 
        Referral_Warranted, EDD_Comment, Initiated_Date, CTRL_CMT, Date_Submitted, Date_Acknowledged 
        from SARref_local, CaseTracking_local where SARref_local.Case_ID = CaseTracking_local.Case_ID and Status <> 'Removed' '''
    
    sars = pd.read_sql(sql_get_sars, cnxn)
    if not sars.empty:
        if SQL_TYPE == "sql server":
            today = pd.to_datetime('today').date()
            sars['Days_Over_Due'] = (today - sars['Scheduled_Due_Date']).dt.days
        else:
            today = pd.to_datetime('today')
            sars['Days_Over_Due'] = (today - pd.to_datetime(sars['Scheduled_Due_Date'])).dt.days
        sars['Days_Over_Due'] = sars['Days_Over_Due'].apply(lambda x: 0 if x <= 0 else x)
    cursor.close()
    cnxn.close()
    
    if sar_filter_form.filter_btn.data and sar_filter_form.validate():
        sars = apply_filter(sar_filter_form, sars, db_name="sar")
        return render_template('sar_referrals.html', sar_filter_form=sar_filter_form, sars=sars)
    
    if sar_filter_form.export_btn.data and sar_filter_form.validate():
        sars = apply_filter(sar_filter_form, sars, db_name="sar")
        
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        buffer = io.BytesIO()
        sars.to_excel(buffer, index=False)
        headers = {
            'Content-Disposition': f'attachment; filename=SAR_Referrals-{date_str}.xlsx',
            'Content-type': 'application/vnd.ms-excel'
        }
        return Response(buffer.getvalue(), mimetype='application/vnd.ms-excel', headers=headers)
    
    return render_template('sar_referrals.html', sar_filter_form=sar_filter_form, sars=sars)


@preview.route('/sanction_referrals', methods=['GET', 'POST'])
@login_required
def sanc_page():
    sanc_filter_form = SancFilter()
    
    case_id_lst, due_date_lst, submit_date_lst, customer_name_lst = get_filter_items("sanc")
    sanc_filter_form.case_id_sel.choices = case_id_lst
    sanc_filter_form.case_due_date_sel.choices = due_date_lst
    sanc_filter_form.date_submit_sel.choices = submit_date_lst
    sanc_filter_form.customer_name_sel.choices = customer_name_lst
    
    cursor, cnxn = connect_db()
    sql_get_sancs = f'''
        select SanctionRef_local.Case_ID as Case_ID, Sanction_Referral_ID, Status, Scheduled_Due_Date, Subject_Name, Amount, Referral_Reason, 
        Customer_ID, Customer_Name, Additional_Comment, Acknowledged_Date, Submit_Date 
        from SanctionRef_local, CaseTracking_local where SanctionRef_local.Case_ID = CaseTracking_local.Case_ID and Status <> 'Removed' '''
    sancs = pd.read_sql(sql_get_sancs, cnxn)
    if not sancs.empty:
        if SQL_TYPE == "sql server":
            today = pd.to_datetime('today').date()
            sancs['Days_Over_Due'] = (today - sancs['Scheduled_Due_Date']).dt.days
        else:
            today = pd.to_datetime('today')
            sancs['Days_Over_Due'] = (today - pd.to_datetime(sancs['Scheduled_Due_Date'])).dt.days
        sancs['Days_Over_Due'] = sancs['Days_Over_Due'].apply(lambda x: 0 if x <= 0 else x)
    cursor.close()
    cnxn.close()
    
    if sanc_filter_form.filter_btn.data and sanc_filter_form.validate():
        sancs = apply_filter(sanc_filter_form, sancs, db_name="sanc")
            
        return render_template('sanction_referrals.html', sanc_filter_form=sanc_filter_form, sancs=sancs)
    
    if sanc_filter_form.export_btn.data and sanc_filter_form.validate():
        sancs = apply_filter(sanc_filter_form, sancs, db_name="sanc")
        
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        buffer = io.BytesIO()
        sancs.to_excel(buffer, index=False)
        headers = {
            'Content-Disposition': f'attachment; filename=Sanction_Referrals-{date_str}.xlsx',
            'Content-type': 'application/vnd.ms-excel'
        }
        return Response(buffer.getvalue(), mimetype='application/vnd.ms-excel', headers=headers)
    
    return render_template('sanction_referrals.html', sanc_filter_form=sanc_filter_form, sancs=sancs)


@preview.route('/cic_cases', methods=['GET', 'POST'])
@login_required
def cic_cases_page():
    cic_cases_form = CICCasesFilter()
    
    case_id_lst, due_date_lst, customer_name_lst = get_filter_items("cic")
    cic_cases_form.case_id_sel.choices = case_id_lst
    cic_cases_form.case_due_date_sel.choices = due_date_lst
    cic_cases_form.customer_name_sel.choices = customer_name_lst
    
    cursor, cnxn = connect_db()
    sql_get_cic_cases = '''
        select CIC_Cases.Case_ID as Case_ID, CIC_Case_ID, CIC_Case_Status, CIC_Customer_ID, CIC_Customer_Name, CIC_Cases.Risk_Rating, 
        CIC_Cases.Type, KyC_Refresh_Date, Scheduled_Start_Date, Customer_ID, Customer_Name, Scheduled_Due_Date, Transaction_Start_Date, Transaction_End_Date, Comments 
        from CIC_Cases, CaseTracking_local where CIC_Cases.Case_ID = CaseTracking_local.Case_ID and Case_Status <> 'Removed' and CIC_Case_Status <> 'Removed' '''
    cic_cases = pd.read_sql(sql_get_cic_cases, cnxn)
    if not cic_cases.empty:
        if SQL_TYPE == "sql server":
            today = pd.to_datetime('today').date()
            cic_cases['Days_Over_Due'] = (today - cic_cases['Scheduled_Due_Date']).dt.days
        else:
            today = pd.to_datetime('today')
            cic_cases['Days_Over_Due'] = (today - pd.to_datetime(cic_cases['Scheduled_Due_Date'])).dt.days
        cic_cases['Days_Over_Due'] = cic_cases['Days_Over_Due'].apply(lambda x: 0 if x <= 0 else x)
    cursor.close()
    cnxn.close()
    
    if cic_cases_form.filter_btn.data and cic_cases_form.validate():
        cic_cases = apply_filter(cic_cases_form, cic_cases, db_name="cic")
            
        return render_template('preview_cic_case.html', cic_cases_form=cic_cases_form, cic_cases=cic_cases)
    
    if cic_cases_form.export_btn.data and cic_cases_form.validate():
        cic_cases = apply_filter(cic_cases_form, cic_cases, db_name="cic")
        
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        buffer = io.BytesIO()
        cic_cases.to_excel(buffer, index=False)
        headers = {
            'Content-Disposition': f'attachment; filename=CIC_Cases-{date_str}.xlsx',
            'Content-type': 'application/vnd.ms-excel'
        }
        return Response(buffer.getvalue(), mimetype='application/vnd.ms-excel', headers=headers)
    
    return render_template('preview_cic_case.html', cic_cases_form=cic_cases_form, cic_cases=cic_cases)
