# we will now integrate Streamlit with our app,
# connecting our Financial assistant with Front End.
import streamlit as st

from FinanceAssistantService import FAService

service = FAService()

st.set_page_config(page_title="Your Chat App", page_icon=":speech_balloon:")
st.title("🚀 AI Assistant: Your Interactive Financial Looker 🗨️")

with st.container():
    st.info("This is our Financial Chat Assistant!")

prompt = st.chat_input("Ask a question related to finance")
if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    res = service.run_assistant(prompt)
    with st.chat_message("assistant"):
        if res:
            st.markdown(res)
