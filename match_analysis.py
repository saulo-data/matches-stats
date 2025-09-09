#libraries
import streamlit as st
import pandas as pd
from pymongo import MongoClient, collection
import plotly.express as px

#connection
conn = st.secrets['url_con']
client = MongoClient(conn)
db = client.football_data
col = db.fotmob_stats

#list of the teams
cups = ['INT', 'INT-2']
leagues = col.find({'general.country': {"$nin": cups}}).distinct('general.league')
home_teams = col.distinct('teams.home.name')
away_teams = col.distinct('teams.away.name')
color_home = '#27e265'
color_away = '#d49115'

#function to get the data of the selected match
@st.cache_data(show_spinner=False)
def get_match(home: str, away: str) -> dict:
    match = col.find_one({'teams.home.name': home, 'teams.away.name': away})

    return match

#function to get complete names for teams
def get_teams_dict(venue: str, collection: collection, exclude: list) -> dict:
    teams_data = {}
    teams = list(collection.find({'general.country': {"$nin": exclude}}, {"general.country": 1, "general.league": 1, f"teams.{venue}.name": 1}))
    

    for team in teams:
        team_name = team['teams'][venue]['name']
        team_league = team['general']['league']
        team_country = team['general']['country']
        complete_name = f"{team_name} - {team_country}"
        if complete_name not in teams_data.keys():
            teams_data[complete_name] = {'country': team_country, 'league': team_league, 'name': team_name}
        else:
            continue
    
    return teams_data

def categorize_shot(shot):
        if shot >= 0.7:
            return 'High'
        elif 0.7 > shot >= 0.3:
            return 'Medium'
        else:
            return 'Low'

st.set_page_config(page_title='Match Plots', layout='wide')

#create a sidebar
with st.sidebar:
    st.image('static/image.png', 
             caption="Saulo Faria - Data Scientist Specialized in Football")
    st.write("This Web App was designed in order to get smart plots of a plethora of matches (current season). If you want to have more details about these matches, other stats, other seasons or believe I can help you in your project, send an email to saulo.foot@gmail.com. I'm always open to work.")

    st.subheader("My links (pt-br)")
    st.link_button("Instagram", "https://www.instagram.com/saulo.foot/", use_container_width=True)
    st.link_button("X", "https://x.com/fariasaulo_", use_container_width=True)
    st.link_button("Youtube", "https://www.youtube.com/channel/UCkSw2eyetrr8TByFis0Uyug", use_container_width=True)
    st.link_button("LinkedIn", "https://www.linkedin.com/in/saulo-faria-318b872b9/", use_container_width=True)

#page title
st.header('Plot the Stats of a Selected Match - Only National Leagues')
home_teams = get_teams_dict(venue='home', collection=col, exclude=cups)
away_teams = get_teams_dict(venue='away', collection=col, exclude=cups)
home_names = list(home_teams.keys())
away_names = list(away_teams.keys())

#form to select the teams
with st.form('my-form'):
    if 'home' not in st.session_state:
        st.session_state['home'] = home_teams[home_names[0]]['name']
    
    if 'away' not in st.session_state:
        st.session_state['away'] = away_teams[away_names[0]]['name']

    col1, col2 = st.columns(2)

    with col1:
        home = st.selectbox(label="Select a Home Team", options=home_names, index=0)
    
    with col2:
        away = st.selectbox(label="Select an Away Team", options=away_names, index=1)

    submitted = st.form_submit_button("Submit")

    if submitted:
        try:
            st.session_state['home'] = home_teams[home]['name']
            st.session_state['away'] = away_teams[away]['name']

            match = get_match(st.session_state['home'], st.session_state['away'])
            if not match:
                st.text("Maybe This Match Hasn't Ocurred Yet or the Teams Don't Belong to the Same National League")
            else:
                scoreline = f"{match['score']['home']} x {match['score']['away']}"
                match_details = f"{match['general']['country']} - {match['general']['league']} - Season {match['general']['season']}"

                stats = match['stats']

                df_stats = pd.DataFrame.from_dict(stats)
                df_stats['team'] = [st.session_state['home'], st.session_state['away']]
                df_stats = df_stats.melt(id_vars=['team'], value_vars=df_stats.columns)

                touch_100 = df_stats[df_stats['variable'] == 'touch_opp_box_100_passes']['value'].values

                df_stats = df_stats[df_stats['variable'] != 'touch_opp_box_100_passes']
                df_stats = df_stats.replace({
                    'ball_possession': 'Ball Poss', 
                    'passes_opp_half_%': 'Passes Opp Half %', 
                    'xg_op_for_100_passes': 'xG Open Play Per 100 Passes', 
                    'interceptions_perc': 'Interceptions %'
                })
                
                
                shots = match['shotmap']
                home_shots = pd.DataFrame.from_dict(shots['home'])
                home_shots['team'] = match['teams']['home']['name']
                away_shots = pd.DataFrame.from_dict(shots['away'])
                away_shots['team'] = match['teams']['away']['name']
                df_shots = pd.concat([home_shots, away_shots]).fillna(0)
                df_shots['size'] = [s + 0.05 for s in df_shots['xgot']]
                df_shots['efficiency_rate'] = (df_shots['xg'] + df_shots['xgot']) / 2

                st.subheader(match_details)
    
                col1, col2, col3 = st.columns([3, 12, 3], vertical_alignment='center', gap='large')

                with col1:
                    st.image(f"{match['teams']['home']['image']}", use_container_width=True)
                with col2:
                    st.markdown(f"<h1 style='text-align: center;'>{match['teams']['home']['name']} - {scoreline} - {match['teams']['away']['name']}</h1>", unsafe_allow_html=True)
                with col3:
                    st.image(f"{match['teams']['away']['image']}", use_container_width=True)
                

                fig = px.scatter(data_frame=df_shots, x='min', y='xg', color='team', color_discrete_sequence=[color_home, color_away], size='size',
                                    hover_name='team', hover_data={'xgot': True, 'team': False, 'player': True, 'type': True, 'situation': True, 'outcome': True, 'size': False},  
                                    range_y=[0, 1], title='xG by Minute and its xGOT (Size)', labels={'min': 'Minutes', 'xg': 'xG'}
                                    
                                 )
                fig.update_xaxes(tickvals=[0, 10, 20, 30, 40, 45, 50, 60, 70, 80, 90])
                fig.update_layout(legend_title_text='Squads')
                
                fig_bar = px.bar(data_frame=df_shots, x='situation', y='xg', color='team', color_discrete_sequence=[color_home, color_away], barmode='group', opacity=0.75, 
                                 title='xG By Situation', labels={'situation': '', 'xg': ''})
                fig_bar.update_layout(showlegend=False)

                fig_polar = px.line_polar(data_frame=df_stats, r='value', theta='variable', line_close=True, color='team', color_discrete_sequence=[color_home, color_away], 
                                          title='Main Stats of the Match')
                fig_polar.update_traces(fill='toself')
                fig_polar.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 1]  # Set the desired min and max values for the radial axis
                            )
                        ),
                        showlegend=False
                )    

                fig_box = px.box(data_frame=df_shots, x='team', y='efficiency_rate', color='team', color_discrete_sequence=[color_home, color_away], 
                                 title='Efficiency of the Shots (Mean Between xG and xGOT)', labels={'efficiency_rate': '', 'team': ''})
                fig_box.update_layout(showlegend=False)

                st.divider()

                st.plotly_chart(fig)

                st.divider()

                st.plotly_chart(fig_bar)

                st.divider()

                st.subheader("Touches on the Opponent Box per 100 Passes")

                col4, col5 = st.columns(2, vertical_alignment='center', border=True, gap='large')

                with col4:
                    st.metric(label=st.session_state['home'], value=touch_100[0])
                with col5:
                    st.metric(label=st.session_state['away'], value=touch_100[1])

                st.divider()

                col6, col7 = st.columns(2, vertical_alignment='center')                

                with col6:
                    st.plotly_chart(fig_polar)
                with col7:
                    st.plotly_chart(fig_box)            
            
        except Exception as e:
            st.text(e)
