#                                                  Form sections
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SubmitField, FileField, SelectField, IntegerField, EmailField, DateField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileAllowed
from flask_ckeditor import CKEditorField

class CompanyForm(FlaskForm):
    name = StringField(label="Company Name", validators=[DataRequired()])
    location = StringField(label="Company Location", validators=[DataRequired()])
    contact_name = StringField(label="Contact Name", validators=[DataRequired()])
    contact = StringField(label="Contact Number", validators=[DataRequired()])
    mail = StringField(label="Email", validators=[DataRequired()])
    submit = SubmitField(label="Submit")


class TaskForm(FlaskForm):
    task_name = StringField(label='Task Name', validators=[DataRequired()])
    company_name = SelectField(u'select company')
    location = StringField(label='Task Location', validators=[DataRequired()])
    engineer_name = SelectField(u'Assign staff')
    # status = StringField(label='Status', validators=[DataRequired()])
    startDate = DateField(label='Start Date', validators=[DataRequired()])
    # status = StringField(label='status', validators=[DataRequired()])
    # progress = StringField(label='progress', validators=[DataRequired()])
    cost = IntegerField(label='Cost', validators=[DataRequired()])
    payment = IntegerField(label='Payment', default=0)
    submit = SubmitField(label="Submit")


class UserForm(FlaskForm):
    email = EmailField(label='Email Address', validators=[DataRequired(), ])
    position = StringField(label='Position')
    first_name = StringField(label='First Name', validators=[DataRequired()])
    middle_name = StringField(label='Middle Name', default=None)
    last_name = StringField(label='Last Name', validators=[DataRequired()])
    privilege = SelectField(u'Select Account Type', choices=['Administrator', 'Staff'])
    picture = FileField(label='Profile Picture', validators=[FileAllowed(['png', 'jpg'])], default='profilepic.png')
    password = PasswordField(label='Password', validators=[DataRequired(), Length(min=8, max=16)])
    password1 = PasswordField(label='Retype Password', validators=[DataRequired(), Length(min=8, max=16)])
    submit = SubmitField(label="Submit")


class LeaveForm(FlaskForm):
    start_date = DateField(label="Start Of Leave", validators=[DataRequired()])
    end_date = DateField(label="End Of Leave", validators=[DataRequired()])
    reason = CKEditorField(label='Reason for leave', validators=[DataRequired()])
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
    accept = SelectField(u'Accept or Reject', choices=['Accept', "Reject"], default='Accept', validators=[DataRequired()])
    task_id = IntegerField()
    submit = SubmitField('Submit')

class CommentForm(FlaskForm):
    comment = TextAreaField(label="Comment", validators=[DataRequired()])
    submit = SubmitField(label='Post')

class MessageForm(FlaskForm):
    recipient = StringField(label="ID Name", validators=[DataRequired()])
    title = StringField(label='Message Title', validators=[DataRequired()])
    message = CKEditorField(label='Message Body', validators=[DataRequired()])
    submit = SubmitField(label='Send Message')

class EditUserForm(FlaskForm):
    email = EmailField(label='New Email Address')
    postion = StringField(label='New Position')
    picture = FileField(label='Profile Picture', validators=[FileAllowed(['png', 'jpg'])])
    password = PasswordField(label='Enter New Password', validators=[Length(min=8, max=16)])
    re_password = PasswordField(label='Confirm New Password', validators=[Length(min=8, max=16)])
    user_status = SelectField(u'Select Employee Status', choices=['No Changes', 'Terminated', 'Active'])
    submit = SubmitField(label='Update Details')

class EditCompany(FlaskForm):
    name = StringField(label='New Company Name')
    email = EmailField(label='New Email Address')
    number = StringField(label='New Phone Number')
    contact_name = StringField(label='New Contact Name')
    location = StringField(label='New location')
    submit = SubmitField(label='Update Details')

