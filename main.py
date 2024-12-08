from flask import Flask, render_template, redirect, url_for, request, flash, abort, send_file
from forms import *
from functionality import *
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
import os
from flask_ckeditor import CKEditor


app = Flask(__name__)
bootstrap = Bootstrap5()
bootstrap.init_app(app)
ckeditor = CKEditor(app)

login_manager = LoginManager()
login_manager.init_app(app)


app.secret_key = os.environ["SECRET_KEY"]
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI', 'sqlite:///web_app_database.db')
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size':20,
    'max_overflow': 30,
    'pool_timeout': 30,
    'pool_recycle': 1800
}
app.config['UPLOAD_FOLDER'] = 'static/profile_pic'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = SQLAlchemy()
db.init_app(app)

indeptDetails = ("location", "staff", "payment", "confirm", "start", "end")

########################## DATABASE TABLE


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(30), unique=True, nullable=False)
    position = db.Column(db.String(30),  nullable=False)
    privilege = db.Column(db.String(30),  nullable=False)
    first_name = db.Column(db.String(30),  nullable=False)
    middle_name = db.Column(db.String(30))
    last_name = db.Column(db.String(30),  nullable=False)
    id_name = db.Column(db.String(30),  nullable=False)
    picture = db.Column(db.String(30), default='profilepic.png')
    password = db.Column(db.String(300), nullable=False)
    calendar = relationship("Calendar", back_populates='staff', lazy='subquery')
    contract = db.Column(db.String(30), nullable=False)
    pending = db.Column(db.String(30))
    working = db.Column(db.String(30))
    reject = db.Column(db.String(30))

    comment = relationship("Comment", back_populates='author_name', lazy='subquery')


class Calendar(db.Model):

    __tablename__ = 'calendar'

    id = db.Column(db.Integer, primary_key=True)

    staff_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    staff = relationship("User", back_populates='calendar', lazy='subquery')
    reason = db.Column(db.String(500))
    status = db.Column(db.String(30), nullable=False)
    start = db.Column(db.String(30))
    stop = db.Column(db.String(30))




class Task(db.Model):

    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)

    task_id = db.Column(db.String(30), nullable=False)
    location = db.Column(db.String(30), nullable=False)
    task_name = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(30), nullable=False)
    cost = db.Column(db.Integer)
    payment = db.Column(db.Integer)
    startDate= db.Column(db.String(300))
    stopDate = db.Column(db.String(300))

    staff_pending = db.Column(db.String(300))
    staff_accepted = db.Column(db.String(300))
    staff_rejected = db.Column(db.String(300))

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))
    company_name = relationship("Company", back_populates='task', lazy='subquery')

    comment = relationship("Comment", back_populates='task_name', lazy='subquery')

class Company(db.Model):
    __tablename__ = 'company'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    location = db.Column(db.String(30), nullable=False)
    contact = db.Column(db.String(30))
    contact_name = db.Column(db.String(30))
    mail = db.Column(db.String(30))

    task = relationship("Task", back_populates='company_name', lazy='subquery')

class Comment(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    author = db.Column(db.Integer, db.ForeignKey('users.id'))
    author_name = relationship("User", back_populates='comment', lazy='subquery')

    comment = db.Column(db.String(500), nullable=False)
    timing = db.Column(db.String(30), nullable=False)

    task = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    task_name = relationship("Task", back_populates='comment', lazy='subquery')


class Messages(db.Model):

    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)

    sender = db.Column(db.String(30), nullable=False)
    receiver = db.Column(db.String(30), nullable=False)
    timing = db.Column(db.String(30), nullable=False)
    title = db.Column(db.String(30), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    read = db.Column(db.Boolean, default=False)



with app.app_context():
    db.create_all()
    if len(db.session.query(User).all()) == 0:
        email = 'administrator@taskmanager.com'
        position = 'admin'
        first_name = "admin"
        last_name = "admin"
        privilege = "Administrator"
        password = "Password@1234"
        password = generate_password_hash(password=password,
                                              method='pbkdf2:sha256',
                                              salt_length=8)
        new_user = User(email=email,
                            position=position,
                            first_name=first_name,
                            last_name=last_name,
                            id_name="Admin",
                            password=password,
                            contract="Active",
                            privilege=privilege, )
        db.session.add(new_user)
        db.session.commit()



#                                              Helper function


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


def populate_choice():
    with app.app_context():
        companys = db.session.query(Company).all()
    if len(companys) == 0:
        return ['No company']
    else:
        return [(company.id, company.name) for company in companys]

def staff_list():
    with app.app_context():
        users = db.session.query(User).all()
    if len(users) <= 1:
        return ['No Staff']
    else:
        return [(staff.id, f"{staff.position} - {staff.id_name}") for staff in users if (staff.contract == 'Active' and staff.id != 1)]

def staff_stat(staff):
    complete = []
    on_going = []
    suspended = []
    if staff.pending in (None, "", ' '):
        pending_task = []
    else:
        pending_task = [db.get_or_404(Task,int(count)) for count in staff.pending if count.isnumeric()]
    if staff.working not in (None, "", ' '):
        accepted_task = [count for count in staff.working if count.isnumeric()]
        for id in accepted_task:
            task = db.get_or_404(Task, int(id))
            if task.status == 'Suspended':
                suspended.append(task)
            if task.status == 'Completed':
                complete.append(task)
            if task.status == 'On going':
                on_going.append(task)
    else:
        accepted_task = []
    if staff.reject not in (None, "", ' '):
        rejected_task = [db.get_or_404(Task,int(count)) for count in staff.reject if count.isnumeric()]
    else:
        rejected_task = []



    details = {'pen': (pending_task, len(pending_task)),
               'rej': (rejected_task, len(rejected_task)),
               'comp': (complete, len(complete)),
               'susp': (suspended, len(suspended)),
               'on': (on_going, len(on_going)),
               'acc': (accepted_task, len(accepted_task))}
    return details

def chart(staff_id):
    staff_id = int(staff_id)
    staff = db.get_or_404(User, staff_id)
    data = staff_stat(staff)
    image = draw_pie_chart(data[0])
    if image is not None:
        return send_file(image, as_attachment=False, mimetype='image/png')
    else:
        return "None"

def mail_counter():
    messages = db.session.query(Messages).all()
    messages = [message for message in messages if message.receiver == current_user.id_name]
    messages = [message for message in messages if message.read is False]
    return len(messages)



#                      COSTUME DECORATOR

def admin_only(funct):
    # ensure staffs can't view administrator page
    @wraps(funct)
    def decorated_function(*args, **kwargs):
        if current_user.privilege != 'Administrator':
            return abort(403, "You don't have access to URL")
        return funct(*args, **kwargs)
    return decorated_function

def member_only(f):
    # ensures the user only views task he related to the user
    @wraps(f)
    def decorated_function(task_id):
        task = db.get_or_404(Task, int(task_id))
        if current_user.privilege != 'Administrator':
            if str(current_user.id) not in task.staff_accepted.split(','):
                return abort(403)
        return f(task_id)
    return decorated_function

def leave_calculator(staff):
    # computes if the staff is still on leave or not
    if len(staff.calendar) > 0 and staff.calendar[-1].stop is not None:
        calendar = staff.calendar[-1]
        resume = datetime.strptime(calendar.stop, "%b %d, %Y %H %m")
        if calendar.status == 'Approved' and datetime.now() > resume:
            day = 6 - resume.weekday()
            if day in (1, 2):
                resume = resume + timedelta(days=day)
            else:
                resume = resume + timedelta(days=1)
            resume = datetime.strftime(resume, "%b %d, %Y %H %m")
            available_work = Calendar(staff=staff,
                                    start=resume,
                                  # stop=end,
                                  # reason=message,
                                    status='Available')
            return available_work
        else:
            return False
    else:
        return False




#                                                  Form sections

db_head = ["id", 'company name', 'task name', "task location", "assigned staff", 'cost', "payment", "Balance", "start", "status",
           "confirm"]

#                                      Route Section
@app.route("/<company>/<status>", methods=['POST', 'GET'])
@login_required
@admin_only
def task_list(company, status):
    # display all task for the administrator accounts
    with app.app_context():
        if company == 'all-task':
            data1 = db.session.query(Task).all()
        else:
            data1 = db.session.query(Task).filter(Task.company_id==company)
    details = task_info(data1)
    if status != "None":
        data1 = details[status][0]
    if request.method == 'POST':
        search_data = request.form.get('search_query')
        search_result = []
        for comp in data1:
            if search_data.upper() in comp.task_name.upper():
                search_result.append(comp)
            elif search_data.upper() in comp.task_id.upper():
                search_result.append(comp)
            elif search_data.upper() in comp.location.upper():
                search_result.append(comp)

        return render_template('home.html', company=company, comp=details, data=search_result, db_head=db_head, remove=indeptDetails, webpage='task', num_mail=mail_counter())
    return render_template('home.html', company=company, data=data1, comp=details, db_head=db_head, remove=indeptDetails, webpage='task', num_mail=mail_counter())


@app.route('/all-staffs/<category>', methods=['POST', 'GET'])
@login_required
@admin_only
# Display all the staff for the admin accounts
def all_staffs(category):
    with app.app_context():
        data1 = db.session.query(User).filter(User.id != 1)
        for staff in data1:
            update = leave_calculator(staff)
            if update:
                db.session.add(update)
        db.session.commit()
        data1 = db.session.query(User).filter(User.id != 1)
    details = all_staff_stats(data1)
    if category != "None":
        data1 = details[category][0]
    if request.method == 'POST':
        search_data = request.form.get('search_query')
        search_result = []
        for comp in data1:
            if search_data.upper() in comp.first_name.upper():
                search_result.append(comp)
            elif search_data.upper() in comp.last_name.upper():
                search_result.append(comp)
            elif search_data.upper() in comp.id_name.upper():
                search_result.append(comp)
            elif search_data.upper() in comp.email.upper():
                search_result.append(comp)
        return render_template('all_staffs.html', staffs=search_result, webpage='staff', num_mail=mail_counter(), details=details)
    return render_template('all_staffs.html', staffs=data1, webpage='staff', num_mail=mail_counter(), details=details)

@app.route('/add-company', methods=['GET', 'POST'])
@login_required
@admin_only
def addCompany():
    form = CompanyForm()
    if form.validate_on_submit():

        name = form.name.data
        location = form.location.data
        contact = form.contact.data
        contact_name = form.contact_name.data
        mail = form.mail.data
        newcompany = Company(name=name, location=location, contact_name=contact_name, contact=contact, mail=mail)
        db.session.add(newcompany)
        db.session.commit()
        flash(f"{name} has been successfully added to Company List!!")
        return redirect(url_for('companyList'))
    return render_template('add_company.html', form=form, num_mail=mail_counter())


@app.route("/add-task", methods=["GET", "POST"])
@login_required
@admin_only
def addTask():
    form = TaskForm()
    form.company_name.choices = populate_choice()
    form.engineer_name.choices = staff_list()
    if form.validate_on_submit():
        task_id = generate_id()
        task_name = form.task_name.data
        company_name = form.company_name.data
        engineer_name = form.engineer_name.data
        location = form.location.data
        cost = form.cost.data
        payment = form.payment.data
        startDate = form.startDate.data
        stopDate = "On going"
        # balance = cost - payment
        task_details = Task(
            task_id=task_id,
             company_name=db.get_or_404(Company, int(company_name)),
             location=location,
             task_name=task_name,
             staff_pending=engineer_name,
             status='Pending',
             cost=cost,
             payment= payment,
             # "Balance": balance,
            startDate=startDate,
            stopDate=stopDate,
             )
        db.session.add(task_details)
        user = db.get_or_404(User, engineer_name)
        task_key = db.session.query(Task).filter(Task.task_id==task_id).all()[0].id
        if user.pending in (None, "", ' '):
            user.pending = f'{task_key},'
        else:
            user.pending = user.pending + f',{task_key}, '
        db.session.commit()
        flash(f"New Task {task_name} has been Successfully created")
        return redirect(url_for('task_list', company='all-task', status='None'))
    return render_template('addTask.html', form=form, num_mail=mail_counter())




@app.route("/task_details/<task_id>", methods=["GET", "POST"])
@login_required
@member_only
# Displays the task details for members of task
def taskDetails(task_id):
    task = db.get_or_404(Task, int(task_id))
    details = staff_stat(current_user)
    staff = []
    form = CommentForm()
    with app.app_context():
        # posts = db.session.execute(db.select(Comment).where(Comment.task.id == task.id))
        posts = db.session.query(Comment).filter(Comment.task == task.id)
    if task.staff_accepted not in (None, "", ' '):
        ids = task.staff_accepted.split(",")
        ids = [tsk for tsk in ids if tsk.isnumeric()]
        for ppl in ids:
            staff.append({'name': db.get_or_404(User, int(ppl)).id_name, 'status': 'Accepted'})
    if task.staff_pending not in (None, "", ' '):
        ids = task.staff_pending.split(",")
        ids = [tsk for tsk in ids if tsk.isnumeric()]
        for ppl in ids:
            staff.append({'name': db.get_or_404(User, int(ppl)).id_name, 'status': 'Pending'})

    if form.validate_on_submit():
        # author = current_user.id_name
        postdate = datetime.now().strftime("%b %d, %Y %H %m")
        comment = form.comment.data
        new_comment = Comment(author_name=db.get_or_404(User, current_user.id), comment=comment, timing=postdate, task_name=task)
        db.session.add(new_comment)
        db.session.commit()
        flash('Your Comment has been successfully Added')
        return redirect(url_for('taskDetails', task_id=task_id))
    return render_template('taskDetails.html', details=details, task=task, posts=posts, db_head=db_head, task_id=task_id, staff=staff, form=form, num_mail=mail_counter())


@app.route("/edit-task/<taskid>", methods=["GET", "POST"])
@login_required
@admin_only
def editTask(taskid):
    task = db.get_or_404(Task, taskid)
    form = EditTaskDetails()
    if task.staff_accepted is not None:
        accpt_list = task.staff_accepted.split(',')
    else:
        accpt_list = [None]
    if task.staff_pending != None:
        pend_list = task.staff_pending.split(',')
    else:
        pend_list = [None]
    a_p_list = pend_list + accpt_list
    staff_listing = staff_list()
    addable_staffs = [item for item in staff_listing if str(list(item)[0]) not in a_p_list]
    removable_staffs = [item for item in staff_listing if str(list(item)[0]) in a_p_list]
    addable_staffs.append((None, "No Staff Selected"))
    removable_staffs.append((None, "No Staff Selected"))
    removable_staffs.reverse()
    addable_staffs.reverse()
    form.assignStaff.choices = addable_staffs
    form.removeStaff.choices = removable_staffs
    # Handle request
    if request.method == "POST":
        staffs = form.assignStaff.data
        remove_staff = form.removeStaff.data
        money = form.money.data
        if form.status.data in ('Completed', 'Suspended'):
            task.status = form.status.data
            task.stopDate = datetime.now().strftime("%b %d, %Y %H %m")
            db.session.commit()

        else:
            if form.status.data in ('On going', 'Pending'):
                task.status = form.status.data
                task.stopDate = None
            # Add Staff

            if staffs != "None":
                if (task.staff_accepted is None) or (staffs not in task.staff_accepted.split(',')):
                    if (task.staff_pending is None) or (staffs not in task.staff_pending.split(',')):
                        if task.staff_pending in (None, "", ' '):
                            task.staff_pending = f'{str(staffs)}'
                        else:
                            task.staff_pending = task.staff_pending + f',{str(staffs)}'
                        user = db.get_or_404(User, int(staffs))
                        if user.pending in (None, " ", ""):
                            user.pending = f'{str(task.id)}'
                        else:
                            user.pending = user.pending + f',{str(task.id)}'

            # Remove Staff
            if remove_staff != 'None':
                if task.staff_accepted not in (None, "", " "):
                    accepted_staff = task.staff_accepted.split(",")
                    if remove_staff in accepted_staff:
                        accepted_staff.pop(accepted_staff.index(remove_staff))
                        task.staff_accepted = ','.join(accepted_staff)

                if task.staff_pending not in (None,' ', ""):
                    pend_staff = task.staff_pending.split(",")
                    if remove_staff in pend_staff:
                        pend_staff.pop(pend_staff.index(remove_staff))
                        task.staff_pending = ','.join(pend_staff)

                staffer = db.get_or_404(User, int(remove_staff))
                staff_pend = staffer.pending
                staff_accp = staffer.working
                if staff_pend not in (None, "", ' '):
                    staff_pendlist = staff_pend.split(',')
                    if str(task.id) in staff_pendlist:
                        staff_pendlist.pop(staff_pendlist.index(str(task.id)))
                        staffer.pending = ",".join(staff_pendlist)
                if staff_accp not in (None, "", ' '):
                    staff_joblist = staff_accp.split(',')
                    if str(task.id) in staff_joblist:
                        staff_joblist.pop(staff_joblist.index(str(task.id)))
                        staffer.working = ",".join(staff_joblist)

            # Add Amount

            if money is not None:
                task.payment = task.payment + money
            db.session.commit()
            flash(f"Change has been successful made to {task.task_name}!!!")
            return redirect(url_for('taskDetails', task_id=taskid))
    return render_template('edit_details.html', form=form, name=task.task_name, num_mail=mail_counter())


@app.route("/company-list", methods=['GET', 'POST'])
@login_required
@admin_only
# Displays list of companies for the admin accounts
def companyList():
    colhead = ('name', 'location', 'contact name',  'contact number', 'Contact Email')
    with app.app_context():
        data1 = db.session.query(Company).all()

    details = company_taskinfo(data1)
    if request.method == 'POST':
        search_data = request.form.get('search_query')
        search_result = []
        for comp in data1:
            if search_data.upper() in comp.name.upper():
                search_result.append(comp)

        return render_template('companylist.html', info=details, data=search_result, db_head=colhead, webpage='company')
    return render_template('companylist.html', info=details, data=data1, db_head=colhead, webpage='company', num_mail=mail_counter())


@app.route("/add-user", methods=['GET', 'POST'])
@login_required
@admin_only
def addUser():
    form = UserForm()
    if form.validate_on_submit():
        email = form.email.data
        position = form.position.data
        first_name = form.first_name.data
        middle_name = form.middle_name.data
        picture = form.picture.data
        last_name = form.last_name.data
        privilege = form.privilege.data
        password = form.password.data
        password1 = form.password.data
        if password1 != password:
            flash("Password Doesn't Match")
        else:
            password = generate_password_hash(password=password,
                                              method='pbkdf2:sha256',
                                              salt_length=8)

            datab = db.session.query(User).all()
            idname = id_name_generator(first_name, middle_name, last_name, datab)
            new_user = User( email=email,
                            position=position,
                            first_name=first_name,
                            last_name=last_name,
                            id_name= idname,
                            password= password,
                             contract="Active",
                            privilege=privilege,)

            db.session.add(new_user)
            picture = upload_picture(picture, new_user.id_name,app.config['UPLOAD_FOLDER'])
            new_user.picture = picture
            available_work = Calendar(staff=new_user,
                                    start=datetime.now().strftime("%b %d, %Y %H %m"),
                                     status='Available')
                            # calendar= 'Available')
            db.session.add(available_work)
            db.session.commit()
            flash(f'Your {new_user.id_name} has been successfully Created')
            return redirect(url_for("all_staffs", category='None'))
    return render_template('add_user.html', form=form, num_mail=mail_counter())


@app.route("/edit-user/<user_id>", methods=['GET', 'POST'])
@login_required
@admin_only
def editUser(user_id):
    staff = db.get_or_404(User, user_id)
    form = EditUserForm()
    if request.method == 'POST':
        email = form.email.data
        position = form.postion.data
        password = form.password.data
        re_password = form.re_password.data
        status = form.user_status.data
        picture = form.picture.data
        if status == 'Terminated':
            staff.contract = "Terminated"
        else:
            if status == 'Active':
                staff.contract = 'Active'
            if email is not None and email.strip() != '':
                staff.email = email
            if position is not None and position.strip() != '':
                staff.position = position
            if picture is not None:
                picture = upload_picture(picture, staff.id_name, app.config['UPLOAD_FOLDER'])
                staff.picture = picture
            if password is not None and password.strip() != '':
                if password == re_password:
                    password = generate_password_hash(password=password,
                                                      method='pbkdf2:sha256',
                                                      salt_length=8)
                    staff.password = password
                else:
                    flash('Password mismatch')
                    return redirect(url_for('editUser', user_id=user_id))
        flash('Changes were successfully')
        db.session.commit()
        return redirect(url_for('all_staffs', category='None'))
    return render_template('edit_details.html', form=form, name=staff.id_name, num_mail=mail_counter())

@app.route("/edit-company/<company_id>", methods=['GET', 'POST'])
@login_required
@admin_only
def editCompany(company_id):
    company = db.get_or_404(Company, company_id)
    form = EditCompany()
    if request.method == 'POST':
        name = form.name.data
        email = form.email.data
        location = form.location.data
        contact_name = form.contact_name.data
        number = form.number.data

        if name is not None and name.strip() != '':
            company.name = name
        if email is not None and email.strip() != '':
            company.email = email
        if contact_name is not None and email.strip() != '':
            company.contact_name = contact_name
        if location is not None and location.strip() != '':
            company.location = location.strip()
        if number is not None and number.strip() != '':
            company.contact = number.strip()
        flash('Changes were successfully')
        db.session.commit()
        return redirect(url_for('companyList'))
    return render_template('edit_details.html', form=form, name=company.name, num_mail=mail_counter())


@app.route("/request-leave", methods=['GET', 'POST'])
@login_required
def requestLeave():
    if current_user.privilege == 'Staff':
        details = staff_stat(current_user)
    else:
        details = None
    form = LeaveForm()
    if form.validate_on_submit():
        start = form.start_date.data
        end = form.end_date.data
        recipient = db.get_or_404(User,1).id_name
        title = "Request of Leave of Absense"
        message = form.reason.data
        timing = datetime.now().strftime("%b %d, %Y %H %m")
        new_message = Messages(sender=current_user.id_name,
                               receiver=recipient,
                               title=title, timing=timing,
                               message=message)
        db.session.add(new_message)
        leave_request = Calendar(staff=current_user,
                                 start=start.strftime("%b %d, %Y %H %m"),
                                 stop=end.strftime("%b %d, %Y %H %m"),
                                 reason=message,
                                 status='Pending')
        # current_user.calendar = f"Pending, {start}, {end}"
        db.session.add(leave_request)
        db.session.commit()
        flash('Your Leave Request has been been sent!!!')
        return redirect(url_for('staffprofile', staff='None'))
    return render_template('/user/request_leave.html', form=form, num_mail=mail_counter(), details=details)


@app.route("/", methods=['GET', 'POST'])
def user_login():

    form = LoginForm()
    if form.validate_on_submit():
        username = form.email.data
        password_ = form.password.data
        staff = db.session.query(User).filter(User.email == username).all()
        if len(staff)!=0 and check_password_hash(staff[0].password, password_):
            staff = staff[0]
            login_user(staff)
            flash(f'Welcome Back, {staff.id_name}')
            if staff.privilege == 'Staff':
                return redirect(url_for('staffprofile', staff='None'))
            else:
                return redirect(url_for('all_staffs', category='None'))
        else:
            flash("Incorrect Username or Password!!!")
            return redirect(url_for('user_login'))
    return render_template('/login.html', form=form)

@app.route('/logout')
@login_required
def user_logout():
    logout_user()
    return redirect(url_for('user_login'))

@app.route('/staff-profile/<staff>')
@login_required
# Displays a selected staff profile
def staffprofile(staff):
    last_leave = None
    if staff != 'None':
        staff = db.get_or_404(User, int(staff))
        leave_calculator(staff)
        last_leave = staff.calendar[-1]

    else:
        last_leave = current_user.calendar[-1]
    details = staff_stat(current_user)

    return render_template('/user/profile.html', staff=staff, leave=last_leave, num_mail=mail_counter(), details=details)

def delete_(message_id):
    with app.app_context():
        message = db.get_or_404(Messages, int(message_id))
        db.session.delete(message)
        db.session.commit()
        flash("Message has been deleted")
        return redirect(url_for('inbox'))

@app.route('/to-do', methods=['GET', 'POST'])
@login_required
# Where staff could accept or reject a new task
def to_do():
    table_head = ('id', 'company name', 'location', 'task', 'cost')
    project = []
    details = staff_stat(current_user)
    form = AcceptRejectForm()
    if current_user.pending not in (None, ' ', ""):

        ids = current_user.pending.split(",")
        ids = [tsk for tsk in ids if tsk.isnumeric()]
        for tsk in ids:
            project.append(db.get_or_404(Task, int(tsk)))
    if request.method == "POST":
        pick = form.accept.data
        numb = form.task_id.data
        work = db.get_or_404(Task, int(numb))
        if pick == 'Accept':

            if work.staff_accepted in (None, "", ' '):
                work.staff_accepted = f'{str(current_user.id)}'
                work.status = "On going"
            else:
                work.staff_accepted = work.staff_accepted + f',{str(current_user.id)}'
            if current_user.working in (None, "", ' '):
                current_user.working = f'{str(work.id)}'
            else:
                current_user.working = current_user.working + f',{str(work.id)}'
        else:
            if work.staff_rejected in (None, "", ' '):
                work.staff_rejected = f'{str(work.id)}'
            else:
                work.staff_rejected = work.staff_rejected + f',{str(work.id)}'


            if current_user.reject in (None, "", ' '):
                current_user.reject = f'{str(work.id)}'
            else:
                current_user.reject = current_user.reject + f',{str(current_user.id)}'
        # if current_user.pending
        ids.pop(ids.index(str(numb)))
        current_user.pending = ",".join(ids)
        new_pend = work.staff_pending.split(",")
        new_pend.pop(new_pend.index(str(current_user.id)))
        work.staff_pending = ",".join(new_pend)
        db.session.commit()
        flash(f"You have {pick}ed: {work.task_name} Task!!")
        return redirect(url_for('to_do'))
    return render_template('/user/todo.html', table_head=table_head, details = staff_stat(current_user),  task=project, form=form, num_mail=mail_counter())

@app.route("/taskboard/<status>", methods=['POST', 'GET'])
@login_required
# Display details on all the accepted task for staff account
def taskboard(status):
    data1 = []
    details = staff_stat(current_user)
    with app.app_context():
        taskss = current_user.working
    if taskss is not None:
        taskss = taskss.split(",")
        for tsk in taskss:
            if tsk.isnumeric():
                data1.append(db.get_or_404(Task, int(tsk)))
    info = task_info(data1)
    if status != 'None':
        data1 = details[status][0]
    if request.method == 'POST':
        search_data = request.form.get('search_query')
        search_result = []
        for comp in data1:
            if search_data.upper() in comp.task_name.upper():
                search_result.append(comp)
            elif search_data.upper() in comp.task_id.upper():
                search_result.append(comp)
            elif search_data.upper() in comp.location.upper():
                search_result.append(comp)
        return render_template('home.html', data=search_result, comp=info, details=details, db_head=db_head, remove=indeptDetails, webpage='taskboard', num_mail=mail_counter())
    return render_template('home.html', data=data1, db_head=db_head,comp=info, details=details, remove=indeptDetails, webpage='taskboard', num_mail=mail_counter())

@app.route("/accept-leave/<option>")
@login_required
@admin_only
def accept_leave(option):
    with app.app_context():
        users = db.session.query(User).filter(User.id_name==option)[0]
        last_leave = users.calendar[-1]
        last_leave.status = 'Approved'
        timing = datetime.now().strftime("%b %d, %Y %H %m")
        title = "Approval of Leave Request"
        msg = f"""Good Day,
                        Your request of leave, starting on {last_leave.start} to {last_leave.stop},
                        has been approved, Thank you"""
        new_message = Messages(sender=current_user.id_name,
                                   receiver=users.id_name,
                                   title=title, timing=timing,
                                   message=msg)
        db.session.add(new_message)
        db.session.commit()
        flash(f'You have Approved the Leave Request of {users.id_name}')
    return redirect(url_for("inbox"))

@app.route("/deny-leave/<option>")
@login_required
@admin_only
def reject_leave(option):
    with app.app_context():
        users = db.session.query(User).filter(User.id_name==option)[0]
        last_leave = users.calendar[-1]
        timing = datetime.now().strftime("%b %d, %Y %H %m")
        title = "Approval of Leave Request"
        msg = f"""Good Day,
                        Your request of leave, starting on {last_leave.start} to {last_leave.stop},
                        has been denied, Thank you"""
        new_message = Messages(sender=current_user.id_name,
                               receiver=users.id_name,
                               title=title, timing=timing,
                               message=msg)
        db.session.delete(last_leave)
        db.session.add(new_message)
        db.session.commit()
        flash(f'You have Denied the Leave Request of {users.id_name}')
        return redirect(url_for("inbox"))


@app.route('/inbox', methods=['POST', 'GET'])
@login_required
def inbox():
    heading = ['Sender', "Title", "Date"]
    with app.app_context():
        data1 = db.session.query(Messages).filter(Messages.receiver==current_user.id_name)[::-1]
    details = staff_stat(current_user)
    if request.method == 'POST':
        search_data = request.form.get('search_query')
        search_result = []
        for comp in data1:
            if search_data.upper() in comp.sender.upper():
                search_result.append(comp)
            elif search_data.upper() in comp.title.upper():
                search_result.append(comp)
            elif search_data.upper() in comp.timing.upper():
                search_result.append(comp)
        return render_template('/message/messagelist.html', head=heading,details=details, messages=search_result, webpage='inbox', num_mail=mail_counter())
    return render_template('/message/messagelist.html',details=details,  head=heading, messages=data1, webpage='inbox', num_mail=mail_counter())

@app.route('/outbox', methods=['POST', 'GET'])
@login_required
def outbox():
    heading = ['recipient', "Title", "Date"]
    with app.app_context():
        data1 = db.session.query(Messages).filter(Messages.sender == current_user.id_name)[::-1]
    details = staff_stat(current_user)
    if request.method == 'POST':
        search_data = request.form.get('search_query')
        search_result = []
        for comp in data1:
            if search_data.upper() in comp.receiver.upper():
                search_result.append(comp)
            elif search_data.upper() in comp.title.upper():
                search_result.append(comp)
            elif search_data.upper() in comp.timing.upper():
                search_result.append(comp)
        return render_template('/message/messagelist.html', head=heading, details=details, messages=search_result, webpage='outbox', num_mail=mail_counter())
    return render_template('/message/messagelist.html', details=details, head=heading, messages=data1, webpage='outbox', num_mail=mail_counter())

@app.route('/read-message/<msg>')
@login_required
# read or delete messages and Admin account could accept or reject leave
def read_message(msg):
    with app.app_context():
        message = db.get_or_404(Messages, msg)
        sender = db.session.query(User).filter(User.id_name==message.sender)[0]
        if not(message.read):
            message.read = True
            db.session.commit()
    message = db.get_or_404(Messages, msg)
    details = staff_stat(current_user)
    return render_template('/message/viewmessage.html', message=message, details=details, sender=sender, num_mail=mail_counter())


@app.route('/compose-message/<recipient>', methods=['GET','POST'])
@login_required
def compose_message(recipient):
    form = MessageForm()
    details = staff_stat(current_user)
    if recipient != 'None':
        form.recipient.do_not_call_in_templates = True
    if form.validate_on_submit():
        if recipient == 'None':
            recipient = form.recipient.data
        title = form.title.data
        message = form.message.data

        timing = datetime.now().strftime("%b %d, %Y %H %m")
        all_user = db.session.query(User).all()
        mails = [user.id_name.upper() for user in all_user]
        if recipient.upper() in mails:
            new_message = Messages(sender=current_user.id_name,
                                   receiver=recipient,
                                   title=title, timing=timing,
                                   message=message)
            db.session.add(new_message)
            db.session.commit()
            flash('Your Message has been sent Successfully!!!')
            return redirect(url_for('compose_message', recipient='None'))
    return render_template('/message/compose.html', details=details, form=form, num_mail=mail_counter())



if __name__ == '__main__':
    app.run(debug=False)
