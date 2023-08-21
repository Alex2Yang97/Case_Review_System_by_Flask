import os
import shutil
from distutils.dir_util import copy_tree

from datetime import datetime, timedelta

from .config import TEST, DB_BACKUP_DIR, DB_PROD_DIR


def make_backup(source_folder=DB_PROD_DIR, destination_folder=DB_BACKUP_DIR, test=TEST):
    if test:
        print("This is test version. Don't make backup.")
    else:
        current_date = datetime.now().date()
        new_folder_name = os.path.join(destination_folder, f"Database-prod-{current_date}")
        if not os.path.exists(new_folder_name):
            os.makedirs(new_folder_name)
        else:
            raise Exception("Folder has existed! Please check it.")
        copy_tree(source_folder, new_folder_name)
        print("Back up successfully!")
        
        over_7_days = (datetime.now() - timedelta(days=7)).date()
        remove_folder_name = os.path.join(destination_folder, f"Database-prod-{over_7_days}")
        if os.path.exists(remove_folder_name):
            shutil.rmtree(remove_folder_name)
            print(f"Remove {remove_folder_name} successfully!")
        else:
            print(f"No backup for {remove_folder_name}.")
        
    return
        
    
