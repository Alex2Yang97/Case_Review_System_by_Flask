import os
import sqlite3
from flask_login import UserMixin

from .config import USER_ADMIN_PATH
from .utils import select_sql


class User(UserMixin):
    def __init__(self, id, name, email, password, ip, edit_auth, data_analyst, research_analyst, report_analyst):
         self.id = id
         self.name = name
         self.email = email
         self.password = password
         self.ip = ip
         self.edit_auth = edit_auth
         self.data = data_analyst
         self.research = research_analyst
         self.report = report_analyst
         self.authenticated = False
    def is_active(self):
         return self.is_active()
    def is_anonymous(self):
         return False
    def is_authenticated(self):
         return self.authenticated
    def is_active(self):
         return True
    def get_id(self):
         return self.id
     
    
def get_user_info(user_id):
     lu = select_sql(
          '''SELECT ID, Name, Email, Password, IP, Edit_Authority, Data_analyst, Research_analyst, Report_analyst from User_Info where id = (?)''',
          [user_id],
          db_path=USER_ADMIN_PATH
          )
     
     if lu is None:
          return None
     else:
          return User(
               lu["ID"], lu["Name"], lu["Email"], lu["Password"], lu["IP"], 
               lu["Edit_Authority"], lu["Data_analyst"], lu["Research_analyst"], lu["Report_analyst"])
