from datetime import datetime
from constants import GOOGLEAPIKEY
import asyncio
import aiohttp
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
import qrcode
import base64
from io import BytesIO
import cv2
from pyzbar.pyzbar import decode
from flask import current_app, redirect, url_for
from constants import PORT
from urllib.parse import urlparse, urlunparse

def dateconv(d, t):
    toreturn = (datetime(d.year, d.month, d.day)+t).ctime().split()
    toreturn.insert(1, toreturn[2])
    toreturn[3] = toreturn[-1]
    del toreturn[-1]
    toreturn[-1] = toreturn[-1][:-3]
    toreturn[1] = "-".join(toreturn[1:4])
    del toreturn[3]
    del toreturn[2]
    return ", ".join(toreturn)

async def fetch_location_name(lat, lng, api_key, session):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={api_key}"
    async with session.get(url) as response:
        data = await response.json()
        if data['status'] == 'OK':
            results = data['results']
            if results:
                return results[0]['formatted_address']
        return None

async def get_locations_names_async(coords_list):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_location_name(lat, lng, GOOGLEAPIKEY, session) for lat, lng in coords_list]
        return await asyncio.gather(*tasks)

def get_location_name(coords_list):
    return asyncio.run(get_locations_names_async(coords_list))

def create_google_calendar_event(email, event_title, start, end, description, location):
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            r'C:\Users\singh\Desktop\Creds\credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    event_body = {
        'summary': event_title,
        'start': {
            'dateTime': start.isoformat(),
            'timeZone': 'IST',
        },
        'end': {
            'dateTime': end.isoformat(),
            'timeZone': 'IST',
        },
        'attendees': [
            {'email': email},
        ],
        'description': description,
        'location': "https://www.google.com/maps?q={latitude},{longitude}".format(latitude=location[0], longitude=location[1])
    }

    event = service.events().insert(calendarId='primary', body=event_body).execute()
    return event['id']

def update_google_calendar_event(event_id, event_title=None, start=None, end=None, description=None, location=None):
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    print(event_id, event_title, start, end, description, location)
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            r'C:\Users\singh\Desktop\Creds\credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    event = service.events().get(calendarId='primary', eventId=event_id).execute()

    if event_title:
        event['summary'] = event_title
    if start:
        event['start'] = {'dateTime': start.isoformat(), 'timeZone': 'IST'}
    if end:
        event['end'] = {'dateTime': end.isoformat(), 'timeZone': 'IST'}
    if description:
        event['description'] = description
    if location:
        event['location'] = "https://www.google.com/maps?q={latitude},{longitude}".format(latitude=location[0], longitude=location[1])

    updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
    print('Event updated: %s' % (updated_event.get('htmlLink')))

def delete_google_calendar_event(event_id):
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            r'C:\Users\singh\Desktop\Creds\credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    service.events().delete(calendarId='primary', eventId=event_id).execute()
    print('Event deleted successfully')
    return True
        
def qrcodeticket(data):
    qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    
    return base64.b64encode(buffered.getvalue()).decode("utf-8")
