import unicodedata
import pandas as pd
import shutil
import os
import base64
import re
import streamlit as st

# ----------------- Constants -----------------
VOCAB_FOLDER = "vocab_data"  # Folder to store all vocabulary-related CSV files
DIARY_FILE = "diary.csv"  # Main diary CSV file where user's words are stored
DIARY_BACKUP = "diary_backup.csv"  # Backup of the diary
VOCAB_COLUMNS = ["word_class", "english", "german", "past_tense", "perfect_tense"]  # Columns used in CSV files

# Regex pattern to validate words (letters, umlauts, ß, hyphens, apostrophes, spaces)
VALID_WORD = re.compile(r"^[A-Za-zÄÖÜäöüß'\- ]+$")

# Global flag to ensure diary backup is created only once per session
backup_created = False


# ----------------- Helper Functions -----------------
def normalize_string(s):
    """
    Normalize string to NFC form (composed Unicode form) for consistent comparison.
    """
    return unicodedata.normalize('NFC', str(s))


def check_char_input(word):
    """
    Validates character input from user.
    Returns normalized string if valid, None otherwise.
    Allows 'exit' command to quit program.
    """
    word = word.strip()
    if not word:
        return None
    if word.lower().startswith("exit"):
        exit(0)
    if not VALID_WORD.match(word):
        print("Please enter only letters, spaces, hyphens, or apostrophes.")
        return None
    return normalize_string(word)


def check_num_input(num):
    """
    Validates numeric input from user.
    Returns integer if valid, None otherwise.
    Allows 'exit' command to quit program.
    """
    if num.lower() == 'exit':
        exit(0)
    if num.isdigit():
        return int(num)
    else:
        print("Invalid input. Enter only numbers.")
        return None


def count(maximum):
    """
    Prompt user to enter number of words to test.
    Ensures input is between 1 and maximum allowed.
    """
    while True:
        user_input = check_num_input(
            input(f"\nHow many words would you like to take now? Enter a number between 1 and {maximum}: "))
        if user_input is not None and 1 <= user_input <= maximum:
            return user_input
        else:
            print(f"Please enter a valid number between 1 and {maximum}.")


def backup_diary_once():
    """
    Creates a backup of the diary CSV file if not already done.
    Ensures backup is created only once per session.
    """
    global backup_created
    diary_path = os.path.join(VOCAB_FOLDER, DIARY_FILE)
    backup_path = os.path.join(VOCAB_FOLDER, DIARY_BACKUP)
    if not backup_created and os.path.exists(diary_path):
        shutil.copy(diary_path, backup_path)
        print("\nBackup of your Diary has been created.")
        backup_created = True


# ----------------- Vocabulary Loader -----------------
def load_vocab_files(folder=VOCAB_FOLDER, diary_file=DIARY_FILE):
    """
    Loads all CSV vocabulary files from the folder.
    Marks the main diary file as editable.
    Returns a list of dictionaries containing file info.
    """
    vocab_files = []
    if not os.path.exists(folder):
        os.makedirs(folder)
    for file_name in os.listdir(folder):
        if file_name.endswith(".csv"):
            full_path = os.path.join(folder, file_name)
            editable = (file_name == diary_file)
            vocab_files.append({
                "name": file_name,
                "path": full_path,
                "editable": editable
            })
    return vocab_files


def load_csv(file_path, expected_columns=None):
    """
    Load CSV safely, skip malformed rows, and ensure all expected columns exist.
    """

    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=expected_columns if expected_columns else VOCAB_COLUMNS)
        df.to_csv(file_path, index=False, encoding='utf-8')
        return df

    try:
        df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip')
    except pd.errors.ParserError:
        st.warning(f"CSV {file_path} has malformed rows. Skipping bad lines.")
        df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip')

    # Ensure all expected columns exist
    cols_to_ensure = expected_columns if expected_columns else VOCAB_COLUMNS
    for col in cols_to_ensure:
        if col not in df.columns:
            df[col] = ""

    return df

def save_csv(df, file_path):
    """
    Saves a pandas DataFrame to a CSV file.
    """
    df.to_csv(file_path, index=False, encoding='utf-8')



#"C:\Users\Asus\PycharmProjects\My_German_Vocab_Game\German_Vocab_Game\images\moroccan-flower-dark.png"
def set_background(image_file):
    with open(image_file, "rb") as file:
        encoded = base64.b64encode(file.read()).decode()
    css = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/jpg;base64,{encoded}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def sidebar():
    st.set_page_config(page_title="Game Panel", layout="wide")

    sidebar_style = """
    <style>
    /* Sidebar background */
    section[data-testid="stSidebar"] {
        background-color: #173052;  /* Dark gray */
        color: white;              /* Text color */
    }
    </style>
    """

    st.markdown(sidebar_style, unsafe_allow_html=True)

set_background("images\main_page_bg.jpg")
sidebar()


st.markdown("<h1 style='text-align: center; font-weight: bold;'>My German Vocab Game</h1>",unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; font-style: italic;'>Welcome to the game!</h2>",unsafe_allow_html=True)

# Initialize the user_name in session state if it doesn't exist yet
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if "submit" not in st.session_state:
    st.session_state.submit = False

def handle_submit():
    st.session_state.submit = True

if not st.session_state.submit:
    user_name = st.text_input("Enter your name: ", key="user_name")
    submit_button = st.button("Submit", on_click=handle_submit)

else:
    st.markdown(f"<h2 style='text-align: center;'>👋 Hallo, <strong>{st.session_state.user_name}</strong>! Guten Tag 🌞</h2>",unsafe_allow_html=True)
    st.markdown("<div style='text-align: center; font-size: 18px;'>👉 <strong>Please select an action from the panel to your left!</strong> 🧭</div>",unsafe_allow_html=True)
