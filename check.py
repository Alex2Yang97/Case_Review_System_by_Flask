import os
import pickle
import win32com.client as win32
from werkzeug.security import generate_password_hash, check_password_hash

TEST = True
SQL_TYPE = "sqlite"


def send_data_email(data_info, user_name, user_email, test=TEST, sql_type=SQL_TYPE):
    print(data_info)
    print(user_name)
    print(user_email)
    outlook = win32.Dispatch('outlook.application')
    mail = outlook.CreateItem(0)

    if sql_type == "sql server":
        title = f"Data QC Notification_{data_info.Customer_ID}_{data_info.Customer_Name} ({data_info.Scheduled_Due_Date})"
    else:
        title = f'''Data QC Notification_{data_info["Customer_ID"]}_{data_info["Customer_Name"]} ({data_info["Scheduled_Due_Date"]})'''
        
    header = ("<thead><tr>"
              "<th>Customer ID</th>"
              "<th>Customer Name</th>"
              "<th>Due Date</th>"
              "</tr></thead>")
    
    if sql_type == "sql server":
        Data = ("<tbody><tr>"
                f"<td>{data_info.Customer_ID}</td>"
                f"<td>{data_info.Customer_Name}</td>"
                f"<td>{data_info.Scheduled_Due_Date}</td>"
                "</tr></tbody>")
    else:
        Data = ("<tbody><tr>"
                f"<td>{data_info['Customer_ID']}</td>"
                f"<td>{data_info['Customer_Name']}</td>"
                f"<td>{data_info['Scheduled_Due_Date']}</td>"
                "</tr></tbody>")
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



if __name__ == '__main__':
    data_info = {'Customer_ID': '123', 'Customer_Name': 'test_upload', 'Scheduled_Due_Date': '2024-04-03'}
    user_name = "Alex"
    user_email = ['zryang@bocusa.com', 'zryang@bocusa.com']
    send_data_email(data_info, user_name, user_email, test=TEST, sql_type=SQL_TYPE)
    
