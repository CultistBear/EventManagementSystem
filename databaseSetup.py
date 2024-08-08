from databaseManagement import DB
from constants import PASSWORD_SALT
import hashlib
db = DB()

def password_generate(passw):
    return hashlib.md5((passw+PASSWORD_SALT).encode()).hexdigest()

try:
    db.query("use events;")
    db.query("drop table if exists events;")
    db.query("drop table if exists users;")
    db.query("drop table if exists tickets;")
    db.query("CREATE TABLE Users (Username VARCHAR(255) NOT NULL, UserID INT PRIMARY KEY AUTO_INCREMENT, PasswordHash VARCHAR(255) NOT NULL, FirstName VARCHAR(255) NOT NULL, LastName VARCHAR(255) NOT NULL, Verified VARCHAR(1) DEFAULT 'N', EmailID VARCHAR(255) NOT NULL, PhoneNumber VARCHAR(15), Role ENUM('organizer', 'attendee', 'admin'));")
    db.query("CREATE TABLE Events (EventID INT PRIMARY KEY AUTO_INCREMENT, OrganizerID INT, EventName VARCHAR(255) NOT NULL, Description TEXT, StartDate DATE NOT NULL, StartTime TIME NOT NULL, EndDate DATE NOT NULL, EndTime TIME NOT NULL, Location VARCHAR(255) NOT NULL, Category VARCHAR(50), Seats INT, FOREIGN KEY (OrganizerID) REFERENCES Users(UserID) ON DELETE CASCADE);")
    db.query("CREATE TABLE Tickets ( TicketID INT PRIMARY KEY AUTO_INCREMENT, EventID INT, AttendeeID INT, Status ENUM('registered', 'checked_in', 'cancelled') DEFAULT 'registered', CalendarIntegration int, CalendarID varchar(255), FOREIGN KEY (EventID) REFERENCES Events(EventID) ON DELETE CASCADE, FOREIGN KEY (AttendeeID) REFERENCES Users(UserID) ON DELETE CASCADE);")
    db.close()
    
except Exception as e:
    print(e)
