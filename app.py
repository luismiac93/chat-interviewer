from openai import OpenAI
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="OpenAI Streamlit App", page_icon="🤖")

st.title("OpenAI Streamlit Chatbot App")

if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0 
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "messages" not in st.session_state:
    st.session_state["messages"] = [] 
if "chat_completed" not in st.session_state:
    st.session_state.chat_completed = False 

def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True    

if not st.session_state.setup_complete:
    ### Ask for the user information
    st.subheader("Personal Information", divider='rainbow')

    if "name" not in st.session_state:
        st.session_state["name"] = ""
    if "experience" not in st.session_state:
        st.session_state["experience"] = ""
    if "skills" not in st.session_state:
        st.session_state["skills"] = ""

    st.session_state["name"] = st.text_input(label ="Name", max_chars = 40, value=st.session_state["name"], placeholder = "Enter your name")

    st.session_state["experience"] = st.text_area(label ="Experience", value=st.session_state["experience"], height=200, max_chars = None, placeholder = "Describe your experience")

    st.session_state["skills"] = st.text_area(label ="Skills", value=st.session_state["skills"], height=200, max_chars = None, placeholder = "List your skills")

    # st.write(f"**Your Name**: {st.session_state['name']}")
    # st.write(f"**Your Experience**: {st.session_state['experience']}")
    # st.write(f"**Your Skills**: {st.session_state['skills']}")

    st.subheader("Company and Position", divider='rainbow')

    if "level" not in st.session_state:
        st.session_state["level"] = "Intern"
    if "position" not in st.session_state:
        st.session_state["position"] = "Data Scientist"
    if "company" not in st.session_state:
        st.session_state["company"] = "Google"

    col1, col2 = st.columns(2)

    with col1:
         st.session_state["level"]  = st.radio("Choose level", key="visibility", options = ["Intern", "Junior", "Mid", "Senior", "Lead"])

    with col2:
         st.session_state["position"] = st.selectbox("Choose position", ("Data Scientist", "Data Engineer", "ML Engineer", "AI Researcher"))

    st.session_state["company"] = st.selectbox("Choose company", ("Google", "Facebook", "Amazon", "Apple", "Microsoft", "Netflix", "Other"))

    # st.write(f"You are applying for a {st.session_state["level"]} {st.session_state["position"]} position at {st.session_state["company"]}")

    if st.button("start interview", on_click=complete_setup):
        st.write("Setup complete. You can start the interview now.")


if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_completed:

    st.info("""Start by introducing yourself and why you are a good fit for the position.""", icon="👋🏻")

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4o"

    if not st.session_state.messages:
        st.session_state["messages"] = [
            {"role": "system", "content": f"""
            You are an HR executive for the company {st.session_state["company"]}. You are interviewing a user name {st.session_state["name"]} for the position at level {st.session_state["level"]}.
            The interviewee has the following experience: {st.session_state["experience"]}.

            The interviewee has the following skills: {st.session_state["skills"]}.
            """}
        ] 

        data = """
            Use these details to create two of your questions: {Questions}.

            Chat history: {Chat_history}
            """

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])    

    if st.session_state.user_message_count < 5:
        if prompt := st.chat_input("Your answer. ", max_chars =1000):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                if st.session_state.user_message_count < 4:
                    with st.chat_message("assistant"):
                        stream = client.chat.completions.create(
                            model=st.session_state["openai_model"],
                            messages=[
                                {"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]
                            ],
                            stream=True,
                        )
                        response = st.write_stream(stream)
                    st.session_state.messages.append({"role": "assistant", "content": response})    
                
                st.session_state.user_message_count += 1

    if st.session_state.user_message_count >= 5:
        st.session_state.chat_completed = True

if st.session_state.chat_completed and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click=show_feedback):
        st.write("Fetching feedback...")

if st.session_state.feedback_shown:
    st.subheader("Interview Feedback", divider='rainbow')

    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state["messages"] if msg["role"] != "system"])

    feedback_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    feedback_completion = feedback_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": """You are a helpful tool that provides feedback on interview performance.
             Before the Feedback give a score from 1 to 10, where 10 is the best.
             Fllow this format:
             Overall Score: X/10 //Your score
             Feedback: //here you put your feedback
             Give only the feedback do not ask any additional questions.
             """},
            {"role": "user", "content": f"This is the interview you need to evaluate. Keep in mind that you are only a tool. And you shouldn't engage in any converstation: {conversation_history}"}
        ]
    )

    st.write(feedback_completion.choices[0].message.content)
    
    if st.button("Restart Interview", type="primary"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")