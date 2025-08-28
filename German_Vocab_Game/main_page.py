import unicodedata
import pandas as pd
import shutil
import os
import ast
import re
import streamlit as st
import random

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


st.title("My German Vocab Game")
st.header("Welcome to the game!!")

# Initialize the user_name in session state if it doesn't exist yet
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

# Display the text input and button only if the name is not yet entered
if st.session_state.user_name == "":
    user_name = st.text_input("Enter your name: ")
    submit_button = st.button("Submit")

    # Update session state if the user submits their name
    if submit_button and user_name:
        st.session_state.user_name = user_name

# Greet the user after the name is entered
if st.session_state.user_name:
    st.write(f"\nHallo! {st.session_state.user_name}, Guten Tag")
    st.write(f"\nPlease select any action from the sidebar to your left <--")
