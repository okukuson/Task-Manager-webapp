from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_wtf import FlaskForm
from wtforms import StringField,TextAreaField, PasswordField, SubmitField, SelectField, IntegerField, EmailField, DateField
from wtforms.validators import DataRequired, Email
from functionality import *
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
bootstrap = Bootstrap5()
bootstrap.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)


app.secret_key = "secret key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///web_app_database.db'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy()
db.init_app(app)

# company = []
task_details = []
indeptDetails = ("location", "staff", "payment", "confirm", "start", "end")
users = []
########################## DATABASE TABLE


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(30), unique=True, nullable=False)
    position = db.Column(db.String(30),  nullable=False)
    privilege = db.Column(db.String(30),  nullable=False)
    first_name = db.Column(db.String(30),  nullable=False)
    last_name = db.Column(db.String(30),  nullable=False)
    id_name = db.Column(db.String(30),  nullable=False)
    password = db.Column(db.String(30), nullable=False)
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

    # mail_add = db.Column(db.Integer, db.ForeignKey('users.id'))
    sender = db.Column(db.String(30), nullable=False)
    receiver = db.Column(db.String(30), nullable=False)

    # relationship("User", back_populates='msg_from', lazy='subquery')
    # relationship("User", back_populates='msg_to', lazy='subquery')

    timing = db.Column(db.String(30), nullable=False)
    title = db.Column(db.String(30), nullable=False)
    message = db.Column(db.String(500), nullable=False)



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
            # calendar= 'Available')


#                                              Helper function


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


def populate_choice():
    # gets a list of each company's id and name
    with app.app_context():
        # db.session.execute(db.Select(Company).())
        companys = db.session.query(Company).all()
    if len(companys) == 0:
        return ['No company']
    else:
        return [(company.id, company.name) for company in companys]

def staff_list():
    # gets a list of each staff's id and name
    with app.app_context():
        users = db.session.query(User).all()
    if len(users) <= 1:
        return ['No Staff']
    else:
        return [(staff.id, staff.id_name) for staff in users if (staff.contract == 'Active' and staff.id != 1)]




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
        print(current_user.privilege)
        task = db.get_or_404(Task, int(task_id))
        if current_user.privilege != 'Administrator':
            if str(current_user.id) not in task.staff_accepted.split(','):
                return abort(403)
        return f(task_id)
    return decorated_function

def leave_calculator(staff):
    if len(staff.calendar) > 0 and staff.calendar[-1].stop is not None:
        calendar = staff.calendar[-1]
        print(calendar.stop)
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

class MyForm(FlaskForm):
    name = StringField(label="Name", validators=[DataRequired()])
    location = StringField(label="Location", validators=[DataRequired()])
    contact = StringField(label="Contact", validators=[DataRequired()])
    mail = StringField(label="Email", validators=[DataRequired()])
    submit = SubmitField(label="Submit")


class TaskForm(FlaskForm):
    task_name = StringField(label='Task Name', validators=[DataRequired()])
    company_name = SelectField(u'select company')
    location = StringField(label='Task Location', validators=[DataRequired()])
    engineer_name = SelectField(u'Assign staff')
    # status = StringField(label='Status', validators=[DataRequired()])
    startDate = DateField(label='Start Date', validators=[DataRequired()])
    status = StringField(label='status', validators=[DataRequired()])
    # progress = StringField(label='progress', validators=[DataRequired()])
    cost = IntegerField(label='Cost', validators=[DataRequired()])
    payment = IntegerField(label='Payment', default=0)
    submit = SubmitField(label="Submit")


class UserForm(FlaskForm):
    email = EmailField(label='Email Address', validators=[DataRequired(), ])
    position = StringField(label='Position')
    first_name = StringField(label='First Name', validators=[DataRequired()])
    last_name = StringField(label='Last Name', validators=[DataRequired()])
    privilege = SelectField(u'Select Account Type', choices=['Administrator', 'Staff'])
    password = PasswordField(label='Password', validators=[DataRequired()])
    password1 = PasswordField(label='Retype Password', validators=[DataRequired()])
    submit = SubmitField(label="Submit")


class LeaveForm(FlaskForm):
    start_date = DateField(label="Start Of Leave", validators=[DataRequired()])
    end_date = DateField(label="End Of Leave", validators=[DataRequired()])
    reason = TextAreaField(label='Reason for leave', validators=[DataRequired()])
    submit = SubmitField(label="Submit")

class EditTaskDetails(FlaskForm):
    assignStaff = SelectField(u'add staff', default=None)
    removeStaff = SelectField(u'remove staff', default=None)
    money = IntegerField(label='Amount Paid', default=0)
    status = SelectField(u'Change Task Status', choices=['No Action Selected', 'Suspended', 'Completed', 'On going', 'Pending'])
    submit = SubmitField(label="Save Changes")

class LoginForm(FlaskForm):
    email = EmailField(label="Email Address", validators=[DataRequired()])
    password = PasswordField(label="Password", validators=[DataRequired()])
    submit = SubmitField(label="login")


class AcceptRejectForm(FlaskForm):
    accept = SelectField(u'Accept or Reject', choices=['Accept', "Reject"], validators=[DataRequired()])
    task_id = IntegerField()
    submit = SubmitField('Submit')

class CommentForm(FlaskForm):
    # comment_author = pass
    comment = TextAreaField(label="Comment",validators=[DataRequired()])
    submit = SubmitField(label='Post')

class MessageForm(FlaskForm):
    recipient = EmailField(label="Email Address", validators=[DataRequired()])
    title = StringField(label='Message Title', validators=[DataRequired()])
    message = TextAreaField(label='Message Body', validators=[DataRequired()])
    submit = SubmitField(label='Send Message')

class EditUserForm(FlaskForm):
    email = EmailField(label='New Email Address')
    postion = StringField(label='New Position')
    password = PasswordField(label='Enter New Password')
    re_password = PasswordField(label='Confirm New Password')
    user_status = SelectField(u'Select Employee Status', choices=['No Changes', 'Terminated', 'Active'])
    submit = SubmitField(label='Update Details')

class EditCompany(FlaskForm):
    email = EmailField(label='New Email Address')
    number = StringField(label='New Phone Number')
    location = StringField(label='New location')
    submit = SubmitField(label='Update Details')



db_head = ["id", 'company name', "location", 'task', "assign", 'cost', "payment", "Balance", "start", "status",
           "confirm"]

#                                      Route Section
@app.route("/<company>", methods=['POST', 'GET'])
@login_required
@admin_only
def task_list(company):
    with app.app_context():
        if company == 'all-task':
            data1 = db.session.query(Task).all()
        else:
            data1 = db.session.query(Task).filter(Task.company_id==company)
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
        return render_template('home.html', data=search_result, db_head=db_head, remove=indeptDetails, webpage='task')
    return render_template('home.html', data=data1, db_head=db_head, remove=indeptDetails, webpage='task')

@app.route('/all-staffs', methods=['POST', 'GET'])
@login_required
@admin_only
def all_staffs():
    with app.app_context():
        data1 = db.session.query(User).filter(User.id != 1)
        for staff in data1:
            print(staff.id_name)
            update = leave_calculator(staff)
            if update:
                db.session.add(update)
        db.session.commit()
        data1 = db.session.query(User).filter(User.id != 1)

    if request.method == 'POST':
        search_data = request.form.get('search_query')
        print(search_data)
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
        return render_template('all_staffs.html', staffs=search_result, webpage='staff')
    return render_template('all_staffs.html', staffs=data1, webpage='staff')

@app.route('/add-company', methods=['GET', 'POST'])
@login_required
@admin_only
def addCompany():
    print(current_user.privilege)
    form = MyForm()
    if form.validate_on_submit():

        name = form.name.data
        location = form.location.data
        contact = form.contact.data
        mail = form.mail.data
        newcompany = Company(name=name, location=location, contact=contact, mail=mail)
        db.session.add(newcompany)
        db.session.commit()
        print("Success!!!")

    return render_template('add_company.html', form=form)


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
        print(user.id_name)
        task_key = db.session.query(Task).filter(Task.task_id==task_id).all()[0].id
        print(task_key)
        if user.pending in (None, "", ' '):
            print('None')
            user.pending = f'{task_key},'
        else:
            user.pending = user.pending + f',{task_key}, '
            print('hello')
        db.session.commit()
        # print(task_key)
        # assigntask(engineer_name, task_id)
    #     for task in task_details:
    #         print(task['task'])
    # print(task_details)
    return render_template('addTask.html', form=form)




@app.route("/task_details/<task_id>", methods=["GET", "POST"])
@login_required
@member_only
def taskDetails(task_id):
    task = db.get_or_404(Task, int(task_id))

    staff = []
    form = CommentForm()
    with app.app_context():
        # posts = db.session.execute(db.select(Comment).where(Comment.task.id == task.id))
        posts = db.session.query(Comment).filter(Comment.task == task.id)
    print(type(posts))
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
    return render_template('taskDetails.html', details=task, posts=posts, db_head=db_head, task_id=task_id, staff=staff, form=form)


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
        # print(staffs)
        # print(remove_staff)
        # print(money)
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
                        print(user.pending)
                        if user.pending in (None, " ", ""):
                            user.pending = f'{str(task.id)}'
                        else:
                            user.pending = user.pending + f',{str(task.id)}'

            # Remove Staff
            print(remove_staff)
            if remove_staff != 'None':
                print('entered')
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


            # staffs = form.assignStaff.data
            # if staffs not in task.staff_pending.split(','):
            #     if (task.staff_accepted is None) or (staffs not in task.staff_accepted.split(',')):
            #         task.staff_pending = task.staff_pending + f',{staffs},'
            #         user = db.get_or_404(User, int(staffs))
            #         if user.pending in (None, ""):
            #             user.pending = f'{str(task.id)}'
            #         else:
            #             user.pending = user.pending + f',{str(task.id)}'
            # if form.money.data > 0:
            #     task.payment = task.payment + form.money.data
            db.session.commit()
            flash("Change has been successful")
            return redirect(url_for('taskDetails', task_id=taskid))
    return render_template('edittask.html', form=form, taskid=taskid)


@app.route("/company-list", methods=['GET', 'POST'])
@login_required
@admin_only
def companyList():
    colhead = ('name', 'location', 'contact', 'mail')
    with app.app_context():
        data1 = db.session.query(Company).all()
    if request.method == 'POST':
        search_data = request.form.get('search_query')
        search_result = []
        for comp in data1:
            if search_data.upper() in comp.name.upper():
                search_result.append(comp)
        return render_template('companylist.html', data=search_result, db_head=colhead, webpage='company')
    return render_template('companylist.html', data=data1, db_head=colhead, webpage='company')


@app.route("/add-user", methods=['GET', 'POST'])
# @login_required
# @admin_only
def addUser():
    form = UserForm()
    if form.validate_on_submit():
        email = form.email.data
        position = form.position.data
        first_name = form.first_name.data
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
            new_user = User( email=email,
                            position=position,
                            first_name=first_name,
                            last_name=last_name,
                            id_name= f'{first_name[0]}.{last_name}',
                            password= password,
                             contract="Active",
                            privilege=privilege,)
            db.session.add(new_user)

            available_work = Calendar(staff=new_user,
                                     start= datetime.now().strftime("%b %d, %Y %H %m"),
                                     # stop=end,
                                     # reason=message,
                                     status='Available')
                            # calendar= 'Available')
            # db.session.add(new_user)
            db.session.add(available_work)
            db.session.commit()
    return render_template('add_user.html', form=form)


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
        print(password)
        if status == 'Terminated':
            staff.contract = "Terminated"
        else:
            if status == 'Active':
                staff.contract = 'Active'
            if email is not None and email.strip() != '':
                staff.email = email
            if position is not None and position.strip() != '':
                staff.position = position
            if password is not None and password.strip() != '':
                if password == re_password:
                    staff.password = password
                else:
                    flash('Password mismatch')
                    return redirect(url_for('editUser', user_id=user_id))
        flash('Changes were successfully')
        db.session.commit()
        return redirect(url_for('all_staffs'))
    return render_template('edit_details.html', form=form, name=staff.id_name)

@app.route("/edit-company/<company_id>", methods=['GET', 'POST'])
@login_required
@admin_only
def editCompany(company_id):
    company = db.get_or_404(Company, company_id)
    form = EditCompany()
    if request.method == 'POST':
        email = form.email.data
        location = form.location.data
        number = form.number.data

        if email is not None and email.strip() != '':
            company.email = email
        if location is not None and location.strip() != '':
            company.location = location.strip()
        if number is not None and number.strip() != '':
            company.contact = number.strip()
        flash('Changes were successfully')
        db.session.commit()
        return redirect(url_for('companyList'))
    return render_template('edit_details.html', form=form, name=company.name)


@app.route("/request-leave", methods=['GET', 'POST'])
@login_required
def requestLeave():
    form = LeaveForm()
    print(form.validate_on_submit())
    if form.validate_on_submit():
        start = form.start_date.data
        end = form.end_date.data
        recipient = db.get_or_404(User,1).email
        title = "Request of Leave of Absense"
        message = form.reason.data
        timing = datetime.now().strftime("%b %d, %Y %H %m")
        new_message = Messages(sender=current_user.email,
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
    return render_template('/user/request_leave.html', form=form)


@app.route("/", methods=['GET', 'POST'])
def user_login():

    form = LoginForm()
    if form.validate_on_submit():
        staff = db.session.query(User).filter(User.email == form.email.data)[0]
        print(staff.password)
        password_ = form.password.data
        if check_password_hash(staff.password, password_):
            login_user(staff)
            if staff.privilege == 'Staff':
                return redirect(url_for('staffprofile', staff='None'))
            else:
                return redirect(url_for('all_staffs'))
    return render_template('/login.html', form=form)

@app.route('/logout')
@login_required
def user_logout():
    logout_user()
    return redirect(url_for('user_login'))

@app.route('/staff-profile/<staff>')
@login_required
def staffprofile(staff):
    last_leave = None
    if staff != 'None':
        staff = db.get_or_404(User,int(staff))
        leave_calculator(staff)
        last_leave = staff.calendar[-1]
        # last_req = 0
        # for leave in calend:
        #     if leave.id > last_req:
        #         last_req = leave.id
        #         last_leave = leave
    else:
        last_leave = current_user.calendar[-1]
        # last_req = 0
        # for leave in calend:
        #     if leave.id > last_req:
        #         last_req = leave.id
        #         last_leave = leave
    return render_template('/user/profile.html', staff=staff, leave=last_leave)

def delete_(message_id):
    with app.app_context():
        message = db.get_or_404(Messages, int(message_id))
        db.session.delete(message)
        db.session.commit()
        return url_for('inbox')

@app.route('/to-do', methods=['GET', 'POST'])
@login_required
def to_do():
    table_head = ('id', 'company name', 'location', 'task', 'cost')
    project = []
    form = AcceptRejectForm()
    if current_user.pending not in (None, ' ', ""):

        ids = current_user.pending.split(",")
        ids = [tsk for tsk in ids if tsk.isnumeric()]
        for tsk in ids:
            project.append(db.get_or_404(Task, int(tsk)))
    # print(project)
    if request.method == "POST":
        pick = form.accept.data
        numb = form.task_id.data
        work = db.get_or_404(Task, int(numb))
        if pick == 'Accept':

            if work.staff_accepted in (None, "", ' '):
                print("success")
                print(work.staff_accepted)
                print(f'{str(current_user.id)}')
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
        return redirect(url_for('to_do'))
    return render_template('/user/todo.html', table_head=table_head, task=project, form=form)

@app.route("/taskboard", methods=['POST', 'GET'])
@login_required
def taskboard():
    data1 = []
    with app.app_context():
        taskss = current_user.working
    if taskss is not None:
        taskss = taskss.split(",")
        for tsk in taskss:
            if tsk.isnumeric():
                data1.append(db.get_or_404(Task, int(tsk)))
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
        return render_template('home.html', data=search_result, db_head=db_head, remove=indeptDetails, webpage='taskboard')
    return render_template('home.html', data=data1, db_head=db_head, remove=indeptDetails, webpage='taskboard')

@app.route("/accept-leave/<option>")
@login_required
@admin_only
def accept_leave(option):

    with app.app_context():
        users = db.session.query(User).filter(User.email==option)[0]
        last_leave = users.calendar[-1]
        last_leave.status = 'Approved'
        timing = datetime.now().strftime("%b %d, %Y %H %m")
        title = "Approval of Leave Request"
        msg = f"""Good Day,
                        Your request of leave, starting on {last_leave.start} to {last_leave.stop},
                        has been approved, Thank you"""
        new_message = Messages(sender=current_user.email,
                                   receiver=users.email,
                                   title=title, timing=timing,
                                   message=msg)
        db.session.add(new_message)
        db.session.commit()
    return redirect(url_for("inbox"))

@app.route("/deny-leave/<option>")
@login_required
@admin_only
def reject_leave(option):
    with app.app_context():
        users = db.session.query(User).filter(User.email==option)[0]
        last_leave = users.calendar[-1]
        # last_req = 0
        # for leave in calend:
        #     if leave.id > last_req:
        #         last_req = leave.id
        #         last_leave = leave
        # last_leave.status = 'Available'
        timing = datetime.now().strftime("%b %d, %Y %H %m")
        title = "Approval of Leave Request"
        msg = f"""Good Day,
                        Your request of leave, starting on {last_leave.start} to {last_leave.stop},
                        has been denied, Thank you"""
        new_message = Messages(sender=current_user.email,
                               receiver=users.email,
                               title=title, timing=timing,
                               message=msg)
        db.session.delete(last_leave)
        db.session.add(new_message)
        db.session.commit()
        return redirect(url_for("inbox"))


@app.route('/inbox', methods=['POST', 'GET'])
@login_required
def inbox():
    heading = ['Sender', "Title", "Date"]
    with app.app_context():
        data1 = db.session.query(Messages).filter(Messages.receiver==current_user.email)[::-1]

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
        return render_template('/message/messagelist.html', head=heading, messages=search_result, webpage='inbox')
    return render_template('/message/messagelist.html', head=heading, messages=data1, webpage='inbox')

@app.route('/outbox', methods=['POST', 'GET'])
@login_required
def outbox():
    heading = ['recipient', "Title", "Date"]
    with app.app_context():
        data1 = db.session.query(Messages).filter(Messages.sender == current_user.email)[::-1]
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
        return render_template('/message/messagelist.html', head=heading, messages=search_result, webpage='outbox')
    return render_template('/message/messagelist.html', head=heading, messages=data1, webpage='outbox')

@app.route('/read-message/<msg>')
@login_required
def read_message(msg):
    # print(msg)
    message = db.get_or_404(Messages, int(msg))
    sender = db.session.query(User).filter(User.email==message.sender)[0]
    return render_template('/message/viewmessage.html', message=message, sender=sender)


@app.route('/compose-message/<recipient>', methods=['GET','POST'])
@login_required
def compose_message(recipient):
    form = MessageForm()
    if recipient != 'None':
        print(recipient)
        form.recipient.do_not_call_in_templates = True
    if form.validate_on_submit():
        if recipient == 'None':
            recipient = form.recipient.data
        title = form.title.data
        message = form.message.data
        timing = datetime.now().strftime("%b %d, %Y %H %m")
        all_user = db.session.query(User).all()
        mails = [user.email for user in all_user]
        if recipient in mails:
            new_message = Messages(sender=current_user.email,
                                   receiver=recipient,
                                   title=title, timing=timing,
                                   message=message)
            db.session.add(new_message)
            db.session.commit()
    return render_template('/message/compose.html', form=form)



if __name__ == '__main__':
    app.run()
