import sqlite3
import pandas as pd
from flask import render_template, url_for, flash, redirect, Blueprint, abort, request
from flask_login import login_required

from .forms import AdminManageForm
from .config import USER_ADMIN_PATH
from .utils import get_name


realboss = Blueprint('realboss', __name__)


@realboss.route('/admin_manage', methods=["GET", "POST"])
@login_required
def admin_page():
    conn = sqlite3.connect(USER_ADMIN_PATH)
    admin_ip_lst = pd.read_sql(f"SELECT IP from User_Info where Admin_manager = 1", conn)["IP"].tolist()
    admin_ip_lst.append("22.232.109.188") # Alex's ip
    conn.close()
    
    if request.remote_addr not in admin_ip_lst:
        abort(403)
    
    admin_form = AdminManageForm()
    
    if admin_form.enter_btn.data and admin_form.validate():
        conn = sqlite3.connect(USER_ADMIN_PATH) 
        curs = conn.cursor()
        user_name = get_name(show_name=admin_form.username.data)
        
        if admin_form.add_or_revoke.data == "Delete User":
            if request.remote_addr != "127.0.0.1":
                flash("Only Developers can delete user!", "danger")
            else:
                flash(f"Delete {admin_form.username.data}!", "success")
                curs.execute("DELETE FROM User_Info where Name = (?)", [user_name])
                conn.commit()
        else:
            if admin_form.permission_type.data == "Admin_manager":
                if request.remote_addr != "127.0.0.1":
                    flash("Only Developers can change admin!", "danger")
                else:
                    flash(f"{admin_form.add_or_revoke.data} {admin_form.username.data} {admin_form.permission_type.data}", "success")
                    add_or_revoke = 1 if admin_form.add_or_revoke.data == "Add" else 0
                    curs.execute(f"update User_Info set {admin_form.permission_type.data} = (?) where Name = (?)", [add_or_revoke, user_name])
                    conn.commit()
            else:
                flash(f"{admin_form.add_or_revoke.data} {admin_form.username.data} {admin_form.permission_type.data}", "success")
                add_or_revoke = 1 if admin_form.add_or_revoke.data == "Add" else 0
                curs.execute(f"update User_Info set {admin_form.permission_type.data} = (?) where Name = (?)", [add_or_revoke, user_name])
                conn.commit()

        curs.close()
        conn.close()
        
        return redirect(url_for("realboss.admin_page"))
    
    # Show User and user permission
    conn = sqlite3.connect(USER_ADMIN_PATH)
    admin_df = pd.read_sql('''
        select Name, Edit_Authority, Data_analyst, Research_analyst, Report_analyst, Admin_manager,
        RFI_analyst, KYC_analyst, QC_analyst, FID_client, FID_BSA_officer, EDD_head_approver
        from User_Info
        ''', conn)
    admin_df = admin_df.fillna(0)
    
    permission_cols = admin_df.columns.tolist()
    permission_cols.remove("Name")
    admin_df[permission_cols] = admin_df[permission_cols].astype(int)
    admin_df["Name"] = admin_df["Name"].apply(lambda username: get_name(user_name=username))
    
    return render_template('admin_manage.html', admin_form=admin_form, admin_df=admin_df)
