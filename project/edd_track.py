import os
import sqlite3
from os.path import basename
import zipfile
from datetime import datetime
import pandas as pd

from flask import render_template, flash, Blueprint, redirect,url_for, send_file
from flask_login import login_required, current_user

from werkzeug.utils import secure_filename

from .forms import (StepOne, StepTwo, DownloadFile1, DownloadFile2, DownloadFile3,
                    StepThree, StepFour, StepFive, StepSix, StepSeven, StepEight, StepNine, StepTen,
                    )
from .utils import connect_db, execute_sql, select_sql, cal_dates, get_name, strptime_date
from .models import get_user_info
from .emails import (
    send_step1_email, send_step2_email, send_step3_email, send_step4_email, send_step5_email,
    send_step6_email, send_step7_email, send_step9_email, send_step10_email)
from .config import (
    SQL_TYPE, DOC_TEMPLATES_DIR, FID_RFI_REPORT_DIR, CRR_DRAFTS_DIR, CRR_APPROVED_DIR, REVIEW_DRAFTS_DIR, REVIEW_FROM_KYC_EDD_DIR, REVIEW_FROM_FID_CLIENT_DIR, 
    REVIEW_FOR_APPROVAL_DIR, REVIEW_APPROVED_DIR, USER_ADMIN_PATH)


tracking_edd = Blueprint('tracking_edd', __name__)


def tracking_case_info(case_id):
    case_info = select_sql(f'''
        select Customer_ID, Customer_Name, Risk_Rating, Scheduled_Due_Date 
        FROM casetracking_local where case_id = {case_id}''')
    
    sql_select = f'''
        select Tracking_ID, Case_ID, Tracking_Status, 
            RFI_Analyst, RFI_Initiation_Date, 
            FID_Client, Step2_Date,
            KYC_Analyst, QC_Analyst, Step3_Date, Step3_Analyst,
            FID_BSA_Officer, Step4_Date, Step4_Analyst,
            Step5_Date, Step5_Analyst,
            Step6_Round, Step6_Latest_Time, Step6_Latest_Comment, Step6_Analyst,
            Step7_Round, Step7_Latest_Time, Step7_Latest_Comment, Step7_Analyst,
            Step8_Date, Step8_Analyst,
            Step9_Analyst, Step9_Round, New_Risk_Rating, EDD_Head_Approver, Step9_Latest_Time, Step9_Latest_Comment,
            Step10_Analyst, Step10_Round, Approver_Action, Step10_Latest_Time, Step10_Latest_Comment
        from EDD_tracking where case_id = {case_id}'''
    
    tracking_case = select_sql(sql_select)
     
    return tracking_case, case_info


@tracking_edd.route('/step_1_2/<int:case_id>', methods=['GET', 'POST'])
@login_required
def step_1_2_page(case_id):
    user_name = get_user_info(current_user.get_id()).name
    show_name = get_name(user_name=user_name)
    user_email = get_user_info(current_user.get_id()).email
    
    step_one_form = StepOne()
    step_two_form = StepTwo()
    download_report_form = DownloadFile1()
    download_report_form.download_file1_btn.label.text = "Download Report"
    
    if step_one_form.send_btn.data and step_one_form.validate():
        now_time = datetime.now()
        
        # Save uploaded file
        rfi_report = step_one_form.rfi_report.data
        timestamp = now_time.strftime("%Y-%m-%d_%H-%M-%S")
        filename = timestamp + "_" + secure_filename(rfi_report.filename)
        
        saved_file_dir = os.path.join(FID_RFI_REPORT_DIR, str(case_id))
        if not os.path.exists(saved_file_dir):
            os.makedirs(saved_file_dir)
        rfi_report.save(os.path.join(saved_file_dir, filename))
        
        # Update data in database
        insert_tracking_record = '''
            INSERT INTO EDD_tracking (Case_ID, RFI_Initiation_Date, RFI_Analyst, Tracking_Status, 
            Step6_Round, Step7_Round, Step9_Round, Step10_Round) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?) '''
        execute_sql(
            insert_tracking_record, 
            (case_id, now_time.date(), show_name, 2, 0, 0, 0, 0))
        
        # Send email to FID
        _, case_info = tracking_case_info(case_id)
        message = send_step1_email(
            case_info, user_name=show_name, user_email=user_email, 
            attachment_path=os.path.join(saved_file_dir, filename))
        
        flash(f"Step1 Finish! {message}", "success")
        return redirect(url_for("tracking_edd.step_1_2_page", case_id=case_id))
        
    if step_two_form.send_btn.data and step_two_form.validate():
        now_time = datetime.now()
        
        # Update data in database
        update_tracking_record = f'''
            update EDD_tracking SET Step2_Date = ?, FID_Client = ?, Tracking_Status = ? where Case_ID = {case_id}'''
        execute_sql(update_tracking_record, (now_time.date(), show_name , 3))
        
        # Send email to EDD Team
        _, case_info = tracking_case_info(case_id)
        message = send_step2_email(case_info, user_name=show_name, user_email=user_email)
        
        flash(f"Step2 Finish! {message}", "success")
        return redirect(url_for("tracking_edd.step_1_2_page", case_id=case_id))
    
    if download_report_form.download_file1_btn.data and download_report_form.validate():
        return redirect(url_for("tracking_edd.report_download", case_id=case_id))
    
    tracking_case, case_info = tracking_case_info(case_id)
    if not tracking_case:
        for field in step_two_form:
            field.render_kw = {"disabled": "disabled"}
        download_report_form.download_file1_btn.render_kw = {"disabled": "disabled"}
    else:
        
        tracking_status = tracking_case["Tracking_Status"]
        if tracking_status == 2:
            for field in step_one_form:
                field.render_kw = {"disabled": "disabled"}
        else:
            for field in step_one_form:
                field.render_kw = {"disabled": "disabled"}
            for field in step_two_form:
                field.render_kw = {"disabled": "disabled"}
    
    if tracking_case:
        step_one_form.rfi_analyst.default = tracking_case["RFI_Analyst"]
        step_one_form.rfi_init_date.default = strptime_date(tracking_case["RFI_Initiation_Date"])
        step_one_form.process()
        step_two_form.case_received_date.default = strptime_date(tracking_case["Step2_Date"])
        step_two_form.fid_client.default = tracking_case["FID_Client"]
        step_two_form.process()
    
    return render_template(
        'et_1_2.html', case_id=case_id, case_info=case_info,
        step_one_form=step_one_form, step_two_form=step_two_form, download_report_form=download_report_form)
    

@tracking_edd.route('/step_1_2/template_FI', methods=['GET'])
@login_required
def template_FI_download():
    template_name = os.path.join(DOC_TEMPLATES_DIR, "KYC_RFI_Template_FI.docx")
    return send_file(template_name, as_attachment=True)


@tracking_edd.route('/step_1_2/template_NBFI', methods=['GET'])
@login_required
def template_NBFI_download():
    template_name = os.path.join(DOC_TEMPLATES_DIR, "KYC_RFI_Template_NBFI.docx")
    return send_file(template_name, as_attachment=True)


@tracking_edd.route('/step_1_2/report/<int:case_id>', methods=['GET'])
@login_required
def report_download(case_id):
    saved_file_dir = os.path.join(FID_RFI_REPORT_DIR, str(case_id))   
    name_list = os.listdir(saved_file_dir)
    full_list = [os.path.join(saved_file_dir,i) for i in name_list]
    full_list = sorted(full_list, key=os.path.getmtime, reverse=True)
    return send_file(full_list[0], as_attachment=True)


@tracking_edd.route('/step_3_4/<int:case_id>', methods=['GET', 'POST'])
@login_required
def step_3_4_page(case_id):
    user_name = get_user_info(current_user.get_id()).name
    show_name = get_name(user_name=user_name)
    user_email = get_user_info(current_user.get_id()).email
    
    step_three_form = StepThree()
    step_four_form = StepFour()
    step_five_form = StepFive()
    download_refresh_review = DownloadFile1()
    download_refresh_review.download_file1_btn.label.text = "Download KYC Refresh Review"
    download_reviewed_crr_form = DownloadFile2()
    download_reviewed_crr_form.download_file2_btn.label.text = "Download Reviewed CRR"
    download_approved_crr_form = DownloadFile3()
    download_approved_crr_form.download_file3_btn.label.text = "Download Approved CRR"
    
    if step_three_form.send_btn.data and step_three_form.validate():
        now_time = datetime.now()
        
        # Save uploaded file
        crr_draft = step_three_form.crr_draft.data
        kyc_form = step_three_form.kyc_form.data
        timestamp = now_time.strftime("%Y-%m-%d_%H-%M-%S")
        filename_crr_draft = timestamp + "_" + secure_filename(crr_draft.filename)
        filename_kyc_form = timestamp + "_" + secure_filename(kyc_form.filename)
        
        saved_file_dir = os.path.join(REVIEW_DRAFTS_DIR, str(case_id))
        if not os.path.exists(saved_file_dir):
            os.makedirs(saved_file_dir)
        crr_draft.save(os.path.join(saved_file_dir, filename_crr_draft))
        kyc_form.save(os.path.join(saved_file_dir, filename_kyc_form))
        
        update_tracking_record = f'''
            update EDD_tracking SET KYC_Analyst = ?, QC_Analyst = ?, Step3_Date = ?, Step3_Analyst = ?, Tracking_Status = ? where Case_ID = {case_id}'''
        execute_sql(update_tracking_record, (step_three_form.kyc_analyst.data, step_three_form.qc_analyst.data, now_time.date(), show_name, 4))
        
        tracking_case, case_info = tracking_case_info(case_id)
        
        conn = sqlite3.connect(USER_ADMIN_PATH)
        curs = conn.cursor()
        qc_analyst_user_name = get_name(show_name=tracking_case["QC_Analyst"])
        qc_analyst_email = curs.execute(
            "SELECT Email from User_Info where Name = (?)", [qc_analyst_user_name]).fetchone()[0]
        curs.close()
        conn.close()
        
        message = send_step3_email(
            tracking_case["QC_Analyst"], case_info, user_name=show_name, user_email=[user_email, qc_analyst_email],
            attachment_path_lst=[os.path.join(saved_file_dir, filename_crr_draft), os.path.join(saved_file_dir, filename_kyc_form)])
        
        flash(f"Step3 Finish! {message}", "success")
        return redirect(url_for("tracking_edd.step_3_4_page", case_id=case_id))

    if download_refresh_review.download_file1_btn.data and download_refresh_review.validate():
        return redirect(url_for("tracking_edd.refresh_review_download", case_id=case_id))

    if step_four_form.send_btn.data and step_four_form.validate():
        crr_draft = step_four_form.crr_draft.data
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = timestamp + "_" + secure_filename(crr_draft.filename)
        
        saved_file_dir = os.path.join(CRR_DRAFTS_DIR, str(case_id))
        if not os.path.exists(saved_file_dir):
            os.makedirs(saved_file_dir)
        crr_draft.save(os.path.join(saved_file_dir, filename))
        
        update_tracking_record = f'''
            update EDD_tracking SET FID_BSA_Officer = ?, Step4_Date = ?, Step4_Analyst = ?, Tracking_Status = ? where Case_ID = {case_id}'''
        execute_sql(update_tracking_record, (step_four_form.fid_bsa_officer.data, datetime.now().date(), show_name, 5))
        
        tracking_case, case_info = tracking_case_info(case_id)
        
        officer_user_name = get_name(show_name=tracking_case["FID_BSA_Officer"])
        fid_bsa_officer_email = select_sql(
            "SELECT Email from User_Info where Name = (?)",
            [officer_user_name],
            db_path=USER_ADMIN_PATH)["Email"]
        message = send_step4_email(
            tracking_case["FID_BSA_Officer"], case_info, user_name=show_name, user_email=[user_email, fid_bsa_officer_email],
            attachment_path=os.path.join(saved_file_dir, filename))
        
        flash(f"Step4 Finish! {message}", "success")
        return redirect(url_for("tracking_edd.step_3_4_page", case_id=case_id))
    
    if download_reviewed_crr_form.download_file2_btn.data and download_reviewed_crr_form.validate():
        return redirect(url_for("tracking_edd.reviewed_crr_download", case_id=case_id))
    
    if step_five_form.approve_btn.data and step_five_form.validate():
        approved_crr = step_five_form.approved_crr.data
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = timestamp + "_" + secure_filename(approved_crr.filename)
        
        saved_file_dir = os.path.join(CRR_APPROVED_DIR, str(case_id))
        if not os.path.exists(saved_file_dir):
            os.makedirs(saved_file_dir)
        approved_crr.save(os.path.join(saved_file_dir, filename))
        
        update_tracking_record = f'''
            update EDD_tracking SET Step5_Date = ?, Step5_Analyst = ?, Tracking_Status = ? where Case_ID = {case_id}'''
        execute_sql(update_tracking_record, (datetime.now().date(), show_name, 6))
        
        tracking_case, case_info = tracking_case_info(case_id)
        message = send_step5_email(
            tracking_case["QC_Analyst"], case_info, user_name=show_name, user_email=user_email,
            attachment_path=os.path.join(saved_file_dir, filename))
        
        flash(f"Step5 Finish! {message}", "success")
        return redirect(url_for("tracking_edd.step_3_4_page", case_id=case_id)) 
    
    if download_approved_crr_form.download_file3_btn.data and download_approved_crr_form.validate():
        return redirect(url_for("tracking_edd.approved_crr_download", case_id=case_id))
    
    tracking_case, case_info = tracking_case_info(case_id)
    if not tracking_case:
        for field in step_three_form:
            field.render_kw = {"disabled": "disabled"}
        for field in step_four_form:
            field.render_kw = {"disabled": "disabled"}
        for field in step_five_form:
            field.render_kw = {"disabled": "disabled"}
        download_refresh_review.download_file1_btn.render_kw = {"disabled": "disabled"}
        download_reviewed_crr_form.download_file2_btn.render_kw = {"disabled": "disabled"}
        download_approved_crr_form.download_file3_btn.render_kw = {"disabled": "disabled"}
    else:
        tracking_status = tracking_case["Tracking_Status"]
        if tracking_status < 3:
            for field in step_three_form:
                field.render_kw = {"disabled": "disabled"}
            for field in step_four_form:
                field.render_kw = {"disabled": "disabled"}
            for field in step_five_form:
                field.render_kw = {"disabled": "disabled"}
            download_refresh_review.download_file1_btn.render_kw = {"disabled": "disabled"}
            download_reviewed_crr_form.download_file2_btn.render_kw = {"disabled": "disabled"}
            download_approved_crr_form.download_file3_btn.render_kw = {"disabled": "disabled"}
        elif tracking_status == 3:
            for field in step_four_form:
                field.render_kw = {"disabled": "disabled"}
            for field in step_five_form:
                field.render_kw = {"disabled": "disabled"}
            download_refresh_review.download_file1_btn.render_kw = {"disabled": "disabled"}
            download_reviewed_crr_form.download_file2_btn.render_kw = {"disabled": "disabled"}
            download_approved_crr_form.download_file3_btn.render_kw = {"disabled": "disabled"}
        elif tracking_status == 4:
            for field in step_three_form:
                field.render_kw = {"disabled": "disabled"}
            for field in step_five_form:
                field.render_kw = {"disabled": "disabled"}
            download_reviewed_crr_form.download_file2_btn.render_kw = {"disabled": "disabled"}
            download_approved_crr_form.download_file3_btn.render_kw = {"disabled": "disabled"}
        elif tracking_status == 5:
            for field in step_three_form:
                field.render_kw = {"disabled": "disabled"}
            for field in step_four_form:
                field.render_kw = {"disabled": "disabled"}
            download_approved_crr_form.download_file3_btn.render_kw = {"disabled": "disabled"}
        else:
            for field in step_three_form:
                field.render_kw = {"disabled": "disabled"}
            for field in step_four_form:
                field.render_kw = {"disabled": "disabled"}
            for field in step_five_form:
                field.render_kw = {"disabled": "disabled"}
        
        step_three_form.kyc_analyst.default = tracking_case["KYC_Analyst"]
        step_three_form.qc_analyst.default = tracking_case["QC_Analyst"]
        step_three_form.step3_date.default = strptime_date(tracking_case["Step3_Date"])
        step_three_form.process()
        step_four_form.fid_bsa_officer.default = tracking_case["FID_BSA_Officer"]
        step_four_form.submit_date.default = strptime_date(tracking_case["Step4_Date"])
        step_four_form.process()
        step_five_form.approve_date.default = strptime_date(tracking_case["Step5_Date"])
        step_five_form.process()
    
    return render_template(
        'et_3_4.html', case_id=case_id, case_info=case_info,
        step_three_form=step_three_form, step_four_form=step_four_form, step_five_form=step_five_form, download_refresh_review=download_refresh_review,
        download_reviewed_crr_form=download_reviewed_crr_form, download_approved_crr_form=download_approved_crr_form)


@tracking_edd.route('/step_3_4/crr_FI_template', methods=['GET'])
@login_required
def template_crr_FI_download():
    template_name = os.path.join(DOC_TEMPLATES_DIR, "CRR_FI_Calculator_v.3.3.xlsx")
    return send_file(template_name, as_attachment=True)


@tracking_edd.route('/step_3_4/crr_template', methods=['GET'])
@login_required
def template_crr_FINCB_download():
    template_name = os.path.join(DOC_TEMPLATES_DIR, "CRR_NNP_FI-NCB_Calculator_v.3.6.xlsx")
    return send_file(template_name, as_attachment=True)


@tracking_edd.route('/step_3_4/KYC_form_template', methods=['GET'])
@login_required
def template_KYC_form_download():
    template_name = os.path.join(DOC_TEMPLATES_DIR, "Customer KYC Form.xlsx")
    return send_file(template_name, as_attachment=True)


@tracking_edd.route('/step_3_4/refresh_review/<int:case_id>', methods=['GET'])
@login_required
def refresh_review_download(case_id):
    saved_file_dir = os.path.join(REVIEW_DRAFTS_DIR, str(case_id))   
    name_list = os.listdir(saved_file_dir)
    full_list = [os.path.join(saved_file_dir,i) for i in name_list]
    full_list = sorted(full_list, key=os.path.getmtime, reverse=True)
    
    zipf = zipfile.ZipFile(os.path.join(saved_file_dir, 'KYC_Refresh_Review.zip'),'w', zipfile.ZIP_DEFLATED)
    for file in [full_list[0], full_list[1]]:
        # 这样可以只存文件名，不会有全部路径
        zipf.write(file, basename(file))
    zipf.close()
    return send_file(os.path.join(saved_file_dir, 'KYC_Refresh_Review.zip'),
            mimetype = 'zip',
            download_name= 'KYC_Refresh_Review.zip',
            as_attachment = True)


@tracking_edd.route('/step_3_4/crr_reviewed/<int:case_id>', methods=['GET'])
@login_required
def reviewed_crr_download(case_id):
    saved_file_dir = os.path.join(CRR_DRAFTS_DIR, str(case_id))   
    name_list = os.listdir(saved_file_dir)
    full_list = [os.path.join(saved_file_dir,i) for i in name_list]
    full_list = sorted(full_list, key=os.path.getmtime, reverse=True)
    return send_file(full_list[0], as_attachment=True)


@tracking_edd.route('/step_3_4/crr_approved/<int:case_id>', methods=['GET'])
@login_required
def approved_crr_download(case_id):
    saved_file_dir = os.path.join(CRR_APPROVED_DIR, str(case_id))   
    name_list = os.listdir(saved_file_dir)
    full_list = [os.path.join(saved_file_dir,i) for i in name_list]
    full_list = sorted(full_list, key=os.path.getmtime, reverse=True)
    return send_file(full_list[0], as_attachment=True)


@tracking_edd.route('/step_5_6_7/<int:case_id>', methods=['GET', 'POST'])
@login_required
def step_5_6_7_page(case_id):
    user_name = get_user_info(current_user.get_id()).name
    show_name = get_name(user_name=user_name)
    user_email = get_user_info(current_user.get_id()).email
    
    step_six_form = StepSix()
    step_seven_form = StepSeven()
    step_eight_form = StepEight()
    download_review_from_kyc_edd = DownloadFile1()
    download_review_from_kyc_edd.download_file1_btn.label.text = "Download Review from KYC EDD Team"
    download_review_from_fid_client = DownloadFile2()
    download_review_from_fid_client.download_file2_btn.label.text = "Download Review from FID-Client"
    
    if step_six_form.step6_send_btn.data and step_six_form.validate():
        now_time = datetime.now()
        
        # Save uploaded file
        review_from_edd = step_six_form.kyc_refresh_review.data
        timestamp = now_time.strftime("%Y-%m-%d_%H-%M-%S")
        filename_review_from_edd = timestamp + "_" + secure_filename(review_from_edd.filename)
        
        saved_file_dir = os.path.join(REVIEW_FROM_KYC_EDD_DIR, str(case_id))
        if not os.path.exists(saved_file_dir):
            os.makedirs(saved_file_dir)
        review_from_edd.save(os.path.join(saved_file_dir, filename_review_from_edd))
        
        # Update data in database
        tracking_case, case_info = tracking_case_info(case_id)
        
        update_tracking_record = f'''
            update EDD_tracking SET Step6_Round = ?, Step6_Latest_Time = ?, Step6_Latest_Comment = ?, Step6_Analyst = ?, Tracking_Status = ? where Case_ID = {case_id}'''
        execute_sql(
            update_tracking_record, 
            (tracking_case["Step6_Round"]+1, now_time, step_six_form.step6_comment.data, show_name, 7))
        
        insert_step6_record = '''
            INSERT INTO Track_step6 (Tracking_ID, Step6_Round, Step6_Analyst, Step6_Time, Step6_Comment) 
            VALUES (?, ?, ?, ?, ?) '''
        execute_sql(
            insert_step6_record, 
            (tracking_case["Tracking_ID"], tracking_case["Step6_Round"]+1, show_name, now_time, step_six_form.step6_comment.data))
        
        # Send email to FID-Client
        fid_kyc_analyst_user_name = get_name(show_name=tracking_case["FID_Client"])
        fid_kyc_analyst_email = select_sql(
            "SELECT Email from User_Info where Name = (?)",
            [fid_kyc_analyst_user_name],
            db_path=USER_ADMIN_PATH)["Email"]
        
        message = send_step6_email(
            tracking_case["FID_Client"], case_info, user_name=show_name, user_email=[user_email, fid_kyc_analyst_email], 
            attachment_path=os.path.join(saved_file_dir, filename_review_from_edd))
        
        flash(f"Step6 Finish! {message}", "success")
        return redirect(url_for("tracking_edd.step_5_6_7_page", case_id=case_id))
    
    if download_review_from_kyc_edd.download_file1_btn.data and download_review_from_kyc_edd.validate():
        return redirect(url_for("tracking_edd.review_from_kyc_edd_download", case_id=case_id))

    if step_seven_form.step7_send_btn.data and step_seven_form.validate():
        now_time = datetime.now()
        
        # Save uploaded file
        review_from_fid = step_seven_form.kyc_refresh_review.data
        timestamp = now_time.strftime("%Y-%m-%d_%H-%M-%S")
        filename_review_from_fid = timestamp + "_" + secure_filename(review_from_fid.filename)
        
        saved_file_dir = os.path.join(REVIEW_FROM_FID_CLIENT_DIR, str(case_id))
        if not os.path.exists(saved_file_dir):
            os.makedirs(saved_file_dir)
        review_from_fid.save(os.path.join(saved_file_dir, filename_review_from_fid))
        
        # Update data in database
        tracking_case, case_info = tracking_case_info(case_id)
        
        update_tracking_record = f'''
            update EDD_tracking SET Step7_Round = ?, Step7_Latest_Time = ?, Step7_Latest_Comment = ?, Step7_Analyst = ?, Tracking_Status = ? where Case_ID = {case_id}'''
        execute_sql(
            update_tracking_record, 
            (tracking_case["Step7_Round"]+1, now_time, step_seven_form.step7_comment.data, show_name, 6))
        
        insert_step7_record = '''
            INSERT INTO Track_step7 (Tracking_ID, Step7_Round, Step7_Analyst, Step7_Time, Step7_Comment) 
            VALUES (?, ?, ?, ?, ?) '''
        execute_sql(
            insert_step7_record, 
            (tracking_case["Tracking_ID"], tracking_case["Step7_Round"]+1, show_name, now_time, step_six_form.step6_comment.data))
        
        # Send email to QC Analyst
        kyc_qc_analyst_user_name = get_name(show_name=tracking_case["QC_Analyst"])
        kyc_qc_analyst_email = select_sql(
            "SELECT Email from User_Info where Name = (?)",
            [kyc_qc_analyst_user_name],
            db_path=USER_ADMIN_PATH)["Email"]
        
        message = send_step7_email(
            tracking_case["QC_Analyst"], case_info, user_name=show_name, user_email=[user_email, kyc_qc_analyst_email], 
            attachment_path=os.path.join(saved_file_dir, filename_review_from_fid))
        
        flash(f"Step7 Finish! {message}! Back to Step 6!", "success")
        return redirect(url_for("tracking_edd.step_5_6_7_page", case_id=case_id))

    if download_review_from_fid_client.download_file2_btn.data and download_review_from_fid_client.validate():
        return redirect(url_for("tracking_edd.review_from_fid_client_download", case_id=case_id))
    
    if step_eight_form.finish_btn.data and step_eight_form.validate():
        now_time = datetime.now()
        
        update_tracking_record = f'''
            update EDD_tracking SET Step8_Analyst = ?, Step8_Date = ?, Tracking_Status = ? where Case_ID = {case_id}'''
        execute_sql(update_tracking_record, (show_name, now_time.date(), 9))
        flash("Step8 Finish!", "success")
        return redirect(url_for("tracking_edd.step_5_6_7_page", case_id=case_id))
    
    tracking_case, case_info = tracking_case_info(case_id)
    if not tracking_case:
        for field in step_six_form:
            field.render_kw = {"disabled": "disabled"}
        for field in step_seven_form:
            field.render_kw = {"disabled": "disabled"}
        for field in step_eight_form:
            field.render_kw = {"disabled": "disabled"}
        download_review_from_kyc_edd.download_file1_btn.render_kw = {"disabled": "disabled"}
        download_review_from_fid_client.download_file2_btn.render_kw = {"disabled": "disabled"}
    else:
        tracking_status = tracking_case["Tracking_Status"]
        if tracking_status < 6:
            for field in step_six_form:
                field.render_kw = {"disabled": "disabled"}
            for field in step_seven_form:
                field.render_kw = {"disabled": "disabled"}
            for field in step_eight_form:
                field.render_kw = {"disabled": "disabled"}
            download_review_from_kyc_edd.download_file1_btn.render_kw = {"disabled": "disabled"}
            download_review_from_fid_client.download_file2_btn.render_kw = {"disabled": "disabled"}
                
        elif tracking_status == 6:
            for field in step_seven_form:
                field.render_kw = {"disabled": "disabled"}
        
        elif tracking_status == 7:
            for field in step_six_form:
                field.render_kw = {"disabled": "disabled"}
                
        elif tracking_status > 7:
            for field in step_six_form:
                field.render_kw = {"disabled": "disabled"}
            for field in step_seven_form:
                field.render_kw = {"disabled": "disabled"}
            for field in step_eight_form:
                field.render_kw = {"disabled": "disabled"}
            
        if not tracking_case["Step6_Round"] or (tracking_case["Step6_Round"] == 0):
            download_review_from_kyc_edd.download_file1_btn.render_kw = {"disabled": "disabled"}
            step_eight_form.finish_btn.render_kw = {"disabled": "disabled"}
        if not tracking_case["Step7_Round"] or (tracking_case["Step7_Round"] == 0):
            download_review_from_fid_client.download_file2_btn.render_kw = {"disabled": "disabled"}
            step_eight_form.finish_btn.render_kw = {"disabled": "disabled"}
        
        step_six_form.step6_round.default = tracking_case["Step6_Round"]
        step_six_form.step6_latest_time.default = strptime_date(
            tracking_case["Step6_Latest_Time"], "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%d %H:%M:%S") if tracking_case["Step6_Latest_Time"] else ""
        step_six_form.fid_client.default = tracking_case["FID_Client"]
        step_six_form.step6_comment.default = tracking_case["Step6_Latest_Comment"]
        step_six_form.process()
        
        step_seven_form.step7_round.default = tracking_case["Step7_Round"]
        step_seven_form.step7_latest_time.default = strptime_date(
            tracking_case["Step7_Latest_Time"], "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%d %H:%M:%S") if tracking_case["Step7_Latest_Time"] else ""
        step_seven_form.qc_analyst.default = tracking_case["QC_Analyst"]
        step_seven_form.step7_comment.default = tracking_case["Step7_Latest_Comment"]
        step_seven_form.process()
        
        step_eight_form.finsih_date.default = strptime_date(tracking_case["Step8_Date"])
        step_eight_form.finish_analyst.default = tracking_case["Step8_Analyst"]
        step_eight_form.process()
    
    return render_template(
        'et_5_6_7.html', case_id=case_id, case_info=case_info,
        step_six_form=step_six_form, step_seven_form=step_seven_form, step_eight_form=step_eight_form,
        download_review_from_kyc_edd=download_review_from_kyc_edd, download_review_from_fid_client=download_review_from_fid_client)


@tracking_edd.route('/step_5_6_7/review_from_kyc_edd/<int:case_id>', methods=['GET'])
@login_required
def review_from_kyc_edd_download(case_id):
    saved_file_dir = os.path.join(REVIEW_FROM_KYC_EDD_DIR, str(case_id))   
    name_list = os.listdir(saved_file_dir)
    full_list = [os.path.join(saved_file_dir,i) for i in name_list]
    full_list = sorted(full_list, key=os.path.getmtime, reverse=True)
    return send_file(full_list[0], as_attachment=True)


@tracking_edd.route('/step_5_6_7/review_from_fid_client/<int:case_id>', methods=['GET'])
@login_required
def review_from_fid_client_download(case_id):
    saved_file_dir = os.path.join(REVIEW_FROM_FID_CLIENT_DIR, str(case_id))   
    name_list = os.listdir(saved_file_dir)
    full_list = [os.path.join(saved_file_dir,i) for i in name_list]
    full_list = sorted(full_list, key=os.path.getmtime, reverse=True)
    return send_file(full_list[0], as_attachment=True)

    
@tracking_edd.route('/step_8_9_10/<int:case_id>', methods=['GET', 'POST'])
@login_required
def step_8_9_10_page(case_id):
    user_name = get_user_info(current_user.get_id()).name
    show_name = get_name(user_name=user_name)
    user_email = get_user_info(current_user.get_id()).email
    
    step_nine_form = StepNine()
    step_ten_form = StepTen()
    download_report_form = DownloadFile1()
    download_report_form.download_file1_btn.label.text = "Download KYC EDD Review"
    download_approved_review_form = DownloadFile2()
    download_approved_review_form.download_file2_btn.label.text = "Download Approved Review"
    
    if step_nine_form.send_btn.data and step_nine_form.validate():
        now_time = datetime.now()
        
        # Save uploaded file
        review_for_approval = step_nine_form.review_for_approval.data
        timestamp = now_time.strftime("%Y-%m-%d_%H-%M-%S")
        filename_review_for_approval = timestamp + "_" + secure_filename(review_for_approval.filename)
        
        saved_file_dir = os.path.join(REVIEW_FOR_APPROVAL_DIR, str(case_id))
        if not os.path.exists(saved_file_dir):
            os.makedirs(saved_file_dir)
        review_for_approval.save(os.path.join(saved_file_dir, filename_review_for_approval))
        
        # Update data in database
        tracking_case, case_info = tracking_case_info(case_id)
        
        update_tracking_record = f'''
            update EDD_tracking SET Step9_Analyst = ?, Step9_Round = ?, New_Risk_Rating = ?, EDD_Head_Approver = ?, 
            Step9_Latest_Time = ?, Step9_Latest_Comment = ?, Tracking_Status = ? where Case_ID = {case_id}'''
        execute_sql(
            update_tracking_record, 
            (show_name, tracking_case["Step9_Round"]+1, step_nine_form.new_risk_rating.data, step_nine_form.edd_head_approver.data, 
             now_time, step_nine_form.step9_comment.data, 10))
        
        insert_step9_record = '''
            INSERT INTO Track_step9 (Tracking_ID, Step9_Round, Step9_Analyst, Step9_Time, Step9_Comment) 
            VALUES (?, ?, ?, ?, ?) '''
        execute_sql(
            insert_step9_record, 
            (tracking_case["Tracking_ID"], tracking_case["Step9_Round"]+1, show_name, now_time, step_nine_form.step9_comment.data))
        
        # Send email to EDD Head
        edd_head_approver_user_name = get_name(show_name=tracking_case["EDD_Head_Approver"])
        edd_head_approver_email = select_sql(
            "SELECT Email from User_Info where Name = (?)",
            [edd_head_approver_user_name],
            db_path=USER_ADMIN_PATH)["Email"]
        print(edd_head_approver_email)
        
        message = send_step9_email(
            tracking_case["EDD_Head_Approver"], case_info, user_name=show_name, user_email=[user_email, edd_head_approver_email], 
            attachment_path=os.path.join(saved_file_dir, filename_review_for_approval))
        
        flash(f"Step9 Finish! {message}", "success")
        return redirect(url_for("tracking_edd.step_8_9_10_page", case_id=case_id))
    
    if download_report_form.download_file1_btn.data and download_report_form.validate():
        return redirect(url_for("tracking_edd.review_for_approval_download", case_id=case_id))
    
    if step_ten_form.send_btn.data and step_ten_form.validate():
        now_time = datetime.now()
        
        if (step_ten_form.action.data == "Approve") or (step_ten_form.action.data == "Pending"):
            if not step_ten_form.approved_review.data:
                flash("Please attach approved review!", "danger")
            else:
                # Save uploaded file
                review_approved = step_ten_form.approved_review.data
                timestamp = now_time.strftime("%Y-%m-%d_%H-%M-%S")
                filename_review_approved = timestamp + "_" + secure_filename(review_approved.filename)
                
                saved_file_dir = os.path.join(REVIEW_APPROVED_DIR, str(case_id))
                if not os.path.exists(saved_file_dir):
                    os.makedirs(saved_file_dir)
                review_approved.save(os.path.join(saved_file_dir, filename_review_approved))
            
                # Update data in database
                tracking_case, case_info = tracking_case_info(case_id)
                tracking_status = 9 if step_ten_form.action.data == "Pending" else 11
                update_tracking_record = f'''
                    update EDD_tracking SET Step10_Analyst = ?, Step10_Round = ?, Approver_Action = ?, Step10_Latest_Time = ?, Step10_Latest_Comment = ?, Tracking_Status = ? where Case_ID = {case_id}'''
                execute_sql(
                    update_tracking_record, 
                    (show_name, tracking_case["Step10_Round"]+1, step_ten_form.action.data, now_time, step_ten_form.step10_comment.data, tracking_status))
                
                insert_step10_record = '''
                    INSERT INTO Track_step10 (Tracking_ID, Step10_Round, Step10_Analyst, Step10_Time, Step10_Comment) 
                    VALUES (?, ?, ?, ?, ?) '''
                execute_sql(
                    insert_step10_record, 
                    (tracking_case["Tracking_ID"], tracking_case["Step10_Round"]+1, show_name, now_time, step_ten_form.step10_comment.data))
                
                message = send_step10_email(
                    case_info, user_name=show_name, user_email=user_email, 
                    attachment_path=os.path.join(saved_file_dir, filename_review_approved), action="Approve")
                flash(f"{message}! Review {step_ten_form.action.data}!", "success")
        
        elif step_ten_form.action.data == "Reject":
            tracking_case, case_info = tracking_case_info(case_id)
            update_tracking_record = f'''
                update EDD_tracking SET Step10_Analyst = ?, Step10_Round = ?, Approver_Action = ?, Step10_Latest_Time = ?, Step10_Latest_Comment = ?, Tracking_Status = ? where Case_ID = {case_id}'''
            execute_sql(
                update_tracking_record, 
                (show_name, tracking_case["Step10_Round"]+1, step_ten_form.action.data, now_time, 9))
            
            insert_step10_record = '''
                INSERT INTO Track_step10 (Tracking_ID, Step10_Round, Step10_Approver, Step10_Time, Step10_Comment) 
                VALUES (?, ?, ?, ?, ?) '''
            execute_sql(
                insert_step10_record, 
                (tracking_case["Tracking_ID"], tracking_case["Step10_Round"]+1, show_name, now_time, step_ten_form.step10_comment.data))
            
            message = send_step10_email(
                case_info, user_name=show_name, user_email=user_email, 
                attachment_path=os.path.join(saved_file_dir, filename_review_approved), action="Reject")
            flash(f"{message}! Finish Step10! Finish current case!", "success")
        
        return redirect(url_for("tracking_edd.step_8_9_10_page", case_id=case_id))
    
    if download_approved_review_form.download_file2_btn.data and download_approved_review_form.validate():
        return redirect(url_for("tracking_edd.review_approved_download", case_id=case_id))
    
    tracking_case, case_info = tracking_case_info(case_id)
    if not tracking_case:
        for field in step_nine_form:
            field.render_kw = {"disabled": "disabled"}
        for field in step_ten_form:
            field.render_kw = {"disabled": "disabled"}
        download_report_form.download_file1_btn.render_kw = {"disabled": "disabled"}
        download_approved_review_form.download_file2_btn.render_kw = {"disabled": "disabled"}
    else:
        tracking_status = tracking_case["Tracking_Status"]
        if tracking_status < 9:
            for field in step_nine_form:
                field.render_kw = {"disabled": "disabled"}
            for field in step_ten_form:
                field.render_kw = {"disabled": "disabled"}
            download_report_form.download_file1_btn.render_kw = {"disabled": "disabled"}
            download_approved_review_form.download_file2_btn.render_kw = {"disabled": "disabled"}
        elif tracking_status == 9:
            for field in step_ten_form:
                field.render_kw = {"disabled": "disabled"}
            download_report_form.download_file1_btn.render_kw = {"disabled": "disabled"}
            download_approved_review_form.download_file2_btn.render_kw = {"disabled": "disabled"}
        elif tracking_status == 10:
            for field in step_nine_form:
                field.render_kw = {"disabled": "disabled"}
            download_approved_review_form.download_file2_btn.render_kw = {"disabled": "disabled"}
        else:
            for field in step_nine_form:
                field.render_kw = {"disabled": "disabled"}
            for field in step_ten_form:
                field.render_kw = {"disabled": "disabled"}
        
        if tracking_case["Approver_Action"] == "Reject":
            download_approved_review_form.download_file2_btn.render_kw = {"disabled": "disabled"}
        
        if not tracking_case["Step9_Round"] or (tracking_case["Step9_Round"] == 0):
            download_report_form.download_file1_btn.render_kw = {"disabled": "disabled"}
        if not tracking_case["Step10_Round"] or (tracking_case["Step10_Round"] == 0):
            download_approved_review_form.download_file2_btn.render_kw = {"disabled": "disabled"}
        
        step_nine_form.step9_latest_time.default = strptime_date(
            tracking_case["Step9_Latest_Time"], "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%d %H:%M:%S") if tracking_case["Step9_Latest_Time"] else ""
        step_nine_form.step9_round.default = tracking_case["Step9_Round"]
        step_nine_form.qc_analyst.default = tracking_case["QC_Analyst"]
        step_nine_form.new_risk_rating.default = tracking_case["New_Risk_Rating"]
        step_nine_form.edd_head_approver.default = tracking_case["EDD_Head_Approver"]
        step_nine_form.step9_comment.default = tracking_case["Step9_Latest_Comment"]
        step_nine_form.process()
        
        step_ten_form.step10_latest_time.default = strptime_date(
            tracking_case["Step10_Latest_Time"], "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%d %H:%M:%S") if tracking_case["Step10_Latest_Time"] else ""
        step_ten_form.step10_round.default = tracking_case["Step10_Round"]
        step_ten_form.approver.default = tracking_case["Step10_Analyst"]
        step_ten_form.action.default = tracking_case["Approver_Action"]
        step_ten_form.step10_comment.default = tracking_case["Step10_Latest_Comment"]
        step_ten_form.process()
    
    return render_template(
        'et_8_9_10.html', case_id=case_id, case_info=case_info,
        step_nine_form=step_nine_form, step_ten_form=step_ten_form, 
        download_report_form=download_report_form, download_approved_review_form=download_approved_review_form)
    
    
@tracking_edd.route('/step_8_9_10/review_for_approval/<int:case_id>', methods=['GET'])
@login_required
def review_for_approval_download(case_id):
    saved_file_dir = os.path.join(REVIEW_FOR_APPROVAL_DIR, str(case_id))   
    name_list = os.listdir(saved_file_dir)
    full_list = [os.path.join(saved_file_dir,i) for i in name_list]
    full_list = sorted(full_list, key=os.path.getmtime, reverse=True)
    return send_file(full_list[0], as_attachment=True)


@tracking_edd.route('/step_8_9_10/review_approved/<int:case_id>', methods=['GET'])
@login_required
def review_approved_download(case_id):
    saved_file_dir = os.path.join(REVIEW_APPROVED_DIR, str(case_id))   
    name_list = os.listdir(saved_file_dir)
    full_list = [os.path.join(saved_file_dir,i) for i in name_list]
    full_list = sorted(full_list, key=os.path.getmtime, reverse=True)
    return send_file(full_list[0], as_attachment=True)
