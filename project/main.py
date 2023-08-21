import os
import shutil
import datetime
import pandas as pd


from flask import Blueprint, render_template, make_response, send_file
from flask_login import login_required

from .utils import connect_db
from .config import DOC_TEMPLATES_DIR, METRICS_DIR, TEST
from .metrics import gen_case_metrics, gen_rmb_case_metrics, gen_recom_metrics, gen_sar_metrics


main = Blueprint('main', __name__)


RELEASE_DATE = datetime.datetime.now().date()

@main.route('/home')
@login_required
def index_page():
    return render_template('index.html', release_date=RELEASE_DATE, version="Test" if TEST else "Product")


@main.route('/version_updates')
@login_required
def version_updates_page():
    return render_template('updates_version.html')


@main.route('/todo_updates')
@login_required
def todo_updates_page():
    return render_template('updates_todo.html')


@main.route('/metrics', methods=["GET"])
@login_required
def download_metrics():
    sample_name = os.path.join(DOC_TEMPLATES_DIR, "Case Metrics Sample.xlsx")
    copy_file = shutil.copy(sample_name, METRICS_DIR)
    
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    new_name = os.path.join(METRICS_DIR, f"Metrics - {date_str}.xlsx")
    os.rename(copy_file, new_name)
    
    year_now = datetime.datetime.now().year
    month_now = datetime.datetime.now().month
    
    gen_case_metrics(year_now, month_now, new_name)
    gen_rmb_case_metrics(year_now, month_now, new_name)
    gen_recom_metrics(year_now, month_now, new_name)
    gen_sar_metrics(year_now, month_now, new_name)
    
    return send_file(new_name, as_attachment=True)
    
    
    
    
