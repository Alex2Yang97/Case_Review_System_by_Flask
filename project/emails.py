import os
import pickle
import pythoncom
import win32com
import win32com.client as win32
from werkzeug.security import generate_password_hash, check_password_hash

from .config import (
    ADMIN_EMAIL, TEST, SQL_TYPE, DATA_QC_TO_EMAILS, DATA_QC_CC_EMAILS, RESEARCH_QC_CC_EMAILS, 
    REPORT_TO_EMAILS, REPORT_CC_EMAILS, APPROVE_TO_EMAILS, APPROVE_CC_EMAILS,
    STEP1_TO_EMAILS, STEP1_CC_EMAILS, STEP2_TO_EMAILS, STEP2_CC_EMAILS, STEP3_TO_EMAILS, STEP3_CC_EMAILS,
    STEP4_TO_EMAILS, STEP4_CC_EMAILS, STEP5_TO_EMAILS, STEP5_CC_EMAILS, STEP6_TO_EMAILS, STEP6_CC_EMAILS,
    STEP7_TO_EMAILS, STEP7_CC_EMAILS, STEP9_TO_EMAILS, STEP9_CC_EMAILS, STEP10_TO_EMAILS, STEP10_CC_EMAILS)
from .metrics import get_month_year
from .utils import strptime_date




def sign_up_email(user_info):
    
    file_path = os.path.abspath(".")
    pfile_name = os.path.join(file_path, f"{user_info['username']}.p")
    with open(pfile_name, 'wb') as fp:
        pickle.dump(user_info, fp, protocol=pickle.HIGHEST_PROTOCOL)
    
    outlook = win32.Dispatch('outlook.application')
    mail = outlook.CreateItem(0)

    header = ("<thead><tr>"
              "<th>User Name</th>"
              "<th>User Email</th>"
              "<th>User IP</th>"
              "</tr></thead>")
    Data = ("<tbody><tr>"
            f"<td>{user_info['username']}</td>"
            f"<td>{user_info['user_email']}</td>"
            f"<td>{user_info['ip_address']}</td>"
            "</tr></tbody>")
    table = header + Data

    cssStyle = "<style>th{font-weight:bold;color:white;background-color:coral}th, td {border: 1px solid black;}"
    txtStart = ("Hi DA Team,"
                "<br><br>"
                "Please review my information and create an account for me. Thank you "
                "<br><br>")
    HTMLstart = "<html>" + cssStyle + "<body>" + txtStart + "<table>"
    HTMLend = f"</table><br><br>Best,<br>{user_info['username']}<br></body></html>"

    mail.To = ADMIN_EMAIL
    mail.Subject = f"Sign Up for EDD Tracker"
    mail.HTMLBody = HTMLstart + table + HTMLend
    mail.Attachments.Add(pfile_name)
    mail.Send()
    
    os.remove(pfile_name)
    
    return "Sign Up Email Sent"


def verification_email(code, user_email):
    # 非常奇怪的bug，在某一次测试后，第一句突然就会出现报错，而且报错只在使用flask的时候才出现，单独测试这个函数是可以正常发送邮件的
    # 改成第二句就正常了
    # outlook = win32.Dispatch('outlook.application')
    outlook = win32com.client.Dispatch("outlook.Application", pythoncom.CoInitialize())
    mail = outlook.CreateItem(0)

    txtStart = ("Hi,"
                "<br><br>"
                f"Please use this code: <strong>{code}</strong> to create an account!"
                "<br><br>")
    HTMLstart = "<html>" + "<body>" + txtStart + "<table>"
    HTMLend = f"</table><br><br>Best,<br>DA Team<br></body></html>"

    mail.To = user_email
    mail.Subject = f"Sign Up for EDD Tracker"
    mail.HTMLBody = HTMLstart + HTMLend
    mail.Send()
    
    return "Verification Email Sent"


def send_data_email(data_info, user_name, user_email, test=TEST, sql_type=SQL_TYPE):
    # outlook = win32.Dispatch('outlook.application')
    outlook = win32com.client.Dispatch("outlook.Application", pythoncom.CoInitialize())
    mail = outlook.CreateItem(0)

    title = f'''Data QC Notification_{data_info["Customer_ID"]}_{data_info["Customer_Name"]} ({data_info["Scheduled_Due_Date"]})'''
    Data = ("<tbody><tr>"
            f"<td>{data_info['Customer_ID']}</td>"
            f"<td>{data_info['Customer_Name']}</td>"
            f"<td>{data_info['Scheduled_Due_Date']}</td>"
            "</tr></tbody>")
        
    header = ("<thead><tr>"
              "<th>Customer ID</th>"
              "<th>Customer Name</th>"
              "<th>Due Date</th>"
              "</tr></thead>")
    table = header + Data

    cssStyle = "<style>th{font-weight:bold;color:white;background-color:coral}th, td {border: 1px solid black;}"
    txtStart = ("Hi All,"
                "<br><br>"
                "Data for this case is complete and ready for QC. Thank you "
                "<br><br>")
    HTMLstart = "<html>" + cssStyle + "<body>" + txtStart + "<table>"
    
    HTMLend = (f"</table><br><br>This email was sent by <b>{user_name} ({user_email[0]})</b> on EDD Tracker."
               "<br><br>Best,<br>EDD Tracker<br></body></html>")

    if test:
        mail.To = user_email[0]
        mail.CC = user_email[0]
    else:
        mail.To = user_email[1]
        mail.CC = user_email[0]
        
    mail.Subject = title
    mail.HTMLBody = HTMLstart + table + HTMLend
    mail.Send()
    
    return "Data Email Sent"
    
    
def send_data_qc_email(data_info, user_name, user_email, test=TEST, sql_type=SQL_TYPE):
    # outlook = win32.Dispatch('outlook.application')
    outlook = win32com.client.Dispatch("outlook.Application", pythoncom.CoInitialize())
    mail = outlook.CreateItem(0)

    if data_info["Case_Type"] != "RMB Review":
        
        title = f"Case Assignment_{data_info['Customer_ID']}_{data_info['Customer_Name']} ({data_info['Scheduled_Due_Date']})"
        header = ("<thead><tr>"
                "<th>Customer ID</th>"
                "<th>Customer Name</th>"
                "<th>Risk Rating</th>"
                "<th>Volume</th>"
                "<th>Value</th>"
                "<th>EDD Analyst</th>"
                "</tr></thead>")
        Data = ("<tbody><tr>"
                f"<td>{data_info['Customer_ID']}</td>"
                f"<td>{data_info['Customer_Name']}</td>"
                f"<td>{data_info['Risk_Rating']}</td>"
                f"<td>{data_info['Volume']}</td>"
                f"<td>{data_info['Value']}</td>"
                f"<td>{data_info['Report_Analyst']}</td>"
                "</tr></tbody>")
        table = header + Data
        
    else: # data_info.Case_Type == "RMB Review"
        date_str = get_month_year(
            strptime_date(data_info['Transaction_Start_Date']).month, 
            strptime_date(data_info['Transaction_Start_Date']).year, 
            str_type="ad")

        title = f"RMB Case Assignment_{data_info['Customer_ID']}_{data_info['Customer_Name']} ({date_str})"
        header = (
            "<thead><tr>"
            "<th>Data Review Period</th>"
            "<th>Customer ID</th>"
            "<th>Customer Name</th>"
            "<th>Risk Rating</th>"
            "<th>Volume</th>"
            "<th>Value</th>"
            "<th>Category</th>"
            "<th>Type</th>"
            "<th>EDD Analyst</th>"
            "</tr></thead>")
        Data = (
            "<tbody><tr>"
            f"<td>{date_str}</td>"
            f"<td>{data_info['Customer_ID']}</td>"
            f"<td>{data_info['Customer_Name']}</td>"
            f"<td>{data_info['Risk_Rating']}</td>"
            f"<td>{data_info['Volume']}</td>"
            f"<td>{data_info['Value']}</td>"
            f"<td>{data_info['Category']}</td>"
            f"<td>{data_info['Type']}</td>"
            f"<td>{data_info['Report_Analyst']}</td>"
            "</tr></tbody>")
        table = header + Data

    cssStyle = "<style>th{font-weight:bold;color:white;background-color:coral}th, td {border: 1px solid black;}"
    txtStart = ("Hi All,"
                "<br><br>"
                f"The following case is ready. <br><br>"
                "The research team and assigned EDD analysts please start on them as soon as possible and also update the tracker.<br>"
                "In addition, when the research team have finished the work for those customers, "
                "Please kindly [reply all] to this email so the report analysts can start on the Top 10 Bene/Orig analysis. Thanks.<br><br>")
    HTMLstart = "<html>" + cssStyle + "<body>" + txtStart + "<table>"
    
    HTMLend = (f"</table><br><br>This email was sent by <b>{user_name} ({user_email})</b> on EDD Tracker."
               "<br><br>Best,<br>EDD Tracker<br></body></html>")

    if test:
        mail.To = user_email
        mail.CC = user_email
    else:
        mail.To = DATA_QC_TO_EMAILS + "; " + user_email
        mail.CC = DATA_QC_CC_EMAILS
        
    mail.Subject = title
    mail.HTMLBody = HTMLstart + table + HTMLend
    mail.Send()
    
    return "Data Email Sent"    


def send_research_email(data_info, user_name, user_email, test=TEST, sql_type=SQL_TYPE):
    # outlook = win32.Dispatch('outlook.application')
    outlook = win32com.client.Dispatch("outlook.Application", pythoncom.CoInitialize())
    mail = outlook.CreateItem(0)

    title = f"Research QC Notification_{data_info['Customer_ID']}_{data_info['Customer_Name']} ({data_info['Scheduled_Due_Date']})"
    Data = f'''<tbody><tr>
            <td>{data_info['Customer_ID']}</td>
            <td>{data_info['Customer_Name']}</td>
            <td>{data_info['Scheduled_Due_Date']}</td>
            </tr></tbody>'''
                
    header = ("<thead><tr>"
                "<th>Customer ID</th>"
                "<th>Customer Name</th>"
                "<th>Due Date</th>"
                "</tr></thead>")
    table = header + Data

    cssStyle = "<style>th{font-weight:bold;color:white;background-color:coral}th, td {border: 1px solid black;}"
    txtStart = ("Hi All,"
                "<br><br>"
                "Research for this case is complete and ready for QC. Thank you "
                "<br><br>")
    HTMLstart = "<html>" + cssStyle + "<body>" + txtStart + "<table>"
    
    HTMLend = (f"</table><br><br>This email was sent by <b>{user_name} ({user_email[0]})</b> on EDD Tracker."
               "<br><br>Best,<br>EDD Tracker<br></body></html>")

    if test:
        mail.To = user_email[0]
        mail.CC = user_email[0]
    else:
        mail.To = user_email[1]
        mail.CC = user_email[0]
    
    mail.Subject = title
    mail.HTMLBody = HTMLstart + table + HTMLend
    mail.Send()
    
    return "Research Email Sent"


def send_research_qc_email(data_info, user_name, user_email, test=TEST, sql_type=SQL_TYPE):
    # outlook = win32.Dispatch('outlook.application')
    outlook = win32com.client.Dispatch("outlook.Application", pythoncom.CoInitialize())
    mail = outlook.CreateItem(0)
    
    title = f"Research QC Complete Notification_{data_info['Customer_ID']}_{data_info['Customer_Name']} ({data_info['Scheduled_Due_Date']})"
    Data = ("<tbody><tr>"
            f"<td>{data_info['Customer_ID']}</td>"
            f"<td>{data_info['Customer_Name']}</td>"
            f"<td>{data_info['Scheduled_Due_Date']}</td>"
            "</tr></tbody>")
        
    header = ("<thead><tr>"
                "<th>Customer ID</th>"
                "<th>Customer Name</th>"
                "<th>Due Date</th>"
                "</tr></thead>")
    table = header + Data

    cssStyle = "<style>th{font-weight:bold;color:white;background-color:coral}th, td {border: 1px solid black;}"
    txtStart = ("Hi All,"
                "<br><br>"
                "Research QC for this case is complete. Thank you "
                "<br><br>")
    HTMLstart = "<html>" + cssStyle + "<body>" + txtStart + "<table>"
    
    HTMLend = (f"</table><br><br>This email was sent by <b>{user_name} ({user_email})</b> on EDD Tracker."
               "<br><br>Best,<br>EDD Tracker<br></body></html>")

    if test:
        mail.To = user_email
        mail.CC = user_email
    else:
        mail.To = user_email
        mail.CC = RESEARCH_QC_CC_EMAILS
        
    mail.Subject = title
    mail.HTMLBody = HTMLstart + table + HTMLend
    mail.Send()
    
    return "Research QC Email Sent"   


def send_report_email(data_info, user_name, user_email, test=TEST, sql_type=SQL_TYPE):
    # outlook = win32.Dispatch('outlook.application')
    outlook = win32com.client.Dispatch("outlook.Application", pythoncom.CoInitialize())
    mail = outlook.CreateItem(0)

    title = f"Report QC Notification_{data_info['Customer_ID']}_{data_info['Customer_Name']} ({data_info['Scheduled_Due_Date']})"
    Data = f'''<tbody><tr>
            <td>{data_info['Customer_ID']}</td>
            <td>{data_info['Customer_Name']}</td>
            <td>{data_info['Scheduled_Due_Date']}</td>
            </tr></tbody>'''
        
    header = ("<thead><tr>"
                "<th>Customer ID</th>"
                "<th>Customer Name</th>"
                "<th>Due Date</th>"
                "</tr></thead>")
    table = header + Data

    cssStyle = "<style>th{font-weight:bold;color:white;background-color:coral}th, td {border: 1px solid black;}"
    txtStart = ("Hi All,"
                "<br><br>"
                "Report for this case is complete and ready for QC. Thank you "
                "<br><br>")
    HTMLstart = "<html>" + cssStyle + "<body>" + txtStart + "<table>"
    
    HTMLend = (f"</table><br><br>This email was sent by <b>{user_name} ({user_email})</b> on EDD Tracker."
               "<br><br>Best,<br>EDD Tracker<br></body></html>")

    if test:
        mail.To = user_email
        mail.CC = user_email
    else:
        mail.To = REPORT_TO_EMAILS + "; " + user_email
        mail.CC = REPORT_CC_EMAILS
        
    mail.Subject = title
    mail.HTMLBody = HTMLstart + table + HTMLend
    mail.Send()
    
    return "Report Email Sent"


def send_approval_email(data_info, user_name, user_email, test=TEST, sql_type=SQL_TYPE):
    # outlook = win32.Dispatch('outlook.application')
    outlook = win32com.client.Dispatch("outlook.Application", pythoncom.CoInitialize())
    mail = outlook.CreateItem(0)

    title = f'''Report Pending Approval Notification_{data_info['Customer_ID']}_{data_info['Customer_Name']} ({data_info['Scheduled_Due_Date']})'''
    Data = f'''<tbody><tr>
            <td>{data_info['Customer_ID']}</td>
            <td>{data_info['Customer_Name']}</td>
            <td>{data_info['Scheduled_Due_Date']}</td>
            </tr></tbody>'''
        
    header = ("<thead><tr>"
                "<th>Customer ID</th>"
                "<th>Customer Name</th>"
                "<th>Due Date</th>"
                "</tr></thead>")
    table = header + Data

    cssStyle = "<style>th{font-weight:bold;color:white;background-color:coral}th, td {border: 1px solid black;}"
    txtStart = ("Hi All,"
                "<br><br>"
                "Report QC for this case is complete and is now pending approval. Thank you "
                "<br><br>")
    HTMLstart = "<html>" + cssStyle + "<body>" + txtStart + "<table>"
    
    HTMLend = (f"</table><br><br>This email was sent by <b>{user_name} ({user_email})</b> on EDD Tracker."
               "<br><br>Best,<br>EDD Tracker<br></body></html>")

    if test:
        mail.To = user_email
        mail.CC = user_email
    else:
        mail.To = APPROVE_TO_EMAILS + "; " + user_email
        mail.CC = APPROVE_CC_EMAILS
        
    mail.Subject = title
    mail.HTMLBody = HTMLstart + table + HTMLend
    mail.Send()
    
    return "Report QC Email Sent"


def send_step1_email(data_info, user_name, user_email, attachment_path, test=TEST, sql_type=SQL_TYPE):
    # outlook = win32.Dispatch('outlook.application')
    outlook = win32com.client.Dispatch("outlook.Application", pythoncom.CoInitialize())
    mail = outlook.CreateItem(0)

    title = f"{data_info['Customer_ID']}_{data_info['Customer_Name']}_2023 RFI"

    txtStart = (
        "Hi FID Team,"
        "<br><br>"
        "Please see the attached RFI regarding the case mentioned above."
        "<br><br>"
        "Please note that if the FLU / Customer is not able to complete the RFI response package within the 60 days from the RFI issue date, "
        "the FLU shall promptly reply to the LCD KYC Analyst and/or Team Lead to provide high-level updates and an estimated target timeline of obtaining the complete RFI response."
        "<br><br>"
        "Please let us know if you have any questions."
        "<br><br>"
        "Thank you!"
        )
    HTMLstart = "<html>" + "<body>" + txtStart
    
    HTMLend = (
        "<br><br>"
        "<br><br>"
        f"This email was sent by <b>{user_name} ({user_email})</b> on EDD Tracker."
        "<br><br>Best,<br>EDD Tracker<br></body></html>"
        )

    if test:
        mail.To = user_email
        mail.CC = user_email
    else:
        mail.To = STEP1_TO_EMAILS + "; " + user_email
        mail.CC = STEP1_CC_EMAILS
        
    mail.Subject = title
    mail.HTMLBody = HTMLstart + HTMLend
    mail.Attachments.Add(attachment_path)
    mail.Send()
    return "Step1 email sent!"


def send_step2_email(data_info, user_name, user_email, test=TEST):
    # outlook = win32.Dispatch('outlook.application')
    outlook = win32com.client.Dispatch("outlook.Application", pythoncom.CoInitialize())
    mail = outlook.CreateItem(0)

    title = f"Case Received: {data_info['Customer_ID']}_{data_info['Customer_Name']}_2023 RFI"

    txtStart = (
        f"Hi ALL,"
        "<br><br>"
        "FID completed the RFI for Beijing Azalea Management Consulting Corporation. The required documents had been captured in both FID client's folder and Fenergo."
        "<br><br>"
        "Please kindly review and let us know if you have any questions."
        "<br><br>"
        "Thank you!"
        )
    HTMLstart = "<html>" + "<body>" + txtStart
    
    HTMLend = (
        "<br><br>"
        f"This email was sent by <b>{user_name} ({user_email})</b> on EDD Tracker."
        "<br><br>Best,<br>EDD Tracker<br></body></html>"
        )

    if test:
        mail.To = user_email
        mail.CC = user_email
    else:
        mail.To = STEP2_TO_EMAILS
        mail.CC = STEP2_CC_EMAILS + "; " + user_email
        
    mail.Subject = title
    mail.HTMLBody = HTMLstart + HTMLend
    mail.Send()
    return "Step2 email sent!"


def send_step3_email(qc_analyst, data_info, user_name, user_email, attachment_path_lst, test=TEST):
    # outlook = win32.Dispatch('outlook.application')
    outlook = win32com.client.Dispatch("outlook.Application", pythoncom.CoInitialize())
    mail = outlook.CreateItem(0)

    title = f"{data_info['Customer_ID']}_{data_info['Customer_Name']}_2023 Periodic KYC Refresh Review"

    txtStart = (
        f"Hi {qc_analyst},"
        "<br><br>"
        "The below referenced case is ready for your QC review."
        "<br><br>"
        "Thank you!"
        )
    HTMLstart = "<html>" + "<body>" + txtStart
    
    HTMLend = (
        "<br><br>"
        f"This email was sent by <b>{user_name} ({user_email[0]})</b> on EDD Tracker."
        "<br><br>Best,<br>EDD Tracker<br></body></html>"
        )

    if test:
        mail.To = user_email[0]
        mail.CC = user_email[0]
    else:
        mail.To = STEP5_TO_EMAILS + "; " + user_email[1]
        mail.CC = STEP5_CC_EMAILS + "; " + user_email[0]
        
    mail.Subject = title
    mail.HTMLBody = HTMLstart + HTMLend
    for att in attachment_path_lst:
        mail.Attachments.Add(att)
    mail.Send()
    return "Step3 email sent!"


def send_step4_email(fid_bsa_officer, data_info, user_name, user_email, attachment_path, test=TEST):
    # outlook = win32.Dispatch('outlook.application')
    outlook = win32com.client.Dispatch("outlook.Application", pythoncom.CoInitialize())
    mail = outlook.CreateItem(0)

    title = f"{data_info['Customer_ID']}_{data_info['Customer_Name']}_2023 Periodic KYC Refresh Review"

    txtStart = (
        f"Hi {fid_bsa_officer},"
        "<br><br>"
        f"Please see attached the QCed CRR for {data_info['Customer_ID']}_{data_info['Customer_Name']} for your review and approval. "
        "Customer risk rating has changed from ??? to ??? during current review period. "
        "Please note full EDD Report is temporarily available in EDD Tracker for reference. "
        "All other information can be referred in the shared folder as well."
        "<br><br>"
        "Please kindly review and let us know if you have any questions."
        "<br><br>"
        "Thank you!"
        )
    HTMLstart = "<html>" + "<body>" + txtStart
    
    HTMLend = (
        "<br><br>"
        f"This email was sent by <b>{user_name} ({user_email[0]})</b> on EDD Tracker."
        "<br><br>Best,<br>EDD Tracker<br></body></html>"
        )

    if test:
        mail.To = user_email[0]
        mail.CC = user_email[0]
    else:
        mail.To = STEP3_TO_EMAILS + "; " + user_email[1]
        mail.CC = STEP3_CC_EMAILS + "; " + user_email[0]
        
    mail.Subject = title
    mail.HTMLBody = HTMLstart + HTMLend
    mail.Attachments.Add(attachment_path)
    mail.Send()
    return "Step4 email sent!"


def send_step5_email(qc_analyst, data_info, user_name, user_email, attachment_path, test=TEST):
    # outlook = win32.Dispatch('outlook.application')
    outlook = win32com.client.Dispatch("outlook.Application", pythoncom.CoInitialize())
    mail = outlook.CreateItem(0)

    title = f"Approved: {data_info['Customer_ID']}_{data_info['Customer_Name']}_2023 Periodic KYC Refresh Review"

    txtStart = (
        f"Hi {qc_analyst},"
        "<br><br>"
        "Please see approved version as attached."
        "<br><br>"
        "Thank you!"
        )
    HTMLstart = "<html>" + "<body>" + txtStart
    
    HTMLend = (
        "<br><br>"
        f"This email was sent by <b>{user_name} ({user_email})</b> on EDD Tracker."
        "<br><br>Best,<br>EDD Tracker<br></body></html>"
        )

    if test:
        mail.To = user_email
        mail.CC = user_email
    else:
        mail.To = STEP4_TO_EMAILS + "; " + user_email
        mail.CC = STEP4_CC_EMAILS
        
    mail.Subject = title
    mail.HTMLBody = HTMLstart + HTMLend
    mail.Attachments.Add(attachment_path)
    mail.Send()
    return "Step5 email sent!"


def send_step6_email(fid_client, data_info, user_name, user_email, attachment_path, test=TEST):
    # outlook = win32.Dispatch('outlook.application')
    outlook = win32com.client.Dispatch("outlook.Application", pythoncom.CoInitialize())
    mail = outlook.CreateItem(0)

    title = f"{data_info['Customer_ID']}_{data_info['Customer_Name']}_2023 Periodic KYC Refresh Review"

    txtStart = (
        f"Hi {fid_client},"
        "<br><br>"
        "Please see QC comments and let me know if you have any questions."
        "<br><br>"
        "Thank you!"
        )
    HTMLstart = "<html>" + "<body>" + txtStart
    
    HTMLend = (
        "<br><br>"
        f"This email was sent by <b>{user_name} ({user_email[0]})</b> on EDD Tracker."
        "<br><br>Best,<br>EDD Tracker<br></body></html>"
        )

    if test:
        mail.To = user_email[0]
        mail.CC = user_email[0]
    else:
        mail.To = STEP6_TO_EMAILS + "; " + user_email[1]
        mail.CC = STEP6_CC_EMAILS + "; " + user_email[0]
        
    mail.Subject = title
    mail.HTMLBody = HTMLstart + HTMLend
    mail.Attachments.Add(attachment_path)
    mail.Send()
    return "Step6 email sent"


def send_step7_email(qc_analyst, data_info, user_name, user_email, attachment_path, test=TEST):
    # outlook = win32.Dispatch('outlook.application')
    outlook = win32com.client.Dispatch("outlook.Application", pythoncom.CoInitialize())
    mail = outlook.CreateItem(0)

    title = f"New onboarding {data_info['Customer_ID']}_{data_info['Customer_Name']}"

    txtStart = (
        f"Hi {qc_analyst},"
        "<br><br>"
        "Thanks for your comments. All issues have been addressed, please kindly find the details as attached. Please free feel to let me know if you have any questions."
        "<br><br>"
        "Thank you!"
        )
    HTMLstart = "<html>" + "<body>" + txtStart
    
    HTMLend = (
        "<br><br>"
        f"This email was sent by <b>{user_name} ({user_email[0]})</b> on EDD Tracker."
        "<br><br>Best,<br>EDD Tracker<br></body></html>"
        )

    if test:
        mail.To = user_email[0]
        mail.CC = user_email[0]
    else:
        mail.To = STEP7_TO_EMAILS + "; " + user_email[1]
        mail.CC = STEP7_CC_EMAILS + "; " + user_email[0]
        
    mail.Subject = title
    mail.HTMLBody = HTMLstart + HTMLend
    mail.Attachments.Add(attachment_path)
    mail.Send()
    return "Step7 email sent"


def send_step9_email(edd_approver, data_info, user_name, user_email, attachment_path, test=TEST):
    # outlook = win32.Dispatch('outlook.application')
    outlook = win32com.client.Dispatch("outlook.Application", pythoncom.CoInitialize())
    mail = outlook.CreateItem(0)

    title = f"New onboarding {data_info['Customer_ID']}_{data_info['Customer_Name']}"

    txtStart = (
        f"Hi {edd_approver},"
        "<br><br>"
        f"FID has submitted a new onboarding request for {data_info['Customer_Name']}. "
        f"The purpose of the new onboarding is for {data_info['Customer_Name']} to open USD clearing accounts with BOCNY in order to engage in investment activities with Customer."
        "<br><br>"
        "There was no negative news identified during the new onboarding review period. "
        "KYC profile and CRR have been updated to include customer's profile and anticipated account activities information. "
        "This customer is currently rated as Medium risk under FI Enhanced CRR. "
        "<br><br>"
        "Please feel free to let us know if any questions."
        "<br><br>"
        "Thank you!"
        )
    HTMLstart = "<html>" + "<body>" + txtStart
    
    HTMLend = (
        "<br><br>"
        f"This email was sent by <b>{user_name} ({user_email[0]})</b> on EDD Tracker."
        "<br><br>Best,<br>EDD Tracker<br></body></html>"
        )

    if test:
        mail.To = user_email[0]
        mail.CC = user_email[0]
    else:
        mail.To = STEP9_TO_EMAILS + "; " + user_email[1]
        mail.CC = STEP9_CC_EMAILS + "; " + user_email[0]
        
    mail.Subject = title
    mail.HTMLBody = HTMLstart + HTMLend
    mail.Attachments.Add(attachment_path)
    mail.Send()
    return "Step9 email sent"


def send_step10_email(data_info, user_name, user_email, attachment_path, action="Approve", test=TEST):
    # outlook = win32.Dispatch('outlook.application')
    outlook = win32com.client.Dispatch("outlook.Application", pythoncom.CoInitialize())
    mail = outlook.CreateItem(0)

    title = f"{action}: {data_info['Customer_ID']}_{data_info['Customer_Name']} Periodic KYC Refresh Review"

    if action == "Approve":
        txtStart = (
            "Hi KYC Team,"
            "<br><br>"
            "The above mentioned customer's 2023 KYC refresh has been approved. Please see the attached KYC with the approved CRR embedded. "
            "<br><br>"
            "Hi Brian and Ariel,"
            "<br><br>"
            "Please update EDD trackers accordingly."
            "<br><br>"
            "Thank you!"
            )
    elif action == "Reject":
        txtStart = (
            "Hi ALL,"
            "<br><br>"
            "The above mentioned customer's 2023 KYC refresh has been rejected."
            )
    else:
        raise ValueError("Wrong parameters! Please input 'Approve' or 'Reject'!")
        
    HTMLstart = "<html>" + "<body>" + txtStart
    HTMLend = (
        "<br><br>"
        f"This email was sent by <b>{user_name} ({user_email})</b> on EDD Tracker."
        "<br><br>Best,<br>EDD Tracker<br></body></html>"
        )

    if test:
        mail.To = user_email
        mail.CC = user_email
    else:
        mail.To = STEP10_TO_EMAILS + "; " + user_email
        mail.CC = STEP10_CC_EMAILS
        
    mail.Subject = title
    mail.HTMLBody = HTMLstart + HTMLend
    if action == "Approve":
        mail.Attachments.Add(attachment_path)
    mail.Send()
    return "Step10 email sent"

