import streamlit as st
import requests
import pandas as pd

st.set_page_config(layout="wide", page_title="Standup Performance")
st.title("Standup Performance Analytics")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    token = st.text_input("Application Token", type="password")
    organizer = st.text_input("Organizer Email")
    link = st.text_area("Meeting Link", height=80)
    s_date = st.date_input("Start Date")
    e_date = st.date_input("End Date")
    btn = st.button("Generate Report", type="primary")

if btn and token and organizer and link:
    with st.spinner("Analyzing..."):
        try:
            payload = {
                "token": token,
                "start_date": str(s_date),
                "end_date": str(e_date),
                "organizer_email": organizer,
                "meeting_link": link
            }
            res = requests.post("http://localhost:8000/analyze", json=payload)
            
            if res.status_code != 200:
                st.error(f"Error: {res.text}")
            else:
                data = res.json()
                if not data:
                    st.warning("No meetings found in this period.")
                else:
                    # --- DATA PROCESSING ---
                    flat_data = []
                    total_meetings = len(data)
                    
                    for m in data:
                        for att in m['attendees']:
                            flat_data.append({
                                "Name": att['name'],
                                "Team": att['team'],
                                "Date": m['date'],
                                "OnTime": att['is_on_time'] # <--- NEW
                            })
                    
                    if not flat_data:
                        st.warning("Meetings found, but no attendees.")
                    else:
                        df = pd.DataFrame(flat_data)
                        
                        
                        stats = df.groupby(['Team', 'Name']).agg({
                            'Date': 'nunique',
                            'OnTime': 'sum' 
                        }).reset_index()
                        
                        stats.rename(columns={'Date': 'Days Attended', 'OnTime': 'Days On Time'}, inplace=True)
                        
                        stats['Attendance %'] = (stats['Days Attended'] / total_meetings * 100).round(1)
                        stats['Punctuality %'] = (stats['Days On Time'] / stats['Days Attended'] * 100).fillna(0).round(1)
                        
                        sorted_df = stats.sort_values(by='Attendance %', ascending=False)
                        top_5 = sorted_df.head(5)
                        bottom_5 = sorted_df.tail(5)

                        
                        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                        kpi1.metric("Total Meetings", total_meetings)
                        kpi2.metric("Total People", df['Name'].nunique())
                        avg_dur = sum(m['duration'] for m in data) / total_meetings
                        kpi3.metric("Avg Duration", f"{avg_dur:.1f} min")
                        avg_punc = stats['Punctuality %'].mean()
                        kpi4.metric("Team Punctuality", f"{avg_punc:.1f}%")

                        st.divider()

                        tab1, tab2 = st.tabs(["Performance Analytics", "Team Report"])
                        
                        with tab1:
                            st.subheader("Top 5")
                            st.dataframe(
                                top_5[['Name', 'Team', 'Attendance %', 'Punctuality %']]
                                .style.background_gradient(subset=['Attendance %'], cmap="Greens")
                                .format({'Attendance %': '{:.1f}%', 'Punctuality %': '{:.1f}%'})
                            )
                            
                            st.divider()
                            
                            st.subheader("Bottom 5")
                            st.dataframe(
                                bottom_5[['Name', 'Team', 'Attendance %', 'Punctuality %']]
                                .style.background_gradient(subset=['Attendance %'], cmap="Reds_r") # Red for low
                                .format({'Attendance %': '{:.1f}%', 'Punctuality %': '{:.1f}%'})
                            )

                        with tab2:
                            st.subheader("Full Team Breakdown")
                            unique_teams = stats['Team'].unique()
                            for team in unique_teams:
                                with st.expander(f"Team: {team}", expanded=False):
                                    team_data = stats[stats['Team'] == team]
                                    st.dataframe(
                                        team_data[['Name', 'Days Attended', 'Attendance %', 'Punctuality %']]
                                        .style.background_gradient(subset=['Attendance %'], cmap="Blues")
                                        .format({'Attendance %': '{:.1f}%', 'Punctuality %': '{:.1f}%'})
                                    )

        except Exception as e:
            st.error(f"Connection Error: {e}")