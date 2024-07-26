import streamlit as st
import pandas as pd
import hmac
import gspread
import numpy as np
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials


def mk_skills_dict(skills_rows):
    skills_dict = {None:[]}
    skills_rows=skills_rows[6:]
    #print(skills_rows)
    for i in skills_rows.iterrows():
        try:
            skills_dict[i[1][0].strip()].append(i[1][1].strip())
        except:
            skills_dict[i[1][0].strip()] = [i[1][1].strip()]
    return skills_dict

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

def load_data(spreadheet, worksheet):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope)
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_url(spreadheet)
    print(worksheet)
    worksheet = spreadsheet.worksheet(worksheet)  # or use spreadsheet.worksheet("Sheet Name")
    data = worksheet.get_all_values()
    df = pd.DataFrame([i[1:] for i in data], index=[i[0] for i in data])  # Using the first row as header
    return df

def load_skills_data(spreadheet, worksheet):
    df = load_data(spreadheet, worksheet)
    df.index.values[0] = "Categories"
    df.index.values[1] = "Skills"
    return df

def load_engagement_data(spreadheet, worksheet):
    df = load_data(spreadheet, worksheet)
    metadata = list(df.loc["Name"][:10])
    df.columns = metadata + list(df.loc["SORT BY COLUMN:"][10:])
    df = df.iloc[4:]
    #df.replace('',np.nan, inplace=True) #probably not needed
    df = df[df.index != '']

    #current_year = datetime.now().year
    #date_format = "%Y-%m-%d"
    #df.columns = list(df.columns[:11]) + list(pd.to_datetime([f'{current_year}-{i}' for i in df.columns[11:]], format=date_format))

    return df, metadata

def skills_view(df):
    with st.expander("Raw data"):
        st.write(df)
    with st.form(key='mode'):
        axis = st.radio('Please choose mode',['People based search','Skill based search'], index=None)
        skills_rows = df.iloc[:2]
        st.form_submit_button('proceed')


    if axis == 'People based search':
        person = st.selectbox('Please select the person to describe',df.index, index=None)
        if axis and person:
            st.write(person)
            person_df = pd.concat([skills_rows, df.loc[[person]]], ignore_index=True)
            df_cleaned = person_df.dropna(axis=1, subset=[2])
            df_cleaned = df_cleaned.T[6:]
            df_cleaned = df_cleaned.style.map(lambda x: f"background-color: {'#C7F6C7' if str(x) in ['3','4','5'] else '#eded82' if str(x)=='2' else 'white'}")
            st.write(df_cleaned)

    if axis == 'Skill based search':
        with st.form(key='skills'):
            skills_df = skills_rows[skills_rows.columns[6:]]
            skills_dict = mk_skills_dict(skills_df.T)
            category = st.selectbox('Select Skills Category',skills_dict.keys(), index = None)
            st.form_submit_button('proceed')
        with st.form(key='skills2'):
            skill = st.multiselect('Select Skill', skills_dict[category])
            st.form_submit_button('proceed')


        for s in skill:
            print(s)
            st.write(s)
            short_list = df.T.loc[df.T['Skills'] == s]
            short_list.dropna(axis=1, inplace=True)
            if short_list.empty:
                continue
            short_list = short_list[short_list.columns[2:]]
            short_list = short_list.T.style.map(lambda x: f"background-color: {'#C7F6C7' if str(x) in ['3','4','5'] else '#eded82' if str(x)=='2' else 'white'}")
            st.write(short_list)

def percent_to_float(x):
    if x == '':
        return np.nan  # Convert empty strings to NaN
    else:
        return float(x.strip('%')) / 100

def engagement_view(df, metadata):
    with st.expander("Raw data"):
        st.write(df)
    with st.form(key='people'):
        names = list(set(df.index))
        names.sort()
        name = st.multiselect('Select people to analyze', names)


        #min_date = df.columns[11:].min()
        #max_date = df.columns[11:].max()
        #print(min_date)
        #print(max_date)
        # Create the slider
        start_date, end_date = st.select_slider(
            "Select date range",
            options=df.columns[11:],
            value=[df.columns[11],df.columns[-1]])
        signed_only = st.checkbox('Include only SIGNED projects', value=True)
        st.form_submit_button('proceed')

    for i in name:
        short_df = df.loc[df.index == i]
        if signed_only:
            short_df = short_df.loc[short_df['Status'] =='Signed']
        filtered_df = short_df.loc[:, start_date:end_date]
        filtered_df = filtered_df.applymap(percent_to_float)
        write_df = pd.concat([short_df[['Project','Tribe']], filtered_df], axis=1)
        write_df.loc['Sum'] = write_df.sum(numeric_only=True)

        write_df.loc['Sum']['Project'] = ''
        write_df.loc['Sum']['Tribe'] = ''
        write_df = write_df.T
        st.write(write_df)


def highlight_summary_row(s):
    return ['background-color: #ffacac' if i > 1 else '#cbffbd' if i <= 0.5 else '' for i in range(len(s))]


def main():
    st.title("People Dashboard")
    if not check_password():
        st.stop()
    df_skills = load_skills_data(st.secrets["spreadsheet_skills"], "People vs Skills")
    df_engagement, metadata_engagement = load_engagement_data(st.secrets["spreadsheet_engagement"], "ALL Tribes")
    tab1, tab2 = st.tabs(['skills','engagement'])

    with tab1:
        skills_view(df_skills)

    with tab2:
        engagement_view(df_engagement, metadata_engagement)





if __name__ == "__main__":
    main()
