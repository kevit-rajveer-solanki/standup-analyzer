import streamlit as st
import requests
import pandas as pd

st.set_page_config(layout="wide", page_title="Standup Performance")
st.title("Standup Analytics")

with st.sidebar:
    st.header("Settings")
    token = st.text_input("Application Token", type="password")
    organizer = st.text_input("Organizer Email")
    link = st.text_area("Meeting Link", height=80)
    s_date = st.date_input("Start Date")
    e_date = st.date_input("End Date")
    btn = st.button("Generate Report", type="primary")

if btn and token and organizer and link:
    with st.spinner("Fetching timestamps..."):
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
                    st.warning("No data found.")
                else:
                    flat_data = []
                    total_meetings = len(data)
                    
                    for m in data:
                        for att in m['attendees']:
                            flat_data.append({
                                "Name": att['name'],
                                "Team": att['team'],
                                "Date": m['date'],
                                "Join Time": att['join_time'],
                                "Leave Time": att['leave_time'],
                                "OnTime": att['is_on_time']
                            })
                    
                    df = pd.DataFrame(flat_data)
                    
                    if df.empty:
                        st.warning("No attendees found.")
                    else:
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Total Meetings", total_meetings)
                        c2.metric("Total Unique People", df['Name'].nunique())
                        
                        
                        avg_punc = (df['OnTime'].sum() / len(df) * 100)
                        c3.metric("Overall Punctuality", f"{avg_punc:.1f}%")

                        st.divider()

                        # 2. Tabs
                        tab1, tab2, tab3 = st.tabs(["Performance Leaderboard", "Daily Timestamps", "Detailed List"])

                        with tab1:
                            stats = df.groupby(['Team', 'Name']).agg({
                                'Date': 'nunique',       
                                'OnTime': 'sum'          
                            }).reset_index()
                            
                            stats.rename(columns={'Date': 'Days Attended', 'OnTime': 'Days On Time'}, inplace=True)
                            
                            stats['Attendance %'] = (stats['Days Attended'] / total_meetings * 100).round(1)
                            stats['Punctuality %'] = (stats['Days On Time'] / stats['Days Attended'] * 100).fillna(0).round(1)
                            
                            st.subheader("Top 5 Consistent Members")
                            top_5 = stats.sort_values(by=['Attendance %', 'Punctuality %'], ascending=False).head(5)
                            st.dataframe(top_5.style.background_gradient(subset=['Attendance %'], cmap="Greens").format({'Attendance %': '{:.1f}%', 'Punctuality %': '{:.1f}%'}))

                            st.subheader("Bottom 5 Members")
                            bot_5 = stats.sort_values(by=['Attendance %', 'Punctuality %'], ascending=True).head(5)
                            st.dataframe(bot_5.style.background_gradient(subset=['Attendance %'], cmap="Reds_r").format({'Attendance %': '{:.1f}%', 'Punctuality %': '{:.1f}%'}))

                        with tab2:
                            st.subheader("Daily Join/Leave Logs")
                            
                            teams = sorted(df['Team'].unique())
                            selected_team = st.selectbox("Select Team:", ["All"] + list(teams))
                            view_df = df if selected_team == "All" else df[df['Team'] == selected_team]

                            view_df['Time Log'] = view_df['Join Time'] + " - " + view_df['Leave Time']
                            
                            try:
                                pivot_df = view_df.pivot_table(
                                    index=['Team', 'Name'], 
                                    columns='Date', 
                                    values='Time Log', 
                                    aggfunc='first'
                                ).fillna("Absent")
                                st.dataframe(pivot_df)
                            except:
                                st.dataframe(view_df[['Team','Name','Date','Join Time','Leave Time']])

                        with tab3:
                            st.subheader("Full Data Export")
                            st.dataframe(df)

        except Exception as e:
            st.error(f"Connection Error: {e}")