import streamlit as st
import os
from openai import AzureOpenAI
import random
from gtts import gTTS
import json
from datetime import datetime

# Set up Azure OpenAI API key and endpoint
os.environ["AZURE_OPENAI_API_KEY"] = st.secrets["AZURE_OPENAI_API_KEY"]

# Set base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Font size slider for dynamic adjustment
font_size = st.sidebar.slider("Adjust Font Size", min_value=10, max_value=40, value=20)

# Inject custom CSS to adjust font size dynamically based on slider
st.markdown(
    f"""
    <style>
    /* Dynamic font size adjustment for all text elements */
    .dynamic-font {{
        font-size: {font_size}px !important;
    }}

    /* Change background image */
    [data-testid="stAppViewContainer"] {{
        background-image: url("https://github.com/clarencemun/GA_capstone_taler_swift/blob/main/wallpaper5.jpg?raw=true");
        background-size: cover;
        background-position: center center;
        background-repeat: no-repeat;
        background-attachment: local;
    }}

    /* Adding semi-transparent backgrounds to text widgets for better readability */
    .stTextInput, .stTextArea, .stSelectbox, .stButton, .stSlider, .big-font, .stMarkdown, .stTabs, .stRadio {{
        background-color: rgba(255, 255, 255, 0.75); /* Semi-transparent white */
        border-radius: 5px; /* Rounded borders */
        padding: 5px; /* Padding around text */
        margin-bottom: 5px; /* Space between widgets */
        color: #333333; /* Dark grey font color */
    }}

    /* Style for big-font class used for larger text */
    .big-font {{
        font-size: 30px !important;
        font-weight: bold;
    }}

    </style>
    """,
    unsafe_allow_html=True
)

# Add app name with correct font size
st.markdown(f'<div class="dynamic-font" style="text-align: center;"><h1>Chapter Two</h1></div>', unsafe_allow_html=True)

# Add developer credit
st.markdown("""
    <div class="dynamic-font" style="text-align: left;">
        <p>Developed by Clarence Mun</p>
    </div>
""", unsafe_allow_html=True)

# Initialise Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=st.secrets["AZURE_ENDPOINT"],
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),  # Ensure API key is stored securely in environment variables
    api_version=st.secrets["AZURE_API_VERSION"]
)

# Define the list of available languages
languages = ['English', '中文', 'Melayu']

# Initialise message history
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []
if 'generated_story' not in st.session_state:
    st.session_state['generated_story'] = None

# Get language prefix for story generation
def get_language_prefix(language):
    if language == '中文':
        return "请用纯中文写一个故事"
    elif language == 'Melayu':
        return "Sila tulis cerita dalam bahasa Melayu penuh, tiada perkataan Inggeris"
    else:
        return "Create a story"

# Generate speech from text using gTTS
def generate_speech(text, filename='story.mp3', language='en', directory="audio"):
    directory = os.path.join(BASE_DIR, directory)
    if selected_language == '中文':
        language = 'zh'
    elif selected_language == 'Melayu':
        language = 'id'
    else:
        language = 'en'

    # Create the text-to-speech object
    myobj = gTTS(text=text, lang=language, slow=False)

    # Check if the directory exists, and create it if it doesn't
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # Generate a filename with a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"story_{timestamp}.mp3"
    file_path = os.path.join(directory, filename)

    # Save the converted audio
    myobj.save(file_path)

    # Play the converted file using 'open' on macOS
    st.audio(file_path, format='audio/mp3', start_time=0)

# Chat with the language model
def chat_with_model(input_text, language):
    message_history = st.session_state['message_history']
    language_prefix = get_language_prefix(language)
    full_input_text = f"{language_prefix} about {input_text}"
    message_history.append({'role': 'user', 'content': full_input_text})

    # Call the GPT model using the client object and handle response correctly
    response = client.chat.completions.create(
        model="gpt-4-0125-preview",  # Azure OpenAI model
        messages=message_history,
        temperature=0.7  # Adjust temperature as needed
    )

    # Accessing the response using the updated object structure
    response_text = response.choices[0].message.content
    message_history.append({'role': 'assistant', 'content': response_text})

    st.session_state['message_history'] = message_history
    return response_text

# Function to save a story to a JSON file
def save_story_to_json(story_data):
    # Specify the directory for saved stories
    stories_dir = os.path.join(BASE_DIR, "saved_stories")
    json_file_path = os.path.join(stories_dir, "stories.json")

    # Ensure the directory exists
    if not os.path.exists(stories_dir):
        os.makedirs(stories_dir)

    try:
        # Load existing data
        if os.path.exists(json_file_path):
            with open(json_file_path, "r") as file:
                data = json.load(file)
            data.append(story_data)
        else:
            data = [story_data]
        # Save updated data
        with open(json_file_path, "w") as file:
            json.dump(data, file, indent=4)
        st.success("Story saved successfully!")
    except Exception as e:
        st.error(f"Failed to save story: {e}")

# Function to load all stories from a JSON file
def load_stories_from_json():
    stories_dir = os.path.join(BASE_DIR, "saved_stories")
    json_file_path = os.path.join(stories_dir, "stories.json")
    try:
        if os.path.exists(json_file_path):
            with open(json_file_path, "r") as file:
                data = json.load(file)
            return data
        else:
            return []
    except Exception as e:
        st.error(f"Failed to load stories: {e}")
        return []

# Generate a story with the specified parameters
def generate_story(main_character, setting, conflict, resolution, moral, length_minutes, include_audio, selected_language):
    prompt = (
        f"Write an inspirational real-life story about second chances for ex-offenders. "
        f"The main character, {main_character}, faces the challenge of reintegrating into society. "
        f"The story is set in {setting}, focusing on the emotional struggles faced by both the main character and their family."
        f"The conflict revolves around {conflict}, but avoid graphic details. Emphasize emotional and psychological challenges."
        f"The resolution includes {resolution}, showing the power of rebuilding relationships and forgiveness."
        f"The moral of the story is '{moral}', encouraging second chances, forgiveness, and family unity."
        f"Ensure the story is appropriate for a secondary school audience, avoiding any traumatic content."
        f"Keep the story length to around {200 * length_minutes} words."
    )

    # Using the spinner to show processing state for story generation
    with st.spinner(f"Generating your story..."):
        story_text = chat_with_model(prompt, selected_language)
    
    if story_text:
        st.session_state['generated_story'] = story_text
        st.success("Story generated successfully!")

        # Prepare data to be saved
        story_data = {
            "main_character": main_character,
            "setting": setting,
            "conflict": conflict,
            "resolution": resolution,
            "moral": moral,
            "length_minutes": length_minutes,
            "text": story_text,
            "include_audio": include_audio,
            "language": selected_language
        }

        # Save the story data
        save_story_to_json(story_data)

        # Generating speech for the plain text
        if include_audio == "Yes":
            with st.spinner("Generating audio..."):
                generate_speech(story_text)
            st.success("Audio generated successfully!")
        
    else:
        st.error("The story generation did not return any text. Please try again.")

# Function to display the story
def display_story():
    if 'generated_story' in st.session_state and st.session_state['generated_story']:
        story_text = st.session_state['generated_story']
        # Display each paragraph of the story text with dynamic font size
        for paragraph in story_text.split('\n'):
            st.markdown(f'<div class="dynamic-font">{paragraph}</div>', unsafe_allow_html=True)

# Sidebar for input configuration (shared across tabs)
with st.sidebar:
    st.title("Configuration")
    selected_language = st.selectbox("Select Language:", languages)
    include_audio = st.radio("Include Audio?", ["No", "Yes"])
    length_minutes = st.slider("Length of story (minutes):", 1, 10, 5)

# Main tabs
tab1, tab2, tab3 = st.tabs(["Rebirth", "Renew", "Reflect"])

# Tab 1: Generate Random Story
with tab1:
    if st.button("Generate Random Story"):
        random_setting = 'Singapore'
        random_conflict = 'stigma faced by the family'
        random_resolution = 'forgiveness and rebuilding family bonds'
        random_moral = 'the power of second chances and family unity'
        generate_story("Kai", random_setting, random_conflict, random_resolution, random_moral, length_minutes, include_audio, selected_language)

# Tab 2: Generate Custom Story
with tab2:
    st.markdown("### Custom Story Mode")

    # Add a field for main character name, default to "Kai" if none provided
    main_character = st.text_input("Main character's name:", value="Kai")

    # Update the custom input fields to align with the second chances theme
    setting = st.text_input("Where the story takes place (setting):", value="within a family and community context")
    conflict = st.text_input(
        "Describe the emotional conflict:",
        help="Example: The stigma faced by the family, the emotional struggle of reintegrating into society, rebuilding trust."
    )
    resolution = st.text_input(
        "How is the conflict resolved?",
        help="Example: The family rebuilds relationships, focuses on forgiveness, and gains support from the community."
    )
    moral = st.text_input(
        "What is the moral of the story?",
        help="Example: The power of second chances, forgiveness, and the strength of family unity."
    )

    # Trigger the story generation when the button is clicked
    if st.button("Generate Custom Story"):
        generate_story(main_character, setting, conflict, resolution, moral, length_minutes, include_audio, selected_language)

# Tab 3: Display Previously Saved Stories
with tab3:
    st.write("(Story Archive)")
    previous_stories = load_stories_from_json()
    if previous_stories:
        for story in previous_stories:
            with st.expander(f"{story['main_character']} - {story['setting']}"):
                # Ensure each paragraph of saved stories is wrapped in dynamic font
                for paragraph in story["text"].split('\n'):
                    st.markdown(f'<div class="dynamic-font">{paragraph}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="dynamic-font">Setting: {story["setting"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="dynamic-font">Conflict: {story["conflict"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="dynamic-font">Resolution: {story["resolution"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="dynamic-font">Moral: {story["moral"]}</div>', unsafe_allow_html=True)
    else:
        st.write("No previous stories found.")

# Display the story if it exists in session state
display_story()
