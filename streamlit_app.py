# app.py
import streamlit as st
import pandas as pd
import datetime
import hashlib
import json
import os
from datetime import datetime

# File paths for data storage
USERS_FILE = "data/users.json"
EVENTS_FILE = "data/events.json"
REGISTRATIONS_FILE = "data/registrations.json"
TEAMS_FILE = "data/teams.json"

# Initialize data files
def init_data_files():
    """Create data directories and files if they don't exist"""
    if not os.path.exists("data"):
        os.makedirs("data")
    
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump([], f)
    
    if not os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, "w") as f:
            json.dump([], f)
    
    if not os.path.exists(REGISTRATIONS_FILE):
        with open(REGISTRATIONS_FILE, "w") as f:
            json.dump([], f)
    
    if not os.path.exists(TEAMS_FILE):
        with open(TEAMS_FILE, "w") as f:
            json.dump([], f)

# Helper functions
def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_data(file_path):
    """Load data from JSON file"""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except:
        return []

def save_data(file_path, data):
    """Save data to JSON file"""
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

# User management functions
def create_user(username, password, role, full_name, email):
    """Create a new user"""
    users = load_data(USERS_FILE)
    
    # Check if username already exists
    if any(user["username"] == username for user in users):
        return False, "Username already exists"
    
    user = {
        "username": username,
        "password": hash_password(password),
        "role": role,  # "participant" or "admin"
        "full_name": full_name,
        "email": email,
        "created_at": datetime.now().isoformat()
    }
    
    users.append(user)
    save_data(USERS_FILE, users)
    return True, "User created successfully"

def authenticate_user(username, password):
    """Authenticate user credentials"""
    users = load_data(USERS_FILE)
    hashed_password = hash_password(password)
    
    for user in users:
        if user["username"] == username and user["password"] == hashed_password:
            return True, user
    return False, None

# Event management functions
def create_event(name, description, date, venue, total_seats, admin_username):
    """Create a new event"""
    events = load_data(EVENTS_FILE)
    
    event = {
        "id": len(events) + 1,
        "name": name,
        "description": description,
        "date": date,
        "venue": venue,
        "total_seats": total_seats,
        "available_seats": total_seats,
        "created_by": admin_username,
        "created_at": datetime.now().isoformat()
    }
    
    events.append(event)
    save_data(EVENTS_FILE, events)
    return True, "Event created successfully"

def get_all_events():
    """Get all events"""
    return load_data(EVENTS_FILE)

def get_event_by_id(event_id):
    """Get event by ID"""
    events = load_data(EVENTS_FILE)
    for event in events:
        if event["id"] == event_id:
            return event
    return None

def update_event_seats(event_id, seats_booked):
    """Update available seats for an event"""
    events = load_data(EVENTS_FILE)
    for event in events:
        if event["id"] == event_id:
            event["available_seats"] -= seats_booked
            save_data(EVENTS_FILE, events)
            return True
    return False

# Registration functions
def register_for_event(event_id, username, team_id=None, member_count=1):
    """Register a participant or team for an event"""
    event = get_event_by_id(event_id)
    if not event:
        return False, "Event not found"
    
    if event["available_seats"] < member_count:
        return False, f"Only {event['available_seats']} seats available"
    
    registrations = load_data(REGISTRATIONS_FILE)
    
    # Check if already registered
    for reg in registrations:
        if reg["event_id"] == event_id and reg["username"] == username:
            return False, "You are already registered for this event"
    
    registration = {
        "event_id": event_id,
        "username": username,
        "team_id": team_id,
        "member_count": member_count,
        "registered_at": datetime.now().isoformat()
    }
    
    registrations.append(registration)
    save_data(REGISTRATIONS_FILE, registrations)
    
    # Update available seats
    update_event_seats(event_id, member_count)
    
    return True, "Registration successful"

def get_user_registrations(username):
    """Get all registrations for a user"""
    registrations = load_data(REGISTRATIONS_FILE)
    user_regs = []
    
    for reg in registrations:
        if reg["username"] == username:
            event = get_event_by_id(reg["event_id"])
            if event:
                user_regs.append({
                    "event_name": event["name"],
                    "event_date": event["date"],
                    "venue": event["venue"],
                    "member_count": reg["member_count"],
                    "registered_at": reg["registered_at"]
                })
    
    return user_regs

# Team management functions
def create_team(team_name, team_lead, members, event_id=None):
    """Create a new team"""
    teams = load_data(TEAMS_FILE)
    
    # Check if team name already exists
    if any(team["team_name"] == team_name for team in teams):
        return False, "Team name already exists"
    
    team = {
        "team_name": team_name,
        "team_lead": team_lead,
        "members": members,
        "event_id": event_id,
        "created_at": datetime.now().isoformat()
    }
    
    teams.append(team)
    save_data(TEAMS_FILE, teams)
    return True, "Team created successfully"

def get_user_teams(username):
    """Get all teams where user is a member or lead"""
    teams = load_data(TEAMS_FILE)
    user_teams = []
    
    for team in teams:
        if team["team_lead"] == username or username in team["members"]:
            user_teams.append(team)
    
    return user_teams

# UI Pages
def login_page():
    """Login page"""
    st.title("🎫 Event Registration System")
    st.subheader("Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if username and password:
                success, user = authenticate_user(username, password)
                if success:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.session_state["role"] = user["role"]
                    st.session_state["full_name"] = user["full_name"]
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please enter both username and password")
    
    st.markdown("---")
    st.subheader("New User?")
    if st.button("Register Here"):
        st.session_state["page"] = "register"
        st.rerun()

def register_page():
    """Registration page for new users"""
    st.title("🎫 Event Registration System")
    st.subheader("Create New Account")
    
    with st.form("register_form"):
        full_name = st.text_input("Full Name")
        email = st.text_input("Email")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        role = st.selectbox("Role", ["participant", "admin"])
        
        submit = st.form_submit_button("Register")
        
        if submit:
            if not all([full_name, email, username, password, confirm_password]):
                st.warning("Please fill all fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            else:
                success, message = create_user(username, password, role, full_name, email)
                if success:
                    st.success(message)
                    st.info("Please login with your credentials")
                    if st.button("Go to Login"):
                        st.session_state["page"] = "login"
                        st.rerun()
                else:
                    st.error(message)
    
    if st.button("Back to Login"):
        st.session_state["page"] = "login"
        st.rerun()

def participant_dashboard():
    """Participant dashboard"""
    st.title(f"👤 Welcome {st.session_state['full_name']}")
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Available Events", "📝 My Registrations", "👥 My Teams", "ℹ️ Profile"])
    
    with tab1:
        st.subheader("Available Events")
        events = get_all_events()
        
        if not events:
            st.info("No events available at the moment")
        else:
            for event in events:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"### {event['name']}")
                        st.write(f"📅 Date: {event['date']}")
                        st.write(f"📍 Venue: {event['venue']}")
                        st.write(f"🎫 Available Seats: {event['available_seats']}/{event['total_seats']}")
                        st.write(f"📝 Description: {event['description']}")
                    with col2:
                        if event['available_seats'] > 0:
                            # Check if already registered
                            registrations = load_data(REGISTRATIONS_FILE)
                            already_registered = any(
                                reg["event_id"] == event["id"] and 
                                reg["username"] == st.session_state["username"] 
                                for reg in registrations
                            )
                            
                            if already_registered:
                                st.success("✅ Registered")
                            else:
                                # Option to register as individual or team
                                reg_type = st.radio(
                                    "Register as:",
                                    ["Individual", "Team"],
                                    key=f"reg_type_{event['id']}"
                                )
                                
                                if reg_type == "Individual":
                                    if st.button(f"Register", key=f"ind_{event['id']}"):
                                        success, message = register_for_event(
                                            event["id"], 
                                            st.session_state["username"]
                                        )
                                        if success:
                                            st.success(message)
                                            st.rerun()
                                        else:
                                            st.error(message)
                                else:
                                    # Team registration
                                    teams = get_user_teams(st.session_state["username"])
                                    if teams:
                                        team_names = [t["team_name"] for t in teams]
                                        selected_team = st.selectbox(
                                            "Select Team",
                                            team_names,
                                            key=f"team_select_{event['id']}"
                                        )
                                        
                                        if st.button(f"Register Team", key=f"team_{event['id']}"):
                                            # Find team members count
                                            team = next(t for t in teams if t["team_name"] == selected_team)
                                            member_count = len(team["members"]) + 1  # +1 for team lead
                                            
                                            success, message = register_for_event(
                                                event["id"],
                                                st.session_state["username"],
                                                selected_team,
                                                member_count
                                            )
                                            if success:
                                                st.success(message)
                                                st.rerun()
                                            else:
                                                st.error(message)
                                    else:
                                        st.warning("No teams found. Create a team first!")
                                        if st.button("Create Team", key=f"create_team_{event['id']}"):
                                            st.session_state["tab"] = "Create Team"
                                            st.rerun()
                        else:
                            st.warning("🔴 Seats Full")
                    st.markdown("---")
    
    with tab2:
        st.subheader("My Registrations")
        registrations = get_user_registrations(st.session_state["username"])
        
        if registrations:
            df = pd.DataFrame(registrations)
            st.dataframe(df)
        else:
            st.info("You haven't registered for any events yet")
    
    with tab3:
        st.subheader("My Teams")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Create Team")
            with st.form("create_team_form"):
                team_name = st.text_input("Team Name")
                members_input = st.text_area("Team Members (one per line)", 
                                            help="Enter usernames of team members, one per line")
                event_id = st.number_input("Event ID (optional)", min_value=0, step=1)
                
                if st.form_submit_button("Create Team"):
                    if team_name and members_input:
                        members = [m.strip() for m in members_input.split("\n") if m.strip()]
                        success, message = create_team(
                            team_name,
                            st.session_state["username"],
                            members,
                            event_id if event_id > 0 else None
                        )
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.warning("Please enter team name and at least one member")
        
        with col2:
            st.markdown("### My Teams")
            teams = get_user_teams(st.session_state["username"])
            
            if teams:
                for team in teams:
                    with st.container():
                        st.markdown(f"**Team: {team['team_name']}**")
                        st.write(f"Team Lead: {team['team_lead']}")
                        st.write(f"Members: {', '.join(team['members'])}")
                        if team.get('event_id'):
                            event = get_event_by_id(team['event_id'])
                            if event:
                                st.write(f"Event: {event['name']}")
                        st.markdown("---")
            else:
                st.info("You are not part of any team yet")
    
    with tab4:
        st.subheader("Profile Information")
        users = load_data(USERS_FILE)
        user = next((u for u in users if u["username"] == st.session_state["username"]), None)
        
        if user:
            st.write(f"**Username:** {user['username']}")
            st.write(f"**Full Name:** {user['full_name']}")
            st.write(f"**Email:** {user['email']}")
            st.write(f"**Role:** {user['role']}")
            st.write(f"**Joined:** {user['created_at']}")

def admin_dashboard():
    """Admin dashboard"""
    st.title(f"👑 Admin Dashboard - {st.session_state['full_name']}")
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📅 Manage Events", "👥 Manage Users", "📊 Registrations", "🎯 Reports"])
    
    with tab1:
        st.subheader("Create New Event")
        with st.form("create_event_form"):
            name = st.text_input("Event Name")
            description = st.text_area("Description")
            date = st.date_input("Event Date", min_value=datetime.now().date())
            venue = st.text_input("Venue")
            total_seats = st.number_input("Total Seats", min_value=1, step=1)
            
            if st.form_submit_button("Create Event"):
                if name and description and venue and total_seats:
                    success, message = create_event(
                        name, description, str(date), venue, total_seats,
                        st.session_state["username"]
                    )
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Please fill all fields")
        
        st.markdown("---")
        st.subheader("All Events")
        events = get_all_events()
        
        if events:
            for event in events:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{event['name']}**")
                    st.write(f"📅 {event['date']} | 📍 {event['venue']}")
                    st.write(f"🎫 Seats: {event['available_seats']}/{event['total_seats']}")
                with col2:
                    st.write(f"Created by: {event['created_by']}")
                st.markdown("---")
        else:
            st.info("No events created yet")
    
    with tab2:
        st.subheader("User Management")
        users = load_data(USERS_FILE)
        
        if users:
            df = pd.DataFrame(users)
            df = df.drop(columns=["password"])  # Hide password
            st.dataframe(df)
        else:
            st.info("No users registered")
    
    with tab3:
        st.subheader("Event Registrations")
        registrations = load_data(REGISTRATIONS_FILE)
        
        if registrations:
            # Get event details
            events = get_all_events()
            event_dict = {e["id"]: e["name"] for e in events}
            
            # Prepare data for display
            reg_data = []
            for reg in registrations:
                reg_data.append({
                    "Event": event_dict.get(reg["event_id"], "Unknown"),
                    "Participant": reg["username"],
                    "Team": reg.get("team_id", "Individual"),
                    "Members": reg["member_count"],
                    "Registered At": reg["registered_at"]
                })
            
            df = pd.DataFrame(reg_data)
            st.dataframe(df)
        else:
            st.info("No registrations yet")
    
    with tab4:
        st.subheader("Reports & Statistics")
        
        events = get_all_events()
        registrations = load_data(REGISTRATIONS_FILE)
        users = load_data(USERS_FILE)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Events", len(events))
        
        with col2:
            st.metric("Total Registrations", len(registrations))
        
        with col3:
            st.metric("Total Users", len(users))
        
        st.markdown("---")
        
        # Event-wise registration count
        if events:
            st.subheader("Event-wise Registrations")
            event_reg_counts = []
            for event in events:
                count = sum(1 for reg in registrations if reg["event_id"] == event["id"])
                event_reg_counts.append({
                    "Event": event["name"],
                    "Registrations": count,
                    "Available Seats": event["available_seats"],
                    "Total Seats": event["total_seats"]
                })
            
            df = pd.DataFrame(event_reg_counts)
            st.dataframe(df)

def main():
    """Main application"""
    # Initialize data files
    init_data_files()
    
    # Initialize session state
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    
    if "page" not in st.session_state:
        st.session_state["page"] = "login"
    
    # Page routing
    if st.session_state["logged_in"]:
        # Add logout button in sidebar
        with st.sidebar:
            st.title("Navigation")
            st.write(f"Welcome, {st.session_state['full_name']}")
            st.write(f"Role: {st.session_state['role']}")
            st.markdown("---")
            
            if st.button("🚪 Logout"):
                for key in st.session_state.keys():
                    del st.session_state[key]
                st.rerun()
        
        # Show appropriate dashboard based on role
        if st.session_state["role"] == "admin":
            admin_dashboard()
        else:
            participant_dashboard()
    else:
        if st.session_state["page"] == "login":
            login_page()
        elif st.session_state["page"] == "register":
            register_page()

if __name__ == "__main__":
    main()
