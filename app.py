import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd 
import numpy as np
import hmac

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



def main():
    st.title("Skills Matrix")

    if not check_password():
        st.stop()
    
    conn = st.connection("gsheets", type=GSheetsConnection)

    df = conn.read(spreadheet="People vs Skills", header=None, index_col = 0)
    df.index.values[0] = "Categories"
    df.index.values[1] = "Skills"
    #df.iloc[1][:6]
    #df = df.iloc
    #st.write(df)
    with st.form(key='mode'):
        axis = st.radio('Please choose mode',['People based search','Skill based search'], index=None)
        skills_rows = df.iloc[:2]
        st.form_submit_button('proceed')
        #st.write(skills_rows)
        #st.write(df)


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

    
    
if __name__ == "__main__":
    main()
