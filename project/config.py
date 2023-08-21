import os

TEST = True
PJ_DIR = r"xxx"

SQL_TYPE = "sqlite" # sql server

SQL_SERVER_NAME = "xxxx"
SQL_SERVER_PWD = "xxxx"

DEVELOPERS = ("xxx", "xxx")

ADMIN_EMAIL = "xxx"

DB_DIR = os.path.join(PJ_DIR, "Database")
FILE_DIR = os.path.join(PJ_DIR, "Filebase")

# Database path
DB_BACKUP_DIR = os.path.join(DB_DIR, "Database-backup")
DB_TEST_DIR = os.path.join(DB_DIR, "Database-test")
DB_PROD_DIR = os.path.join(DB_DIR, "Database-prod")

if TEST:
    EDD_DB_PATH = os.path.join(DB_TEST_DIR, 'EDD_Database_test.db')
    USER_ADMIN_PATH = os.path.join(DB_TEST_DIR, 'User_Admin.db')
    LOG_PATH = os.path.join(DB_TEST_DIR, 'User_Log.db')
else:
    EDD_DB_PATH = os.path.join(DB_PROD_DIR, 'EDD_Database_prod.db')
    USER_ADMIN_PATH = os.path.join(DB_PROD_DIR, 'User_Admin.db')
    LOG_PATH = os.path.join(DB_PROD_DIR, 'User_Log.db')

# Filebase path
if TEST:
    UPLOAD_DIR = os.path.join(FILE_DIR, "Filebase-test")
else:
    UPLOAD_DIR = os.path.join(FILE_DIR, "Filebase-prod")
    
FILE_BACKUP_DIR = os.path.join(FILE_DIR, "Filebase-backup")
DOC_TEMPLATES_DIR = os.path.join(FILE_DIR, "Docs_templates")

# Metrics path
METRICS_DIR = os.path.join(UPLOAD_DIR, "Metrics")

# EDD Tracking path
FID_RFI_REPORT_DIR = os.path.join(UPLOAD_DIR, "Step1_FID_RFI_Reports")
EDD_ANS_REPORT_DIR = os.path.join(UPLOAD_DIR, "EDD_Analysis_Reports")
CRR_DRAFTS_DIR = os.path.join(UPLOAD_DIR, "Step3_CRR_Drafts")
CRR_APPROVED_DIR = os.path.join(UPLOAD_DIR, "Step4_CRR_Approved")

REVIEW_DRAFTS_DIR = os.path.join(UPLOAD_DIR, "Step5_Review_Drafts")
REVIEW_FROM_KYC_EDD_DIR = os.path.join(UPLOAD_DIR, "Step6_Review_from_KYC_EDD")
REVIEW_FROM_FID_CLIENT_DIR = os.path.join(UPLOAD_DIR, "Step7_Review_from_FID-Client")
REVIEW_FOR_APPROVAL_DIR = os.path.join(UPLOAD_DIR, "Step9_Review_for_Approval")
REVIEW_APPROVED_DIR = os.path.join(UPLOAD_DIR, "Step10_Review_Approved")


DATA_QC_TO_EMAILS = "xxx"
DATA_QC_CC_EMAILS = "xxx"

RESEARCH_QC_CC_EMAILS = "xxx"

REPORT_TO_EMAILS = "xxx"
REPORT_CC_EMAILS = "xxx"

APPROVE_TO_EMAILS = "xxx"
APPROVE_CC_EMAILS = "xxx"

STEP1_TO_EMAILS = ""
STEP1_CC_EMAILS = ""

STEP2_TO_EMAILS = ""
STEP2_CC_EMAILS = ""

STEP3_TO_EMAILS = ""
STEP3_CC_EMAILS = ""

STEP4_TO_EMAILS = ""
STEP4_CC_EMAILS = ""

STEP5_TO_EMAILS = ""
STEP5_CC_EMAILS = ""

STEP6_TO_EMAILS = ""
STEP6_CC_EMAILS = ""

STEP6_TO_EMAILS = ""
STEP6_CC_EMAILS = ""

STEP7_TO_EMAILS = ""
STEP7_CC_EMAILS = ""

STEP9_TO_EMAILS = ""
STEP9_CC_EMAILS = ""

STEP10_TO_EMAILS = ""
STEP10_CC_EMAILS = ""

# 如果用户ip有变化，先删掉旧ip，然后加入新ip
TRUSTED_IPS = [
    "127.0.0.1",
    "xxx"
]

# 用户起名字的时候喜欢使用windows id，但是系统上需要显示他们的常用名，所以这里需要根据他们的要求给他们手动添加
NAME_DICT = {
    "abc": "ABC"
}











