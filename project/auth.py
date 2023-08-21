import os
import sqlite3
import threading
from collections import defaultdict
from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required

from .models import User
from .emails import sign_up_email, verification_email
from .forms import SignupForm, VerificationForm, ForgotForm, ResetPWDForm
from .utils import rand_pass
from .config import USER_ADMIN_PATH

USER_VERIFY_DICT = defaultdict(dict)


auth = Blueprint('auth', __name__)


def get_user_info_by_name(user_name):
    conn = sqlite3.connect(USER_ADMIN_PATH)
    curs = conn.cursor()
    curs.execute('''
        SELECT ID, Name, Email, Password, IP, Edit_Authority, Data_analyst, Research_analyst, Report_analyst 
        from User_Info where Name = (?) COLLATE NOCASE
        ''', [user_name])
    lu = curs.fetchone()
    curs.close()
    conn.close()
    if lu is None:
        return None
    else:
        return User(lu[0], lu[1], lu[2], lu[3], lu[4], lu[5], lu[6], lu[7], lu[8])
    

@auth.route('/')
def login():
    return render_template('login_user.html')


@auth.route('/', methods=['POST'])
def login_post():
    user_name = request.form.get('username')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False
    
    # check if user actually exists
    # take the user supplied password, hash it, and compare it to the hashed password in database
    user = get_user_info_by_name(user_name)
    
    if request.method == "POST":
        if not user or not check_password_hash(user.password, password): 
            flash('Please check your login details and try again.', "danger")
            return redirect(url_for('auth.login')) # if user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    return redirect(url_for('main.index_page'))


@auth.route('/forgot', methods=["GET", "POST"])
def forgot_page():
    forgot_form = ForgotForm()
    
    if forgot_form.reset_btn.data and forgot_form.validate():
        conn = sqlite3.connect(USER_ADMIN_PATH)
        curs = conn.cursor()
        check_email = curs.execute("SELECT Email from User_Info where Email = (?) COLLATE NOCASE", [forgot_form.email.data]).fetchone()
        curs.close()
        conn.close()
        if not check_email:
            flash("This email hasn't signed up before!", 'danger')
            return redirect(url_for(("auth.forgot_page")))
        else:
            # global verify_code, email_reset
            # verify_code = rand_pass()
            # verify_code = "EDD2023"
            
            email_reset = forgot_form.email.data
            
            global USER_VERIFY_DICT 
            USER_VERIFY_DICT[email_reset]["code"] = rand_pass()
            
            message = verification_email(USER_VERIFY_DICT[email_reset]["code"], email_reset)
            flash(message, "primary")
            return redirect(url_for("auth.verify", user_email=email_reset, verif_type="reset"))
    
    return render_template('forgot.html', forgot_form=forgot_form)


@auth.route('/reset/<email_reset>', methods=["GET", "POST"])
def reset_page(email_reset):
    reset_form = ResetPWDForm()
    
    if reset_form.confirm_btn.data and reset_form.validate():
        conn = sqlite3.connect(USER_ADMIN_PATH)
        curs = conn.cursor()
        hash_pwd = generate_password_hash(reset_form.pwd1.data, method='sha256')
        curs.execute("Update User_Info set Password = ? where Email = ?", (hash_pwd, email_reset))
        conn.commit()
        curs.close()
        conn.close()
        flash("Password has been reset", "success")       
        return redirect(url_for("auth.login"))
    
    return render_template('reset_pwd.html', reset_form=reset_form)


@auth.route('/signup', methods=["GET", "POST"])
def signup():
    signup_form = SignupForm()
    
    if signup_form.signup_btn.data and signup_form.validate():
        global user_name, user_email, hash_pwd, ip
        user_name = signup_form.username.data
        user_email = signup_form.email.data

        conn = sqlite3.connect(USER_ADMIN_PATH)
        curs = conn.cursor()
        
        # 需要让sqlite case insensitive
        check_email = curs.execute("SELECT Email from User_Info where Email = (?) COLLATE NOCASE", [user_email]).fetchone()
        check_name = curs.execute("SELECT Name from User_Info where Name = (?) COLLATE NOCASE", [user_name]).fetchone()
        
        if check_email and check_email[0].lower()!="zryang@bocusa.com":
            flash("This email has signed up before. If you forget password, please click forget password!", 'danger')
            return redirect(url_for("auth.signup"))
        elif check_name:
            flash("This Username has been used. Please change another name!", 'danger')
            return redirect(url_for("auth.signup"))
        else:
            hash_pwd = generate_password_hash(signup_form.pwd1.data, method='sha256')
            ip = request.remote_addr
            
            global USER_VERIFY_DICT 
            USER_VERIFY_DICT[user_email]["code"] = rand_pass()
            USER_VERIFY_DICT[user_email]["user_name"] = user_name
            USER_VERIFY_DICT[user_email]["hash_pwd"] = hash_pwd
            USER_VERIFY_DICT[user_email]["ip"] = ip
            
            # verify_code = "EDD2023"
            message = verification_email(USER_VERIFY_DICT[user_email]["code"], user_email)
            flash(message, "primary")
            return redirect(url_for("auth.verify", user_email=user_email, verif_type="signup"))
        
    if signup_form.back_btn.data and signup_form.validate():
        return redirect(url_for("auth.login"))

    return render_template('signup_user.html', signup_form=signup_form)


@auth.route('/verification/<user_email>/<verif_type>', methods=["GET", "POST"])
def verify(user_email, verif_type):
    
    # verify_code = "EDD2023"
    global USER_VERIFY_DICT 
    verify_code = USER_VERIFY_DICT[user_email]["code"]
    
    verification_form = VerificationForm()
    if verification_form.confirm_btn.data and verification_form.validate():
        if verify_code == verification_form.verify_code.data:
            if verif_type == "signup":
                user_name = USER_VERIFY_DICT[user_email]["user_name"]
                ip = USER_VERIFY_DICT[user_email]["ip"]
                hash_pwd = USER_VERIFY_DICT[user_email]["hash_pwd"]
                
                conn = sqlite3.connect(USER_ADMIN_PATH)
                c = conn.cursor()
                c.execute(
                    '''INSERT INTO User_Info (Name, Email, IP, Password) VALUES (?, ?, ?, ?)''', (user_name, user_email, ip, hash_pwd))
                conn.commit()
                conn.close()
                flash("Sign Up a new account!", 'success')
                return redirect(url_for("auth.login"))
            else:
                return redirect(url_for("auth.reset_page", email_reset=user_email))
        else:
            flash("Wrong Verification Code", 'danger')
            return redirect(url_for("auth.verify", user_email=user_email, verif_type=verif_type))
        
    return render_template('signup_verification.html', verification_form=verification_form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
