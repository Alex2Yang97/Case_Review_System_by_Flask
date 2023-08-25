# Case_Review_System_by_Flask
This is a case review system built by Flask, Bootstrap and SQLite (SQL Server).


For SQLite database examples

Database\Database-prod
EDD_Database_prod.db

Database\Database-test
EDD_Database_test.db


conn = sqlite3.connect(os.path.join(TEST_DIR, 'EDD_Database_test.db')) 
curs = conn.cursor()

curs.execute('''
    CREATE TABLE IF NOT EXISTS CaseTracking_local (
        Case_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Case_Status TEXT,
        Sub_Status TEXT,
        Customer_ID TEXT, 
        Customer_Name TEXT, 
        Risk_Rating TEXT, 
        FID_KYC_Refresh_Date TEXT,
        Scheduled_Start_Date TEXT,
        Scheduled_Due_Date TEXT,
        Transaction_Start_Date TEXT,
        Transaction_End_Date TEXT,
        Category TEXT, 
        Type TEXT,
        Case_Type TEXT,
        Comment TEXT,
        
        Recom_Esca_Volume INTEGER,
        Has_Recommendation TEXT,
        Escal_Recom_Status TEXT,
        Has_SAR_Referral TEXT,
        SAR_Referral_Status TEXT,
        Has_Sanction_Referral TEXT,
        Sanction_Referral_Status TEXT, 
        
        Data_Start_Date TEXT,
        Data_Analyst TEXT,

        Data_QC_Complete_Date TEXT,
        Data_QC_Analyst TEXT,
        Case_Assigned_Date TEXT,
        Volume INTEGER,
        Value REAL,
        Currency TEXT,
        Number_of_SARs INTEGER,
        High_Risk_Country_Vol_Percentage REAL,
        High_Risk_Country_Val_Percentage REAL,
        
        Research_Started_Date TEXT,
        Research_Complete_Date TEXT,
        Research_Anticipated_Complete_Date TEXT,
        Research_Analyst TEXT,
        Research_Entities_Volume INTEGER,
        
        Research_QC_Start_Date TEXT,
        Research_QC_Anticipated_Complete_Date TEXT,
        Research_QC_Complete_Date TEXT,
        Research_QC_Analyst TEXT,
        
        Report_Start_Date TEXT,
        Report_Complete_Date TEXT,
        Report_Analyst TEXT,
        Nested_Volume INTEGER,
        Nested_Value REAL,
        
        Report_QC_Start_Date TEXT,
        Report_QC_Complete_Date TEXT,
        Report_QC_Analyst TEXT,
        Report_for_Approval_Date TEXT,
        Report_Approved_Date TEXT,
        
        Case_ID_server INTEGER
        )
          ''')

conn.commit()
curs.close()
conn.close()

conn = sqlite3.connect(os.path.join(TEST_DIR, 'EDD_Database_test.db')) 
curs = conn.cursor()

curs.execute('''
    CREATE TABLE IF NOT EXISTS Recommendation_local (
        Recommendation_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Status TEXT,
        Case_ID INTEGER,
        From_Section TEXT,
        Recomm_or_Escal TEXT,
        Responsible_Personnel TEXT,
        Action_Details TEXT,
        Escalation_Type TEXT,
        Escalated_To TEXT,
        Recommendation_Closure_Details TEXT,
        
        Escal_Recomm_Details TEXT,
        Followup_Date_1st TEXT,
        Followup_Date_2nd TEXT,
        Initiated_Date TEXT,
        Ack_Action_Date TEXT,
        Last_Followup_Date TEXT,
        Escalation_Date TEXT,
        Closure_Date TEXT
        )
          ''')

conn.commit()
curs.close()
conn.close()


conn = sqlite3.connect(os.path.join(TEST_DIR, 'EDD_Database_test.db')) 
curs = conn.cursor()

curs.execute('''
    CREATE TABLE IF NOT EXISTS SARref_local (
        SAR_Referral_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Case_ID INTEGER,
        Status TEXT,
        Subject_Name TEXT,
        Amount REAL,
        Subject_Account_NO TEXT,
        Referral_Reason TEXT,
        Reviewed_By_SAR TEXT,
        Referral_Necessary TEXT,
        SAR_Team_Comment TEXT,
        Referral_Warranted TEXT,
        EDD_Comment TEXT,
        CTRL_CMT TEXT,
        Currency TEXT,
        Activity_Start_Date TEXT,
        Activity_End_Date TEXT,
        Initiated_Date TEXT,
        Date_Submitted TEXT,
        Date_Acknowledged TEXT
        )
          ''')

conn.commit()
curs.close()
conn.close()


conn = sqlite3.connect(os.path.join(TEST_DIR, 'EDD_Database_test.db')) 
curs = conn.cursor()

curs.execute('''
    CREATE TABLE IF NOT EXISTS SanctionRef_local (
        Sanction_Referral_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Subject_Name TEXT,
        Amount REAL,
        Referral_Reason TEXT,
        Additional_Comment TEXT,
        Status TEXT,
        Case_ID INTEGER,
        Currency TEXT,
        Submit_Date TEXT,
        Acknowledged_Date TEXT
        )
        ''')

conn.commit()
curs.close()
conn.close()


conn = sqlite3.connect(os.path.join(TEST_DIR, 'EDD_Database_test.db')) 
curs = conn.cursor()

curs.execute('''
    CREATE TABLE IF NOT EXISTS CIC_Cases (
        CIC_Case_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Case_ID INTEGER,
        CIC_Case_Status TEXT,
        CIC_Customer_ID TEXT,
        CIC_Customer_Name TEXT,
        Risk_Rating TEXT,
        Type TEXT,
        KYC_Refresh_Date TEXT,
        Comments TEXT
        )
        ''')

conn.commit()
curs.close()
conn.close()


conn = sqlite3.connect(os.path.join(TEST_DIR, 'EDD_Database_test.db')) 
curs = conn.cursor()

curs.execute('''
    CREATE TABLE IF NOT EXISTS EDD_tracking (
        Tracking_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Case_ID INTEGER,
        Tracking_Status INTEGER,
        RFI_Analyst TEXT,
        RFI_Initiation_Date TEXT,
        FID_Client TEXT,

        Step2_Date TEXT,
        KYC_Analyst TEXT,
        QC_Analyst TEXT,

        Step3_Date TEXT,
        Step3_Analyst TEXT,
        FID_BSA_Officer TEXT,

        Step4_Date TEXT,
        Step4_Analyst TEXT,

        Step5_Date TEXT,
        Step5_Analyst TEXT,

        Step6_Round INTEGER,
        Step6_Latest_Time DATETIME,
        Step6_Latest_Comment TEXT,
        Step6_Analyst TEXT,

        Step7_Round INTEGER,
        Step7_Latest_Time DATETIME,
        Step7_Latest_Comment TEXT,
        Step7_Analyst TEXT,
        
        Step8_Date TEXT,
        Step8_Analyst TEXT,

        Step9_Analyst TEXT,
        Step9_Round INTEGER,
        New_Risk_Rating TEXT,
        EDD_Head_Approver TEXT,
        Step9_Latest_Time DATETIME,
        Step9_Latest_Comment TEXT,

        Step10_Analyst TEXT,
        Step10_Round INTEGER,
        Approver_Action TEXT,
        Step10_Latest_Time DATETIME,
        Step10_Latest_Comment TEXT
        )
        ''')

conn.commit()
curs.close()
conn.close()



conn = sqlite3.connect(os.path.join(TEST_DIR, 'EDD_Database_test.db')) 
curs = conn.cursor()

curs.execute('''
    CREATE TABLE IF NOT EXISTS Track_step6 (
        Record_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Tracking_ID INTEGER,
        Step6_Round INTEGER,
        Step6_Analyst TEXT,
        Step6_Time DATETIME,
        Step6_Comment TEXT
        )
        ''')

conn.commit()
curs.close()
conn.close()


conn = sqlite3.connect(os.path.join(TEST_DIR, 'EDD_Database_test.db')) 
curs = conn.cursor()

curs.execute('''
    CREATE TABLE IF NOT EXISTS Track_step7 (
        Record_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Tracking_ID INTEGER,
        Step7_Round INTEGER,
        Step7_Analyst TEXT,
        Step7_Time DATETIME,
        Step7_Comment TEXT
        )
        ''')

conn.commit()
curs.close()
conn.close()



conn = sqlite3.connect(os.path.join(TEST_DIR, 'EDD_Database_test.db')) 
curs = conn.cursor()

curs.execute('''
    CREATE TABLE IF NOT EXISTS Track_step9 (
        Record_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Tracking_ID INTEGER,
        Step9_Round INTEGER,
        Step9_Analyst TEXT,
        Step9_Time DATETIME,
        Step9_Comment TEXT
        )
        ''')

conn.commit()
curs.close()
conn.close()


conn = sqlite3.connect(os.path.join(TEST_DIR, 'EDD_Database_test.db')) 
curs = conn.cursor()

curs.execute('''
    CREATE TABLE IF NOT EXISTS Track_step10 (
        Record_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Tracking_ID INTEGER,
        Step10_Round INTEGER,
        Step10_Analyst TEXT,
        Step10_Time DATETIME,
        Step10_Comment TEXT
        )
        ''')

conn.commit()
curs.close()
conn.close()

+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

conn = sqlite3.connect(os.path.join(project_dir, "databases", 'User_Log.db')) 
curs = conn.cursor()

curs.execute('''
          CREATE TABLE IF NOT EXISTS Log_Info
          ([ID] INTEGER PRIMARY KEY, [Request_Date] TIMESTAMP not null, [Request_IP] TEXT not null,
          [Request_Method] TEXT not null, [Request_Path] TEXT not null, [Request_Form] TEXT not null, [Request_Status] TEXT not null)
          ''')

conn.commit()
curs.close()
conn.close()



conn = sqlite3.connect(os.path.join(project_dir, 'User_Admin.db')) 
c = conn.cursor()

c.execute('''
          CREATE TABLE IF NOT EXISTS User_Info
          ([ID] INTEGER PRIMARY KEY, [Name] TEXT not null,
          [Password] TEXT not null, [Email] TEXT not null, 
          [IP] TEXT not null)
          ''')

conn.commit()
conn.close()
