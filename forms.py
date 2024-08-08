from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TimeField, DateField, TextAreaField, FileField, BooleanField
from wtforms.validators import InputRequired, Length, EqualTo, Email

class SignUp(FlaskForm):
    Username = StringField(
        "Username", validators=[InputRequired(), Length(min=5, max=16)], render_kw={"class":"formdata"}
    )
    First_Name = StringField("First Name", validators=[InputRequired(), Length(max=100)], render_kw={"class":"formdata"})
    Last_Name = StringField("Last Name", validators=[InputRequired(), Length(max=100)], render_kw={"class":"formdata"})
    Phone = StringField("Phone Number", validators=[InputRequired(), Length(min=10, max=10)], render_kw={"class":"formdata"})
    Email = StringField("Email", validators=[InputRequired(), Email(message="Must be a Valid Email Address"), Length(max=100)], render_kw={"class":"formdata"})
    Password = PasswordField(
        "Password", validators=[InputRequired(), EqualTo("Confirm_Password", message="Passwords Must Match"), Length(min=8)], render_kw={"class":"formdata"}
    )
    Confirm_Password = PasswordField(
        "Confirm Password", validators=[InputRequired(), Length(min=8)], render_kw={"class":"formdata"}
    )
    Role = SelectField("Role", choices=[('organizer', 'Organizer'), ('attendee', 'Attendee')], validators=[InputRequired()], render_kw={"class":"formdata"})
    # done using gpt
    Submit = SubmitField(label=('Submit'), render_kw={"class":"submit"})

class SignIn(FlaskForm):
    UsernameorEmail = StringField("UsernameorEmail", validators=[InputRequired(), Length(max=100)])
    Password = PasswordField("Password", validators=[InputRequired(), Length(min=8, max=30)])
    Submit = SubmitField(label=('Submit'))

class CreateEvent(FlaskForm):
    Index = StringField("Event Index", validators=[InputRequired()], render_kw={"readonly": True, "style": "display:none", "value": "0"})
    EventName = StringField("Event Name", validators=[InputRequired()], render_kw={"class":"formdata"})
    EventLocation = StringField("Event Location", validators=[InputRequired()], render_kw={"class":"formdata"})
    EventStartDate = DateField("Event Start Date", validators=[InputRequired()], render_kw={"class":"formdata"})
    EventStartTime = TimeField("Event Start Time", validators=[InputRequired()], render_kw={"class":"formdata"})
    EventEndDate = DateField("Event End Date", validators=[InputRequired()], render_kw={"class":"formdata"})
    EventEndTime = TimeField("Event End Time", validators=[InputRequired()], render_kw={"class":"formdata"})
    EventCategory = StringField("Event Category", validators=[InputRequired()], render_kw={"class":"formdata"})
    EventDescription = TextAreaField("Event Description", validators=[InputRequired()], render_kw={"class":"formdata", "rows":10, "cols":10})
    EventSeats = StringField("Event Total Seats", validators=[InputRequired()], render_kw={"class":"formdata"})
    EventBanner = FileField("Event Banner", render_kw={"class":"formdata"})
    Submit = SubmitField(label=('Submit'), render_kw={"class":"formdata"})

class DisplayEvents(FlaskForm):
    Index = StringField("Index", validators=[InputRequired()], render_kw={"readonly": True, "style": "display:none"})
    EventName = StringField("Event Name", validators=[InputRequired()], render_kw={"readonly": True, "class":"formdata"})
    EventLocation = StringField("Event Location", validators=[InputRequired()], render_kw={"readonly": True, "class":"formdata"})
    EventStart  = StringField("Event Start Date", validators=[InputRequired()], render_kw={"readonly": True, "class":"formdata"})
    EventEnd = StringField("Event End Date", validators=[InputRequired()], render_kw={"readonly": True, "class":"formdata"})
    EventCategory = StringField("Event Category", validators=[InputRequired()], render_kw={"readonly": True, "class":"formdata"})
    EventSeats = StringField("Event Seats Left", validators=[InputRequired()], render_kw={"class":"formdata"})
    Register = SubmitField(label=('Register'), render_kw={"class":"formdata"})
    ShowQR = SubmitField(label=('Show QR'), render_kw={"class":"formdata"})
    Manage = SubmitField(label=('Manage'), render_kw={"class":"formdata"})

class RegisterEvents(FlaskForm):
    Index = StringField("Index", validators=[InputRequired()], render_kw={"readonly": True, "style": "display:none"})
    EventName = StringField("Event Name", validators=[InputRequired()], render_kw={"readonly": True, "class":"formdata"})
    EventLocation = StringField("Event Location", validators=[InputRequired()], render_kw={"readonly": True, "class":"formdata"})
    EventStart  = StringField("Event Start Date", validators=[InputRequired()], render_kw={"readonly": True, "class":"formdata"})
    EventEnd = StringField("Event End Date", validators=[InputRequired()], render_kw={"readonly": True, "class":"formdata"})
    EventCategory = StringField("Event Category", validators=[InputRequired()], render_kw={"readonly": True, "class":"formdata"})
    EventSeats = StringField("Event Seats Left", validators=[InputRequired()], render_kw={"class":"formdata"})
    CalenderIntegration = BooleanField("Calender Integration", render_kw={"class":"formdata"})
    ConfirmRegister = SubmitField(label=('Confirm Registration'), render_kw={"class":"formdata"})

class ManageEvents(FlaskForm):
    Index = StringField("Index", validators=[InputRequired()], render_kw={"readonly": True, "style": "display:none"})
    EventName = StringField("Event Name", validators=[InputRequired()], render_kw={"readonly": True, "class":"formdata"})
    EventLocation = StringField("Event Location", validators=[InputRequired()], render_kw={"readonly": True, "class":"formdata"})
    EventStart  = StringField("Event Start Date", validators=[InputRequired()], render_kw={"readonly": True, "class":"formdata"})
    EventEnd = StringField("Event End Date", validators=[InputRequired()], render_kw={"readonly": True, "class":"formdata"})
    EventCategory = StringField("Event Category", validators=[InputRequired()], render_kw={"readonly": True, "class":"formdata"})
    EventSeats = StringField("Event Seats Left", validators=[InputRequired()], render_kw={"readonly": True, "class":"formdata"})
    Edit = SubmitField(label=('Edit'), render_kw={"class":"formdata"})
    Delete = SubmitField(label=('Delete'), render_kw={"class":"formdata"})
    
class QRSend(FlaskForm):
    QR = StringField("QR Code", validators=[InputRequired()], render_kw={"readonly": True, "class":"formdata", "id":"QR", "style":"display: none;"})
    Send = SubmitField(label=('Send'), render_kw={"class":"formdata", "id":"sendButton", "style":"display: none;"})

