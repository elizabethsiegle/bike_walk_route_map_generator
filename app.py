from dotenv import load_dotenv
from geopy import distance
import io
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain_community.llms.cloudflare_workersai import CloudflareWorkersAI
import markdown
import os
import pandas as pd
import polyline
import requests
import streamlit as st
from streamlit_searchbox import st_searchbox
from typing import List
import uuid
import folium
from streamlit_folium import folium_static

# Display the title and description
st.title('Route Me🚴‍♀️🚶‍♀️‍➡️🏃‍♀️')

st.markdown("""
    <style>
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #f1f1f1;
            text-align: center;
            padding: 10px 0;
            color: #000;
            font-size: 14px;
            box-shadow: 0 -2px 5px rgba(0,0,0,0.1);
        }
        .content {
            padding-bottom: 150px; /* Adjust this value to create space between content and footer */
        }
    </style>
""", unsafe_allow_html=True)
# Footer HTML
footer_html = """
    <div class="footer">
        Made with ❤️ in SF🌉
    </div>
"""

# Inject the footer into the app
st.markdown(footer_html, unsafe_allow_html=True)

# Define markdown content directly
markdown_content = """
This app uses [Cloudflare Workers AI](https://developers.cloudflare.com/workers-ai/), [LangChain](https://langchain.dev/),  location data/maps from [Folium](https://python-visualization.github.io/folium/latest/), and [Streamlit](https://streamlit.io/)/[Streamlit Folium](https://folium.streamlit.app/) to tackle the Traveling Salesman problem!

1. Enter a city🏙️ you wish to visit
-> get 7 must-visit landmarks in your chosen city
2. Pick the landmarks🌁🗽 you want to visit.
3. Generate the shortest path between these landmarks.
4. Explore! 🗺️
"""
st.markdown(markdown_content)

# Load environment variables
load_dotenv()
mapbox_token = st.secrets["MAPBOX_TOKEN"] # os.environ.get('MAPBOX_TOKEN')
cf_account_id = st.secrets["CLOUDFLARE_ACCOUNT_ID"]# os.environ.get('CLOUDFLARE_ACCOUNT_ID')
cf_api_token = st.secrets["CLOUDFLARE_API_TOKEN"] # os.environ.get('CLOUDFLARE_API_TOKEN')

token = str(uuid.uuid4())

# find cities
def find_city(city_inp: str) -> List[tuple]:
    if len(city_inp) < 3:
        return []
    
    url = "https://api.mapbox.com/search/searchbox/v1/suggest"
    params = {"q": city_inp, "access_token": mapbox_token, "session_token": token, "types": "place"}
    
    res = requests.get(url, params=params)
    if res.status_code != 200:
        return []
    
    try:
        suggestions = res.json().get('suggestions', [])
        results = []
        for s in suggestions:
            print(f"s[name] {s['name']} s[place_formatted] {s['place_formatted']}")
            results.append((f"{s['name']}, {s['place_formatted']}", s['mapbox_id']))

        return results
    except Exception as e:
        st.error(f"Error fetching city suggestions: {e}")
        return []

# Function to retrieve city details
@st.cache_data
def retrieve_city(id):
    url = f"https://api.mapbox.com/search/searchbox/v1/retrieve/{id}"
    params = {"access_token": mapbox_token,"session_token": token}
    res = requests.get(url, params=params)
    if res.status_code != 200:
        return []
    try:
        features = res.json().get('features', [])
        if not features:
            st.warning("No features returned for the city.")
            return []
        return features[0]
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return []

# Function to retrieve landmark details
@st.cache_data
def retrieve_landmark(name, proximity):
    mapbox_url = "https://api.mapbox.com/search/searchbox/v1/forward"
    params = {"access_token": mapbox_token, "q": name, "proximity": proximity, 'types': 'poi', 'poi_category': 'tourist_attraction,museum,monument,historic,park,church,place_of_worship'}
    
    res = requests.get(mapbox_url, params=params)
    print(f'res.json {res.json()}')
    if res.status_code != 200:
        return []
    
    try:
        return res.json()['features'][0]
    except Exception as e:
        print(f"Error retrieving landmark: {e}")
        return []

# find city w/ searchbox
city_id = st_searchbox(find_city, key="city")

# Function to make landmark chain
@st.cache_resource
def lmchain():
    outp_parser = CommaSeparatedListOutputParser()
    form_instructions = outp_parser.get_format_instructions()
    
    llm = CloudflareWorkersAI(account_id=cf_account_id, api_token=cf_api_token)
    prompt = PromptTemplate(
        template="""Return a comma-separated list of the 7 best landmarks in {city}. Only return the list. {form_instructions}""",
        input_variables=["city"],
        partial_variables={"form_instructions": form_instructions},
    )
    
    chain = LLMChain(llm=llm, prompt=prompt, output_parser=outp_parser)
    return chain

# Function to get landmark locations
@st.cache_data
def get_landmarks(landmarks, long_city, lat_city):
    data = []
    for lm in landmarks:
        features = retrieve_landmark(lm, f"{long_city},{lat_city}")
        if not features:
            continue
        
        coor = features['geometry']['coordinates']
        long, lat = coor
        dist = distance.distance((lat_city, long_city), (lat, long)).km
        
        if dist <= 7:
            data.append([lm, long, lat, True])
    
    return pd.DataFrame(data=data, columns=['Name', 'longitude', 'latitude', 'Include'])

@st.cache_data
def travelingsalesman(chosen_landmarks):
    profile = "mapbox/cycling"
    coordinates = ";".join([f"{row['longitude']},{row['latitude']}" for _, row in chosen_landmarks.iterrows()])
    
    url = f"https://api.mapbox.com/optimized-trips/v1/{profile}/{coordinates}"
    params = {"access_token": mapbox_token, "geometries": "geojson"}  # Request GeoJSON format
    
    res = requests.get(url, params=params)
    if res.status_code != 200:
        st.error(f"Error: API request failed with status code {res.status_code}")
        return None, []
    
    try:
        json_response = res.json()
        
        if 'trips' not in json_response or not json_response['trips']:
            st.error("Error: No trips found in the API response")
            return None, []
        
        trip = json_response['trips'][0]
        
        if 'geometry' not in trip:
            st.error("Error: No geometry found in the trip data")
            return None, []
        
        geometry = trip['geometry']
        
        if isinstance(geometry, dict) and 'coordinates' in geometry:
            optimized_coords = [(coord[1], coord[0]) for coord in geometry['coordinates']]
            return json_response, optimized_coords
        else:
            st.error("Error: Unexpected geometry format in the API response")
            return None, []
    except Exception as e:
        st.error(f"Error in travelingsalesman: {str(e)}")
        st.write("JSON Response:", json_response)  # Debug: Print the JSON response
        return None, []

def create_route_map(landmarks, optimized_coords):
    # Create a map centered on the mean of all coordinates
    all_lats = landmarks['latitude'].tolist() + [coord[0] for coord in optimized_coords]
    all_lons = landmarks['longitude'].tolist() + [coord[1] for coord in optimized_coords]
    center_lat = sum(all_lats) / len(all_lats)
    center_lon = sum(all_lons) / len(all_lons)
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
    
    # Add markers for each landmark
    for _, row in landmarks.iterrows():
        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=row['Name']
        ).add_to(m)
    
    # Add the optimized route line if coordinates are available
    if optimized_coords:
        folium.PolyLine(
            optimized_coords,
            weight=6,
            color='red',
            opacity=0.8
        ).add_to(m)
    else:
        st.warning("No optimized route available. Displaying landmarks only.")
    
    # Fit the map to the bounds of all coordinates
    sw = min(all_lats), min(all_lons)
    ne = max(all_lats), max(all_lons)
    m.fit_bounds([sw, ne])
    
    return m

# Function to create a bike route
@st.cache_data
def make_route(city, landmarks, _llm):
    prompt = PromptTemplate(
        template="""You are an experienced tour guide in {city}. You love telling more about landmarks in a short way. Create a bike route for {city} in markdown, using headings with ##, passing by the following landmarks: {landmarks}. End with the introduction of the next landmark {end}, as if it was the next destination, but don't discuss it.""",
        input_variables=["landmarks", "city", "end"]
    )
    chain = LLMChain(llm=_llm, prompt=prompt)
    landmarks_string = "\n".join([f"{row['Name']}" for _, row in landmarks.iloc[:5, :].iterrows()])
    
    # Handle case where there are fewer than 6 landmarks
    if len(landmarks) < 6:
        part_one = chain.run({'city': city, 'landmarks': landmarks_string, 'end': ""})
        return part_one
    else:
        part_one = chain.run({'city': city, 'landmarks': landmarks_string, 'end': landmarks.iloc[5]['Name']})
    
    prompt = PromptTemplate(
        template="""You are an experienced tour guide in {city}. You love telling more about landmarks in a short way. Create a bike route for {city} in markdown, using headings with ##, passing by the following landmarks: {landmarks}. Start your explanation with 'Continuing from {previous}'.""",
        input_variables=["landmarks", "city", "previous"]
    )
    
    chain = LLMChain(llm=_llm, prompt=prompt)
    landmarks_string = "\n".join([f"{row['Name']}" for _, row in landmarks.iloc[5:, :].iterrows()])
    part_two = chain.run({'city': city, 'landmarks': landmarks_string, 'previous': landmarks.iloc[4]['Name']})
    
    return part_one + " " + part_two

# Function to convert markdown data to HTML
@st.cache_data
def to_html(data, filename='route'):
    return markdown.markdown(data)

# New function to convert Folium map to HTML string
def map_to_html(map_object):
    map_html = io.BytesIO()
    map_object.save(map_html, close_file=False)
    return map_html.getvalue().decode()

if 'route' not in st.session_state:
    st.session_state.route = None

# Function to generate a bike route
def gen_route(city, stops):
    route = make_route(city['properties']['full_address'], stops, CloudflareWorkersAI(account_id=cf_account_id, api_token=cf_api_token))
    st.session_state.route = route

def create_route_map(landmarks, optimized_coords):
    # Create a map centered on the first landmark
    m = folium.Map(location=[landmarks.iloc[0]['latitude'], landmarks.iloc[0]['longitude']], zoom_start=12)
    
    # Add markers for each landmark
    for _, row in landmarks.iterrows():
        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=row['Name'],
            tooltip=row['Name']
        ).add_to(m)
    
    # Add the optimized route line if coordinates are available
    if optimized_coords:
        folium.PolyLine(
            optimized_coords,
            weight=2,
            color='red',
            opacity=0.8
        ).add_to(m)
    else:
        st.warning("No optimized route available. Displaying landmarks only.")
    
    return m

# Update the main app logic
# Update the main app logic
if city_id:
    city = retrieve_city(city_id)
    if city:
        coords = city['geometry']['coordinates']
        long, lat = coords
        landmarks = lmchain().run({"city": city['properties']['full_address']})
        
        if 'landmark_locations' not in st.session_state:
            st.session_state.landmark_locations = get_landmarks(landmarks, long, lat)

        user_inp = st.data_editor(
            st.session_state.landmark_locations,
            hide_index=True,
            disabled=('Name', 'longitude', 'latitude'),
            column_config={'longitude': None, 'latitude': None},
            key='user_input',
            use_container_width=True
        )

        st.session_state.landmark_locations.update(user_inp)

        selected_landmarks = st.session_state.landmark_locations[st.session_state.landmark_locations['Include']]
        
        output, optimized_coords = travelingsalesman(selected_landmarks)
        if output is not None and optimized_coords:
            dist = output['trips'][0]['distance']
            conv_fac = 0.000621371
            miles = dist * conv_fac
            st.write(f"Total distance: {miles:.3f} mi")
            
            waypoints = [wp['waypoint_index'] for wp in output['waypoints']]
            stops = selected_landmarks.iloc[waypoints, :]
            
            # Store the route map in session state
            st.session_state.route_map = create_route_map(stops, optimized_coords)
            
            # Display the route map
            folium_static(st.session_state.route_map)
            
            st.button('Generate route!', on_click=lambda: gen_route(city, stops))
        else:
            st.error("Unable to generate the optimized route. Please try again or select different landmarks.")

# Show generated route and offer map download
if 'route' in st.session_state and st.session_state.route:
    route = st.session_state.route
    st.markdown(route)
    
    # Offer route map download if available
    if 'route_map' in st.session_state:
        map_html = map_to_html(st.session_state.route_map)
        st.download_button(
            label='Download Route Map',
            data=map_html,
            file_name='route_map.html',
            mime='text/html'
        )
    
    # Offer route description download
    route_html = to_html(route)
    st.download_button(
        label='Download the route description!',
        data=route_html,
        file_name='cf-workers-ai-tourist-route.html',
        mime='text/html'
    )
st.markdown('</div>', unsafe_allow_html=True)
# Footer HTML
footer_html = """
    <div class="footer">
        Made with ❤️ in SF🌉
    </div>
"""

# Inject the footer into the app
st.markdown(footer_html, unsafe_allow_html=True)