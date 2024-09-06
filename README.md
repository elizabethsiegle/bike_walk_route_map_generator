## ROUTEME

### Generate an optimal path on a map a la Traveling Salesman Problem to hit different landmarks in an input city using Cloudflare Workers AI (using LlaMA-3.1), LangChain (for prompt templates and comma separated list output parser), Mapbox to create a map and get information about cities and landmarks in those cities, and Folium to edit the map.    

![gif](https://private-user-images.githubusercontent.com/8932430/365003433-8225baa0-5779-4323-b080-2653e3354428.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MjU1ODc5NjcsIm5iZiI6MTcyNTU4NzY2NywicGF0aCI6Ii84OTMyNDMwLzM2NTAwMzQzMy04MjI1YmFhMC01Nzc5LTQzMjMtYjA4MC0yNjUzZTMzNTQ0MjgucG5nP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9QUtJQVZDT0RZTFNBNTNQUUs0WkElMkYyMDI0MDkwNiUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNDA5MDZUMDE1NDI3WiZYLUFtei1FeHBpcmVzPTMwMCZYLUFtei1TaWduYXR1cmU9MzBiMjE4NjVmNDhjYmU2YzNjNWEzZTBiNWQ3YjlhYmJkZjQxMjk0MWRlZGY0N2I0ODA2MWRlZGE0NDQ1MTc5MyZYLUFtei1TaWduZWRIZWFkZXJzPWhvc3QmYWN0b3JfaWQ9MCZrZXlfaWQ9MCZyZXBvX2lkPTAifQ.Wxb-7KMmCCA0sb_W013VJmNF2MZni6CIafGi3KHaJnA)

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
