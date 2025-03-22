import streamlit as st
import pandas as pd
import numpy as np
import math
import uuid
from datetime import datetime
import json
import os

# File paths for our "database"
FARMERS_FILE = "farmers.json"
VENDORS_FILE = "vendors.json"
COMMUNITIES_FILE = "communities.json"

# Initialize session state variables if they don't exist
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'current_user_type' not in st.session_state:
    st.session_state.current_user_type = None
if 'chat_community' not in st.session_state:
    st.session_state.chat_community = None
if 'view' not in st.session_state:
    st.session_state.view = "communities"  # Default view is communities list

# Haversine formula to calculate distance between two points on Earth
def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate the distance between two points using Haversine formula"""
    R = 6371  # Earth's radius in kilometers
    
    # Convert decimal degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance

# Database operations
def load_data(file_path):
    """Load data from JSON file"""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return []

def save_data(data, file_path):
    """Save data to JSON file"""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def register_user(user_type, name, latitude, longitude):
    """Register a new user (farmer or vendor)"""
    user_id = str(uuid.uuid4())
    user_data = {
        "id": user_id,
        "name": name,
        "latitude": latitude,
        "longitude": longitude,
        "created_at": datetime.now().isoformat()
    }
    
    if user_type == "farmer":
        farmers = load_data(FARMERS_FILE)
        farmers.append(user_data)
        save_data(farmers, FARMERS_FILE)
        
        # Add farmer to all nearby vendor communities
        add_farmer_to_communities(user_data)
        
    else:  # vendor
        vendors = load_data(VENDORS_FILE)
        vendors.append(user_data)
        save_data(vendors, VENDORS_FILE)
        
        # Create a new community for this vendor
        create_vendor_community(user_data)
    
    return user_id

def create_vendor_community(vendor):
    """Create a new community for a vendor and add nearby farmers"""
    communities = load_data(COMMUNITIES_FILE)
    
    # Create new community
    community = {
        "id": str(uuid.uuid4()),
        "name": f"{vendor['name']}'s Community",
        "vendor_id": vendor["id"],
        "vendor_name": vendor["name"],
        "members": [{"id": vendor["id"], "name": vendor["name"], "type": "vendor"}],
        "messages": [],
        "created_at": datetime.now().isoformat()
    }
    
    # Add all farmers within 50km
    farmers = load_data(FARMERS_FILE)
    for farmer in farmers:
        distance = calculate_distance(
            vendor["latitude"], vendor["longitude"],
            farmer["latitude"], farmer["longitude"]
        )
        
        if distance <= 50:  # 50 km radius
            community["members"].append({
                "id": farmer["id"], 
                "name": farmer["name"],
                "type": "farmer",
                "distance": round(distance, 2)
            })
    
    communities.append(community)
    save_data(communities, COMMUNITIES_FILE)

def add_farmer_to_communities(farmer):
    """Add a new farmer to all vendor communities within 50km"""
    communities = load_data(COMMUNITIES_FILE)
    vendors = load_data(VENDORS_FILE)
    
    for community in communities:
        vendor_id = community["vendor_id"]
        vendor = next((v for v in vendors if v["id"] == vendor_id), None)
        
        if vendor:
            distance = calculate_distance(
                vendor["latitude"], vendor["longitude"],
                farmer["latitude"], farmer["longitude"]
            )
            
            if distance <= 50:  # 50 km radius
                community["members"].append({
                    "id": farmer["id"], 
                    "name": farmer["name"],
                    "type": "farmer",
                    "distance": round(distance, 2)
                })
    
    save_data(communities, COMMUNITIES_FILE)

def get_user_communities(user_id, user_type):
    """Get all communities that a user is a member of"""
    communities = load_data(COMMUNITIES_FILE)
    user_communities = []
    
    for community in communities:
        if any(member["id"] == user_id for member in community["members"]):
            community_info = {
                "id": community["id"],
                "name": community["name"],
                "vendor_name": community["vendor_name"],
                "member_count": len(community["members"]),
                "message_count": len(community["messages"])
            }
            user_communities.append(community_info)
    
    return user_communities

def add_message_to_community(community_id, user_id, user_name, user_type, message):
    """Add a message to a community chat"""
    communities = load_data(COMMUNITIES_FILE)
    
    for community in communities:
        if community["id"] == community_id:
            community["messages"].append({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "user_name": user_name,
                "user_type": user_type,
                "content": message,
                "timestamp": datetime.now().isoformat()
            })
    
    save_data(communities, COMMUNITIES_FILE)

def get_community_details(community_id):
    """Get detailed information about a community"""
    communities = load_data(COMMUNITIES_FILE)
    
    for community in communities:
        if community["id"] == community_id:
            return community
    
    return None

def get_user_by_id(user_id, user_type):
    """Get user details by ID"""
    if user_type == "farmer":
        users = load_data(FARMERS_FILE)
    else:
        users = load_data(VENDORS_FILE)
    
    for user in users:
        if user["id"] == user_id:
            return user
    
    return None

# Streamlit app UI
st.title("Farmer-Vendor Communication App")

# Create initial data files if they don't exist
if not os.path.exists(FARMERS_FILE):
    save_data([], FARMERS_FILE)
if not os.path.exists(VENDORS_FILE):
    save_data([], VENDORS_FILE)
if not os.path.exists(COMMUNITIES_FILE):
    save_data([], COMMUNITIES_FILE)

# Sidebar with login, registration, and user info
with st.sidebar:
    st.header("User Panel")
    
    if st.session_state.current_user:
        user = get_user_by_id(st.session_state.current_user, st.session_state.current_user_type)
        st.success(f"Logged in as: {user['name']} ({st.session_state.current_user_type.capitalize()})")
        
        if st.button("Logout"):
            st.session_state.current_user = None
            st.session_state.current_user_type = None
            st.session_state.chat_community = None
            st.session_state.view = "communities"
            st.rerun()
            
        # Additional menu options
        if st.session_state.view == "chat" and st.session_state.chat_community:
            if st.button("Back to Communities List"):
                st.session_state.view = "communities"
                st.session_state.chat_community = None
                st.rerun()
    else:
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            st.subheader("Login (Demo)")
            login_type = st.selectbox("I am a:", ["Farmer", "Vendor"], key="login_type")
            
            users = load_data(FARMERS_FILE if login_type.lower() == "farmer" else VENDORS_FILE)
            user_names = [user["name"] for user in users]
            
            if user_names:
                selected_name = st.selectbox("Select your name:", user_names)
                selected_user = next((user for user in users if user["name"] == selected_name), None)
                
                if st.button("Login") and selected_user:
                    st.session_state.current_user = selected_user["id"]
                    st.session_state.current_user_type = login_type.lower()
                    st.rerun()
            else:
                st.info(f"No {login_type.lower()}s registered yet. Please register first.")
        
        with tab2:
            st.subheader("Register")
            reg_type = st.selectbox("I am a:", ["Farmer", "Vendor"], key="reg_type")
            name = st.text_input("Your Name")
            
            # For demo purposes, using a map would be better in a real app
            col1, col2 = st.columns(2)
            with col1:
                latitude = st.number_input("Latitude", value=28.6139, format="%.4f")
            with col2:
                longitude = st.number_input("Longitude", value=77.2090, format="%.4f")
            
            if st.button("Register") and name:
                user_id = register_user(reg_type.lower(), name, latitude, longitude)
                st.session_state.current_user = user_id
                st.session_state.current_user_type = reg_type.lower()
                st.success("Registration successful!")
                st.rerun()

# Main content area - Show different views based on login status
if not st.session_state.current_user:
    st.info("Please login or register to use the app")
    
    # Display some sample data for demo purposes
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Registered Farmers")
        farmers = load_data(FARMERS_FILE)
        if farmers:
            farmer_df = pd.DataFrame([{
                "Name": farmer["name"],
                "Location": f"{farmer['latitude']:.4f}, {farmer['longitude']:.4f}"
            } for farmer in farmers])
            st.dataframe(farmer_df)
        else:
            st.write("No farmers registered yet")
    
    with col2:
        st.subheader("Registered Vendors")
        vendors = load_data(VENDORS_FILE)
        if vendors:
            vendor_df = pd.DataFrame([{
                "Name": vendor["name"],
                "Location": f"{vendor['latitude']:.4f}, {vendor['longitude']:.4f}"
            } for vendor in vendors])
            st.dataframe(vendor_df)
        else:
            st.write("No vendors registered yet")

else:
    # User is logged in
    user = get_user_by_id(st.session_state.current_user, st.session_state.current_user_type)
    
    # Simplified view management
    if st.session_state.view == "communities":
        # Communities List View
        st.subheader("My Communities")
        user_communities = get_user_communities(st.session_state.current_user, st.session_state.current_user_type)
        
        if user_communities:
            for community in user_communities:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{community['name']}**")
                    st.write(f"Vendor: {community['vendor_name']} • Members: {community['member_count']} • Messages: {community['message_count']}")
                with col2:
                    if st.button("Open Chat", key=f"chat_{community['id']}"):
                        st.session_state.chat_community = community['id']
                        st.session_state.view = "chat"
                        st.rerun()
                st.divider()
        else:
            st.info("You're not part of any communities yet")
            
    elif st.session_state.view == "chat" and st.session_state.chat_community:
        # Chat View
        community = get_community_details(st.session_state.chat_community)
        
        if community:
            st.subheader(f"Chat: {community['name']}")
            
            # Display community info in expander
            with st.expander("Community Details"):
                st.write(f"Vendor: **{community['vendor_name']}**")
                
                # Display members
                st.write(f"**Members ({len(community['members'])})**")
                
                # Group members by type
                vendors = [m for m in community['members'] if m['type'] == 'vendor']
                farmers = [m for m in community['members'] if m['type'] == 'farmer']
                
                st.write(f"Vendor: {vendors[0]['name']}")
                st.write(f"Farmers: {len(farmers)}")
                
                # Show a sample of farmers with their distances
                if farmers:
                    farmer_df = pd.DataFrame([{
                        "Name": f["name"],
                        "Distance (km)": f.get("distance", "N/A")
                    } for f in farmers[:5]])  # Show only 5 farmers for brevity
                    
                    st.dataframe(farmer_df)
                    if len(farmers) > 5:
                        st.write(f"...and {len(farmers) - 5} more farmers")
            
            # Display chat messages
            st.divider()
            chat_container = st.container(height=400, border=True)
            
            with chat_container:
                for msg in community['messages']:
                    is_self = msg['user_id'] == st.session_state.current_user
                    
                    # Format message based on sender
                    if is_self:
                        st.markdown(f"""
                        <div style='display: flex; justify-content: flex-end;'>
                            <div style='background-color: #DDEBF7; padding: 10px; border-radius: 10px; max-width: 80%;'>
                                <p style='margin: 0; text-align: right;'>{msg['content']}</p>
                                <p style='margin: 0; font-size: 0.8em; color: #666; text-align: right;'>You - {msg['timestamp'].split('T')[1][:5]}</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        user_type_color = "#FFC107" if msg['user_type'] == "vendor" else "#4CAF50"
                        st.markdown(f"""
                        <div style='display: flex; justify-content: flex-start;'>
                            <div style='background-color: #F5F5F5; padding: 10px; border-radius: 10px; max-width: 80%;'>
                                <p style='margin: 0;'>{msg['content']}</p>
                                <p style='margin: 0; font-size: 0.8em;'>
                                    <span style='color: {user_type_color};'>{msg['user_name']} ({msg['user_type'].capitalize()})</span>
                                    <span style='color: #666;'> - {msg['timestamp'].split('T')[1][:5]}</span>
                                </p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Message input form
            st.divider()
            with st.form(key="message_form", clear_on_submit=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    message = st.text_input("Type a message:", key="message_input")
                with col2:
                    submit_button = st.form_submit_button("Send")
                
                if submit_button and message:
                    add_message_to_community(
                        community_id=st.session_state.chat_community,
                        user_id=st.session_state.current_user,
                        user_name=user['name'],
                        user_type=st.session_state.current_user_type,
                        message=message
                    )
                    st.rerun()
            
            # Button to go back to community list
            if st.button("← Back to Communities"):
                st.session_state.view = "communities"
                st.session_state.chat_community = None
                st.rerun()
        else:
            st.error("Community not found")
            st.session_state.view = "communities"
            st.session_state.chat_community = None
            st.rerun()

# Footer
st.divider()
st.caption("Farmer-Vendor Communication App - Demo Version")