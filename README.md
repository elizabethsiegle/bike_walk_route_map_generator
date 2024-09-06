## ROUTEME

### Generate an optimal path on a map a la Traveling Salesman Problem to hit different landmarks in an input city using Cloudflare Workers AI (using LlaMA-3.1), LangChain (for prompt templates and comma separated list output parser), Mapbox to create a map and get information about cities and landmarks in those cities, and Folium to edit the map.    


1. Enter a city🏙️ you wish to visit
-> get a few must-visit landmarks in your chosen city
2. Pick the landmarks🌁🗽 you want to visit.
3. Generate the shortest path between these landmarks.
4. Explore! 🗺️

You'll need 
- a Mapbox access token--[get it here](https://docs.mapbox.com/help/getting-started/access-tokens/)
- your Cloudflare Account ID (the number/character sequence following https://dash.cloudflare.com/ when you login) 
- a Cloudflare Workers AI API key (in your Cloudflare account dashboard, click AI on the lefthand side under R2, then <em>Use REST API</em>, then <em>Create a Workers AI API token</em>)

Download the `requirements.txt` and run `pip install`. Some main libraries this app uses includes LangChain, markdown, pandas, geopy, requests, streamlit, streamlit_searchbox, folium, typing, uuid, streamlit_folium, and folium.plugins (among others.)

Run on the command line with `streamlit run app.py`. 
