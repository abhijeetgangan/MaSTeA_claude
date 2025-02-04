import streamlit as st
import pandas as pd
from io import StringIO
import anthropic

df_aq = pd.read_excel("all_QA.xlsx")
df_aq = df_aq.apply(lambda x: x.replace('\n', ''), axis=0)
list_of_topics = sorted(df_aq['TOPIC'].unique())

# Page configuration
st.set_page_config(page_title="MaSTeA for MaScQA", page_icon=":microscope:", layout="wide")

# Set up the title of the application
st.title('MaSTeA for MaScQA :microscope: :female-scientist:')
subtitle = r'''
$\textsf{
    \large \textbf{Ma}terials \textbf{S}cience \textbf{Te}aching \textbf{A}ssistant
}$
'''
st.write(f"{subtitle} ")

col1, col2 = st.columns((1,3))
col1.header("Settings")

question = ''

# Set up the title for second column
col2.header('Select your topic to study')

# Topic
topic = col2.selectbox(
   "Topics",
   options=sorted(df_aq['TOPIC'].unique()),
   index=0,  # Default value
   help="Select the material science topic"
)

question_list_matching = df_aq.loc[df_aq['TOPIC'] == topic]['QUESTION'].to_list()
question_type_matching = df_aq.loc[df_aq['TOPIC'] == topic]['Question Type'].to_list()

question_type_formated = []
for i, val in enumerate(question_type_matching):
    question_type_formated.append(f"{val}-{i+1}")
question_type_formated.insert(0, "Enter your own question")

question_selected = col2.selectbox(
   "List of question",
   options=question_type_formated,
   index=0,  # Default value
   help="Select the material science question and get the answer with steps"
)

col2.caption('MCQS - Multiple choice questions, MCQS-NUMS - Numerical MCQS, MATCH - Matching questions, NUM - Numerical questions')

system_prompt = "Solve the following question with highly detailed step by step explanation. Write the correct answer inside a dictionary at the end in the following format. The key 'answer' has a list which can be filled by all correct options or by a number as required while answering the question. For example for question with correct answer as option (a), return {'answer':[a]} at the end of solution. For question with multiple options'a,c' as answers, return {'answer':[a,c]}. And for question with numerical values as answer (say 1.33), return {'answer':[1.33]}"

# Select token length
token_length = col1.select_slider(
"Token length",
options=[256, 512, 1024, 2048],
value=256,  # Default value
)

model_option = col1.selectbox("Select a model", 
                                (
                                   "claude-3-5-sonnet-20240620",
                                   "claude-3-haiku-20240307", 
                                   "claude-3-sonnet-20240229", 
                                   "claude-3-opus-20240229", 
                                   "claude-2.1",
                                   "claude-2.0",
                                   "claude-instant-1.2",
                                ),
                                index=0,
                                placeholder="Select model")

text_input_container = col2.empty()
api = text_input_container.text_input("Enter api key")

if api != "":
    text_input_container.empty()
    api_hide = "\*"*len(api)
    col2.info(api_hide)

if not api:
    col2.warning("This model requires API key")

if question_selected == "Enter your own question":
    question_num = 0

if question_selected != "Enter your own question":
    question_num = int(question_selected.split("-")[-1])
    # Format text    
    col2.write_stream(question_list_matching[question_num - 1].removeprefix('[').removesuffix(']').replace("'"," ").replace(","," ").split("\\n"))
    question = ''.join(question_list_matching[question_num - 1].removeprefix('[').removesuffix(']').replace("'"," ").replace(","," ").split("\\n"))
    if col2.button('Get answer'):
        if len(question) != 0:
            client = anthropic.Anthropic(api_key = api)
            message = client.messages.create(
                    model=model_option,
                    max_tokens=token_length,
                    temperature=0,
                    top_p=0.9,
                    system = system_prompt, 
                    messages=[{"role": "user", "content": [ 
                        {"type": "text",
                        "text": question
                        }
                        ]}])
            model_output = message.content
            col2.write(f'{model_output[0].text}')
            answer_type_matching = df_aq.loc[df_aq['TOPIC'] == topic]['Correct Answer'].to_list()
            col2.markdown(f'Correct answer should be {answer_type_matching[question_num - 1]}')
# Read input
if question_selected == "Enter your own question":
    option = col2.radio("Input method",
                        ("Upload text file", "Enter text"),
                        index=1,
                        help="Choose whether to upload a text file containing your question or to enter the text manually.")
    
    if option == "Upload text file":
        uploaded_file = col1.file_uploader("Add text file containing question", type=["txt"])
        if uploaded_file:
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            string_data = stringio.read()
            col1.text_area("Uploaded Question:", value=string_data, height=150)
            question = string_data
        else:
            col1.warning("No file uploaded!")
    elif option == "Enter text":
        question = col2.text_area("Enter your question here:")

    if len(question) != 0:
        client = anthropic.Anthropic(api_key = api)
        message = client.messages.create(
                model=model_option,
                max_tokens=token_length,
                temperature=0,
                top_p=0.9,
                system = system_prompt, 
                messages=[{"role": "user", "content": [ 
                    {"type": "text",
                    "text": question
                    }
                    ]}])

    else:
        col2.warning("Empty string provided")        
    
    # Create a button that when clicked will output the LLMs generated output
    if col2.button('Generate output'):
        model_output = message.content
        # Display a generated output message below the button
        col2.write(f'{model_output[0].text}')
