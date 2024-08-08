from flask import Flask, request, render_template, redirect, url_for, session
from util import dateconv, get_location_name, create_google_calendar_event, qrcodeticket, update_google_calendar_event, delete_google_calendar_event
from datetime import datetime, time
from flask_socketio import SocketIO, emit
import os
from forms import SignUp, SignIn, CreateEvent, DisplayEvents, RegisterEvents, ManageEvents, QRSend
from databaseManagement import DB
from cryptography.fernet import Fernet
from constants import FLASK_SECRET_KEY, PASSWORD_SALT, GOOGLEAPIKEY, EVENTS_DISPLAY_KEY, CURRENT_WORKING_DIRECTORY, PORT
import hashlib
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
socketio = SocketIO(app)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY
csrf = CSRFProtect(app)

@app.before_request
def make_session_temp():
    session.permanent = False
    if session.get("username", None) == None and request.endpoint not in ["signin", "signup", "static", "logout"]:
        return redirect(url_for("signin"))
    if session.get("username", None) != None and request.endpoint in ["signin", "signup"]:
        return redirect(url_for("home"))

@app.route("/", methods=["POST", "GET"])
@app.route("/signup", methods=["POST", "GET"]) 
def signup():
    db = DB()
    form = SignUp()
    if form.is_submitted():
        if form.validate():
            username = request.form.get("Username")
            first_name = request.form.get("First_Name")
            last_name = request.form.get("Last_Name")
            phone = request.form.get("Phone")
            email = request.form.get("Email")
            password = request.form.get("Password")
            role = request.form.get("Role")
            
            if (len(db.query(r"select * from Users where Username = '%s'" % (username)))!= 0):
                session["error"] = "Username Already Exists"
                return redirect(url_for("signup"))

            elif (len(db.query(r"select * from Users where EmailID = '%s'" % (email)))!= 0):
                session["error"] = "Email Already Exists"
                return redirect(url_for("signup"))

            password += PASSWORD_SALT
            db.query(r"INSERT INTO Users (Username, PasswordHash, FirstName, LastName, EmailID, PhoneNumber, Role) values('%s','%s','%s','%s','%s','%s','%s')"% (username, hashlib.md5(password.encode()).hexdigest(), first_name, last_name, email, phone, role))
            session["message"] = "Successfully Signed Up"
            db.close() 
            return redirect(url_for("signup"))
        else:
            session["error"] = ". ".join([i[0] for i in form.errors.values()])
            return redirect(url_for("signup"))

    error = session.pop("error", None)
    message = session.pop("message", None)
    return render_template("index.html", error=error, message=message, form=form)


@app.route("/signin", methods=["POST", "GET"])  
def signin():    
    db = DB()
    form = SignIn()
    if form.validate_on_submit():
        emailorusername = request.form.get("UsernameorEmail")
        password = request.form["Password"]
        password += PASSWORD_SALT
        password = hashlib.md5(password.encode()).hexdigest()
        loginquery = db.query(r"select * from Users where (Username = '%s' or EmailID = '%s') and PasswordHash = '%s'" % (emailorusername, emailorusername, password))
        if (len(loginquery) == 0):
            session["error"] = "Invalid Username/Email or Password"
            return redirect(url_for("signin"))
        else:
            print(loginquery)
            session["username"] = loginquery[0]["Username"]
            session["role"] = loginquery[0]['Role']
            return redirect(url_for("home"))

    db.close()
    message = session.pop("message", None)
    error = session.pop("error", None)
    
    return render_template("signin.html", message=message, error=error, form=form)

@app.route("/logout")
def logout():
    session.pop("username", None)
    session["message"] = "Successfully Logged Out"
    return redirect(url_for("signin"))

@app.route("/home", methods=["POST", "GET"])
def home():
    return render_template("home.html")

@app.route("/createevents", methods = ['POST', 'GET'])
def createevents():
    if(session['role']!='organizer'):
        return redirect('home')
    form = CreateEvent()
    form.Index.data = "None"
    db = DB()
    if form.validate_on_submit():
        if(datetime.combine(form.EventStartDate.data, form.EventStartTime.data) > datetime.combine(form.EventEndDate.data, form.EventEndTime.data)):
            session["error"] = "End Date/Time cannot be before Start Date/Time"
            return redirect(url_for('createevents'))
        if(len(db.query("select * from events where EventName = '%s'"%form.EventName.data))>0):
            session["error"] = "Event Name already taken"
            return redirect(url_for('createevents'))
        if(form.EventBanner.data.mimetype!='application/octet-stream'):
            if(form.EventBanner.data.mimetype !="image/jpeg"):
                print(form.EventBanner.data.mimetype)
                session["error"] = "Only JPG Images are accepted"
                return redirect(url_for('createevents'))
        OrgID = db.query(r"select UserID from users where Username = '%s'"%session['username'])[0]['UserID']
        db.query(r"INSERT INTO Events (EventName, Description, StartDate, EndDate, StartTime, EndTime, Location, OrganizerID, Category, Seats) values('%s','%s','%s','%s','%s','%s','%s','%s','%s', %d)" % (form.EventName.data, form.EventDescription.data, form.EventStartDate.data, form.EventEndDate.data, form.EventStartTime.data, form.EventEndTime.data, form.EventLocation.data, OrgID, form.EventCategory.data, int(form.EventSeats.data)))
        if(form.EventBanner.data.mimetype!='application/octet-stream'):
            EventBann = request.files['EventBanner']
            EventID =  db.query(r"Select EventID from Events where (EventName = '%s' and OrganizerID = '%s')" % (form.EventName.data, OrgID))[0]['EventID']
            EventBann.save(os.path.join(CURRENT_WORKING_DIRECTORY, "static", "EventBanner", str(EventID)+".jpg"))
        print(form.data)
        session["message"] = "Event Created Successfully"
        return redirect(url_for('createevents'))
    else:
        print(form.errors)
    db.close()
    error = session.pop("error", None)
    message = session.pop("message", None)
    return render_template('createevents.html', form=form, maps_api_key=GOOGLEAPIKEY, error=error, message=message)

@app.route("/events", methods = ['POST', 'GET'])
def events():
    db = DB()
    form = DisplayEvents()
    cipher_events = Fernet(EVENTS_DISPLAY_KEY)
    event_list = db.query(r"select * from Events")
    coords_list = [tuple(map(float, i['Location'].split(','))) for i in event_list]
    coords_list = get_location_name(coords_list)
    registered_events = db.query(r"select EventID from Tickets where AttendeeID = (select UserID from Users where Username = '%s')" % session['username'])
    registered_events = [i['EventID'] for i in registered_events]
    count = 0
    for i in event_list:
        i['Start'] = dateconv(i.pop('StartDate'), i.pop('StartTime'))
        i['Location'] = coords_list[count]
        count+=1
        i['End'] = dateconv(i.pop('EndDate'), i.pop('EndTime'))
        i['Index'] = cipher_events.encrypt((str(i['EventID'])).encode()).decode()
        if(os.path.exists(os.path.join(CURRENT_WORKING_DIRECTORY, "static", "EventBanner", str(i['EventID'])+".jpg"))):
            i['EventBanner'] = str(i['EventID'])+".jpg"
        else:
            i['EventBanner'] = "noimage.jpg"
    db.close()
    message = session.pop("message", None)
    error = session.pop("error", None)
    return render_template('events.html', event_list = event_list, form=form, message = message, error = error, registered_events = registered_events)

@app.route("/register/", methods = ['POST', 'GET'])
def register():
    db = DB()
    regid = request.form.get('Index')
    cipher_events = Fernet(EVENTS_DISPLAY_KEY)
    eventID = cipher_events.decrypt(regid.encode()).decode()
    event = db.query(r"select * from Events where EventID = %s" % eventID)[0]
    if(event['Seats'] == 0):
        session["error"] = "No Seats Left"
        return redirect(url_for('events'))
    form = RegisterEvents()
    event['Start'] = dateconv(event.pop('StartDate'), event.pop('StartTime'))
    event['Location'] = get_location_name([(float(event['Location'].split(',')[0]), float(event['Location'].split(',')[1]))])
    event['End'] = dateconv(event.pop('EndDate'), event.pop('EndTime'))
    event['Index'] = cipher_events.encrypt((str(event['EventID'])).encode()).decode()
    if(os.path.exists(os.path.join(CURRENT_WORKING_DIRECTORY, "static", "EventBanner", str(event['EventID'])+".jpg"))):
        event['EventBanner'] = str(event['EventID'])+".jpg"
    else:
        event['EventBanner'] = "noimage.jpg"
    db.close()
    return render_template('registration.html', form=form, event=event)

@app.route("/finishregister", methods = ['POST'])
def finishregister():
    db = DB()
    regid = request.form.get('Index')
    cipher_events = Fernet(EVENTS_DISPLAY_KEY)
    eventID = cipher_events.decrypt(regid.encode()).decode()
    eventInfo = db.query(r"select * from Events where EventID = %s" % eventID)[0]
    if(eventInfo['Seats'] == 0):
        session["error"] = "No Seats Left"
        return redirect(url_for('events'))
    AttID = db.query(r"select UserID from users where UserName = '%s'"%session['username'])[0]['UserID']
    db.query(r"INSERT INTO Tickets (EventID, AttendeeID) values(%s, %s)" % (eventID, AttID))
    db.query(r"UPDATE Events SET Seats = Seats - 1 where EventID = %s" % eventID)
    if(request.form.get('CalenderIntegration') == 'y'):
        Start = (datetime(eventInfo['StartDate'].year, eventInfo['StartDate'].month, eventInfo['StartDate'].day)+eventInfo['StartTime'])
        End = (datetime(eventInfo['EndDate'].year, eventInfo['EndDate'].month, eventInfo['EndDate'].day)+eventInfo['EndTime'])
        calID = create_google_calendar_event(db.query(r"select EmailID from Users where Username = '%s'"%session['username'])[0]['EmailID'], eventInfo['EventName'], start = Start, end = End, description=eventInfo['Description'], location=[float(i) for i in eventInfo['Location'].split(',')]) 
        db.query(r"UPDATE Tickets SET CalendarIntegration = 1, CalendarID = '%s' where EventID = %s and AttendeeID = %s" % (calID, eventID, AttID))
        
    else:
        db.query(r"UPDATE Tickets SET CalendarIntegration = 0, CalendarID = '%s' where EventID = %s and AttendeeID = %s" % ("None", eventID, AttID))
    db.close()
    session['message'] = "Successfully Registered for Event" 
    return redirect(url_for('events'))

@app.route("/registeredevents", methods = ['POST', 'GET'])
def registeredevents():
    db = DB()
    my_events = db.query("select * from Events where EventID in (select EventID from Tickets where AttendeeID = (select UserID from Users where Username = '%s'))" % session['username'])
    cipher_events = Fernet(EVENTS_DISPLAY_KEY)
    form = DisplayEvents()
    coords_list = [tuple(map(float, i['Location'].split(','))) for i in my_events]
    coords_list = get_location_name(coords_list)
    registered_events = db.query(r"select EventID, TicketID from Tickets where AttendeeID = (select UserID from Users where Username = '%s')" % session['username'])
    TicketID = [i['TicketID'] for i in registered_events]
    print(TicketID)
    registered_events = [i['EventID'] for i in registered_events]
    count = 0
    for i in my_events:
        i['Start'] = dateconv(i.pop('StartDate'), i.pop('StartTime'))
        i['Location'] = coords_list[count]
        i['End'] = dateconv(i.pop('EndDate'), i.pop('EndTime'))
        i['Index'] = cipher_events.encrypt((str(TicketID[count])+"!!!!!"+str(i['EventID'])).encode()).decode()
        if(os.path.exists(os.path.join(CURRENT_WORKING_DIRECTORY, "static", "EventBanner", str(i['EventID'])+".jpg"))):
            i['EventBanner'] = str(i['EventID'])+".jpg"
        else:
            i['EventBanner'] = "noimage.jpg"
        print(i, TicketID[count])
        count+=1
    db.close()
    message = session.pop("message", None)
    error = session.pop("error", None)
    return render_template('registeredevents.html',form=form, my_events = my_events, message = message, error = error)

@app.route("/showqr", methods = ['POST', 'GET'])
def showqr():
    db = DB()
    cipher_events = Fernet(EVENTS_DISPLAY_KEY)
    TicketID, EventID = cipher_events.decrypt(request.form.get('Index').encode()).decode().split("!!!!!")
    EventInfo = db.query(r"select * from Events where EventID = %s" % EventID)
    AttendeeInfo = db.query(r"select * from Users where Username = '%s'" % session['username'])
    AttendeeInfo[0]['TicketStatus'] = " ".join(db.query(r"select Status from Tickets where TicketID = %s" % TicketID)[0]['Status'].split("_"))
    coords_list = [tuple(map(float, i['Location'].split(','))) for i in EventInfo]
    coords_list = get_location_name(coords_list)
    event_form = DisplayEvents()
    user_form = SignUp()
    for i in EventInfo:
        i['Start'] = dateconv(i.pop('StartDate'), i.pop('StartTime'))
        i['Location'] = coords_list[0]
        i['End'] = dateconv(i.pop('EndDate'), i.pop('EndTime'))
        if(os.path.exists(os.path.join(CURRENT_WORKING_DIRECTORY, "static", "EventBanner", str(i['EventID'])+".jpg"))):
            i['EventBanner'] = str(i['EventID'])+".jpg"
        else:
            i['EventBanner'] = "noimage.jpg"
    print(AttendeeInfo)
    qr = qrcodeticket(cipher_events.encrypt((TicketID+"!!!!!"+EventID).encode()).decode())
    return render_template('showqr.html', qr=qr, event_form = event_form, user_form = user_form, EventInfo = EventInfo, AttendeeInfo = AttendeeInfo)

@app.route("/listownedevents", methods = ['POST', 'GET'])
def listownedevents():
    db = DB()
    if(session['role']!='organizer'):
        return redirect('home')
    form = DisplayEvents()
    event_list = db.query(r"select * from Events where OrganizerID = (select UserID from Users where Username = '%s')" % session['username'])
    cipher_events = Fernet(EVENTS_DISPLAY_KEY)
    coords_list = [tuple(map(float, i['Location'].split(','))) for i in event_list]
    coords_list = get_location_name(coords_list)
    count = 0
    for i in event_list:
        i['Start'] = dateconv(i.pop('StartDate'), i.pop('StartTime'))
        i['Location'] = coords_list[count]
        count+=1
        i['End'] = dateconv(i.pop('EndDate'), i.pop('EndTime'))
        i['Index'] = cipher_events.encrypt((str(i['EventID'])).encode()).decode()
        if(os.path.exists(os.path.join(CURRENT_WORKING_DIRECTORY, "static", "EventBanner", str(i['EventID'])+".jpg"))):
            i['EventBanner'] = str(i['EventID'])+".jpg"
        else:
            i['EventBanner'] = "noimage.jpg"

    db.close()
    message = session.pop("message", None)
    error = session.pop("error", None)
    return render_template('listownedevents.html', event_list = event_list, form=form, message = message, error = error)

@app.route("/manageevents", methods = ['POST'])
def manageevents():
    if(session['role']!='organizer'):
        return redirect('home')
    form = ManageEvents()
    db =DB()
    cipher_events = Fernet(EVENTS_DISPLAY_KEY)
    EventID = cipher_events.decrypt(request.form.get('Index').encode()).decode()
    event_list = db.query("select * from Events where EventID = %s" % EventID)
    coords_list = [tuple(map(float, i['Location'].split(','))) for i in event_list]
    coords_list = get_location_name(coords_list)
    count = 0
    for i in event_list:
        i['Start'] = dateconv(i.pop('StartDate'), i.pop('StartTime'))
        i['Location'] = coords_list[count]
        count+=1
        i['End'] = dateconv(i.pop('EndDate'), i.pop('EndTime'))
        i['Index'] = cipher_events.encrypt((str(i['EventID'])).encode()).decode()
        if(os.path.exists(os.path.join(CURRENT_WORKING_DIRECTORY, "static", "EventBanner", str(i['EventID'])+".jpg"))):
            i['EventBanner'] = str(i['EventID'])+".jpg"
        else:
            i['EventBanner'] = "noimage.jpg"
    if form.validate_on_submit():
        if (request.form.get('Delete') != None):
            EventID = cipher_events.decrypt(request.form.get('Index').encode()).decode()
            TicketCalID = db.query(r"select CalendarID from Tickets where EventID = %s" % EventID)
            TicketCalID = [i for i in TicketCalID if i['CalendarID'] != "None"]
            for i in TicketCalID:
                delete_google_calendar_event(i['CalendarID'])
            db.query(r"DELETE FROM Events where EventID = %s" % EventID)
            if(os.path.exists(os.path.join(CURRENT_WORKING_DIRECTORY, "static", "EventBanner", str(event_list[0]['EventID'])+".jpg"))):
                os.remove(os.path.join(CURRENT_WORKING_DIRECTORY, "static", "EventBanner", str(event_list[0]['EventID'])+".jpg"))
            session['message'] = "Event Deleted Successfully"
            return redirect(url_for('listownedevents'))
        elif(request.form.get('Edit') != None):
            return redirect(url_for('editevent'))
    return render_template("manageevents.html", form = form, event_list = event_list)

@app.route("/editevent", methods = ['POST', 'GET'])
def editevent():
    if(session['role']!='organizer'):
        return redirect('home')
    db = DB()
    form = CreateEvent()
    cipher_events = Fernet(EVENTS_DISPLAY_KEY)
    EventID = cipher_events.decrypt(request.form.get('Index').encode()).decode()
    event_list = db.query("select * from Events where EventID = %s" % EventID)
    event_list = event_list[0]
    event_list['Index'] = cipher_events.encrypt((str(event_list['EventID'])).encode()).decode()
    
    start_datetime = datetime.combine(datetime.today(), time(0,0,0)) + event_list['StartTime']
    event_list['StartTime'] = start_datetime.time()

    end_datetime = datetime.combine(datetime.today(), time(0,0,0)) + event_list['EndTime']
    event_list['EndTime'] = end_datetime.time()

    if(os.path.exists(os.path.join(CURRENT_WORKING_DIRECTORY, "static", "EventBanner", str(event_list['EventID'])+".jpg"))):
        event_list['EventBanner'] = str(event_list['EventID'])+".jpg"
    else:
        event_list['EventBanner'] = "noimage.jpg"
    form.EventDescription.data = event_list['Description']
    if form.validate_on_submit():
        print("hehe")
        if(datetime.combine(form.EventStartDate.data, form.EventStartTime.data) > datetime.combine(form.EventEndDate.data, form.EventEndTime.data)):
            session["error"] = "End Date/Time cannot be before Start Date/Time"
            return redirect(url_for('listownedevents'))
        if(len(db.query("select EventName from events where EventName = '%s'"%form.EventName.data))>0 and form.EventName.data != event_list['EventName']):
            session["error"] = "Event Name already taken"
            return redirect(url_for('listownedevents'))
        if(form.EventBanner.data.mimetype!='application/octet-stream'):
            if(form.EventBanner.data.mimetype !="image/jpeg"):
                print(form.EventBanner.data.mimetype)
                session["error"] = "Only JPG Images are accepted"
                return redirect(url_for('listownedevents'))
            
        db.query(r"UPDATE Events SET EventName = '%s', Description = '%s', StartDate = '%s', EndDate = '%s', StartTime = '%s', EndTime = '%s', Location = '%s', Category = '%s', Seats = %d where EventID = %s" % (form.EventName.data, form.EventDescription.data, form.EventStartDate.data, form.EventEndDate.data, form.EventStartTime.data, form.EventEndTime.data, form.EventLocation.data, form.EventCategory.data, int(form.EventSeats.data), EventID))
        if(form.EventBanner.data.mimetype!='application/octet-stream'):
            EventBann = request.files['EventBanner']
            EventBann.save(os.path.join(CURRENT_WORKING_DIRECTORY, "static", "EventBanner", str(EventID)+".jpg"))
        session["message"] = "Event Edited Successfully"
        for i in (db.query(r"select CalendarID from Tickets where EventID = %s and CalendarIntegration = 1" % EventID)):
            print(i['CalendarID'])
            update_google_calendar_event(event_id = i['CalendarID'],event_title = form.EventName.data, description = form.EventDescription.data, location = [float(i) for i in form.EventLocation.data.split(',')], start = datetime.combine(form.EventStartDate.data, form.EventStartTime.data), end = datetime.combine(form.EventEndDate.data, form.EventEndTime.data))
        return redirect(url_for('listownedevents'))
    else:
        print(form.EventEndTime, form.errors)
    
    db.close()
    error = session.pop("error", None)
    message = session.pop("message", None)
    return render_template('editevent.html', form=form, maps_api_key=GOOGLEAPIKEY, error=error, message=message, event_list = event_list)


# Route to render attendence.html and start QR code detection
@app.route("/attendence", methods=['POST', 'GET'])
def attendence():
    if(session['role']!='organizer'):
        return redirect('home')
    form = QRSend()
    message = session.pop("message", None)
    error = session.pop("error", None)
    return render_template("attendence.html", form=form, message = message, error=error)

@app.route('/process_qr_data', methods=['POST'])
def process_qr_data():
    cipher_events = Fernet(EVENTS_DISPLAY_KEY)
    TicketID, EventID = cipher_events.decrypt(request.form.get('QR').encode()).decode().split("!!!!!")
    db = DB()
    EventOrg = db.query(r"select UserName from Users where UserID = (select OrganizerID from events where EventID = %s)" % EventID)
    if(EventOrg[0]['UserName']!=session['username']):
        session['error'] = "You are not the Organizer of this Event"
        return redirect(url_for('attendence'))
    
    EventTime = db.query(r"select StartDate, StartTime, EndDate, EndTime from Events where EventID = %s" % EventID)[0]
    EventTime = [datetime(EventTime["StartDate"].year, EventTime["StartDate"].month, EventTime["StartDate"].day)+EventTime["StartTime"], datetime(EventTime["EndDate"].year, EventTime["EndDate"].month, EventTime["EndDate"].day)+EventTime["EndTime"]]
    if(datetime.now() < EventTime[0] or datetime.now() > EventTime[1]):
        session['error'] = "Event is not currently happening"
        return redirect(url_for('attendence'))
    
    TicketStatus = db.query("select Status from tickets where TicketID=%s" % TicketID)[0]['Status']
    if( TicketStatus == 'checked_in'):
        session['error'] = "Attendence Already Marked"
        return redirect(url_for('attendence'))
    
    if( TicketStatus == 'cancelled'):
        session['error'] = "Ticket Cancelled"
        return redirect(url_for('attendence'))
    
    db.query(r"Update tickets set Status = 'checked_in' where TicketID = %s" % TicketID)
    db.close()
    
    session['message'] = "Attendence Marked Successfully"
    return redirect(url_for('attendence'))

@app.route("/switchrole")
def switchrole():
    if(session['role']=='organizer'):
        session['role']='attendee'
    else:
        session['role']='organizer'
        
    return redirect(url_for('home'))

@app.errorhandler(404)  
def not_found(e): 
  return render_template("404.html") 

if __name__ == "__main__":
    with app.app_context():
        ssl_context = (r'C:\Users\singh\Documents\Programs\Sem6_College\SoftwareEng\Certificates\localhost.crt', r'C:\Users\singh\Documents\Programs\Sem6_College\SoftwareEng\Certificates\localhost.key')
        app.run(debug=True, ssl_context=ssl_context, port=PORT, host="0.0.0.0")

