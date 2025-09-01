import os

import streamlit as st
import random

import main_page as gs
import pandas as pd
gs.set_background("images\\test_page_bg.jpg")
gs.sidebar()
vocab_files = gs.load_vocab_files()
print(vocab_files)

# Initialize paths and dataframes
vocab_diary = None
vocab_backup = None
diary_path = None
backup_path = None
global ans_df, ques_df
for f in vocab_files:
    if f['name'] == 'diary.csv':
        diary_path = f['path']
        vocab_diary = gs.load_csv(diary_path)
    elif f['name'] == 'diary_backup.csv':
        backup_path = f['path']

# Initialize session state variables
if 'selected_words' not in st.session_state:
    st.session_state.selected_words = None
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'word_selection_done' not in st.session_state:
    st.session_state.word_selection_done = False  # Indicates if random words have been picked

def tester(vocab_data):
    global incorrect_ans_id, ques_for_users, rows_with_ans
    all_eng = [(index, row['word_class'], row['english']) for index, row in vocab_data.iterrows()]

    # Generate selected_words ONLY if they haven’t been selected yet
    if not st.session_state.get("word_selection_done", False):
        word_num = st.number_input(
            "How many words would you like to test?",
            min_value=0, max_value=len(all_eng), step=5
        )
        if st.button("Generate Words"):
            indices_all_eng = [row[0] for row in all_eng]
            st.session_state.selected_words = random.sample(indices_all_eng, word_num)
            st.session_state.word_selection_done = True
            st.write("✅ Words selected!")

    # Only proceed if words have been selected
    if st.session_state.get("word_selection_done", False) and st.session_state.selected_words:
        rows_with_ans = vocab_data.iloc[st.session_state.selected_words]
        ques_for_users = rows_with_ans.copy()

        # Replace answers with placeholders for user input
        for col in vocab_data.columns[2:]:  # assuming first 2 columns are index/word_class/english
            ques_for_users[col] = ques_for_users[col].apply(
                lambda x: '–' if pd.isna(x) or x in ["–", "-", ""] else ''
            )

        st.subheader("Questions Table")
        user_ans = st.data_editor(ques_for_users, num_rows="dynamic", use_container_width=True, key="diary_editor")

        # Submit button
        if st.button("Submit"):
            marks, correct_answers_id, incorrect_ans_id = compare_dataframes(rows_with_ans, user_ans)
            if marks > 0:
                st.write("Here is the correct answers for the questions for which your answers were wrong. Revise it!!")
                st.dataframe(revision(incorrect_ans_id, rows_with_ans))
                st.session_state.correct_rows = marks
                st.session_state.correct_answers_id = correct_answers_id
                st.session_state.awaiting_dairy_choice = True
            else:
                st.warning("No words were correct. Nothing to add to diary.")
                st.write("Here is the correct answers for the questions for which your answers were wrong. Revise it!!")
                st.dataframe(revision(incorrect_ans_id, rows_with_ans))
                # Reset selection to allow new test
                st.session_state.word_selection_done = False
                st.session_state.selected_words = None

    # Handle diary save if awaiting choice
    if st.session_state.get("awaiting_dairy_choice", False):
        dairy_status = add_words_to_dairy(st.session_state.correct_rows,st.session_state.correct_answers_id,vocab_data)
        st.write(f"Diary status: {dairy_status}. Click submit button again to continue. ")
    return None


def compare_dataframes(rows_with_answer, user_ans):
    correct_answers_id = []
    incorrect_answers_id = []

    if rows_with_answer.shape[0] != user_ans.shape[0]:
        st.error("Ques sheet doesn't have the same number of rows as answers.")
        return 0, []

    for row_id in rows_with_answer.index:
        ans_list = rows_with_answer.loc[row_id].tolist()
        user_ans_list = user_ans.loc[row_id].tolist()
        are_equal = all(
            a == b for a, b in zip(ans_list, user_ans_list)
            if a not in ["–", "-"] and b not in ["–", "-"]
        )
        if are_equal:
            correct_answers_id.append(row_id)
        else:
            incorrect_answers_id.append(row_id)
    #Score calculation
    log_score(rows_with_answer.shape[0], len(correct_answers_id))

    return len(correct_answers_id), correct_answers_id, incorrect_answers_id


def add_words_to_dairy(correct_rows, correct_answers_id, vocab_data):
    global diary_path, vocab_diary, backup_path

    st.write(f"📊 You got {correct_rows} words correct.")

    choice = st.radio("Do you want to add the correct answers to your diary?", ("select one", "Yes", "No"))

    if choice == "Yes":
        if vocab_diary is None:
            return "⚠️ 'diary.csv' not found. Cannot save your progress"

        # Backup
        if backup_path:
            gs.save_csv(vocab_diary, backup_path)
            st.info("🔄 Backup saved to 'diary_backup.csv'")
        else:
            st.warning("⚠️ Could not save backup. 'diary_backup.csv' not found.")
            backup_choice = st.radio("The current state of your diary cannot be backed up. Do you want to continue?",("select one", "Yes", "No"))
            if backup_choice == "No":
                return "Not adding anything to your diary"

        # Append correct answers safely
        for idx in correct_answers_id:
            new_row = vocab_data.loc[[idx]]  # keep as DataFrame
            new_row = new_row.reindex(columns=vocab_diary.columns, fill_value="")

            english_word = new_row["english"].iloc[0]
            if not (vocab_diary["english"] == english_word).any():
                vocab_diary = pd.concat([vocab_diary, new_row], ignore_index=True)

        # Save diary
        gs.save_csv(vocab_diary, diary_path)
        st.success(f"✅ Diary saved successfully at {diary_path}")
        st.write("Diary now has", len(vocab_diary), "rows")
        st.dataframe(vocab_diary.tail())

        # Reset state for new session
        st.session_state.word_selection_done = False
        st.session_state.selected_words = None
        st.session_state.awaiting_dairy_choice = False

        return "✅ Diary saved successfully!"

    elif choice == "No":
        st.session_state.word_selection_done = False
        st.session_state.selected_words = None
        st.session_state.awaiting_dairy_choice = False
        return "Not adding anything to your diary"

    return None

def revision(incorrect_answers_id, user_ques_list):
    revision_df = pd.DataFrame()
    for wrong_ans in incorrect_answers_id:
        revision_df = pd.concat([revision_df, user_ques_list.loc[wrong_ans]], ignore_index=True, axis=1)
    return revision_df.transpose()

def log_score(total, correct):
    from datetime import datetime
    score_file = os.path.join(gs.VOCAB_FOLDER, "score_history.csv")
    df = gs.load_csv(score_file, expected_columns=["Date", "ScorePercent", "TotalQuestions"])
    percent = round((correct/total)*100, 1) if total else 0
    df = pd.concat([df, pd.DataFrame([{
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ScorePercent": percent,
        "TotalQuestions": total
    }])], ignore_index=True)
    gs.save_csv(df, score_file)

# UI
st.title("This is the session to test new words")

# Load vocabulary files and filter out unwanted ones
vocab_files = gs.load_vocab_files()
vocab_files = [f for f in vocab_files if f['name'] not in ['diary_backup.csv', 'score_history.csv', 'achievements.csv']]

st.write("Available vocabulary files to learn from:")
file_options = []
for i, file_info in enumerate(vocab_files, start=1):
    file_options.append(f"{file_info['name']} (Read-only)")
    st.write(f"{i}. {file_info['name']} (Read-only)")

file_choice = st.selectbox("Select a file:", ["Select a file"] + file_options)

if file_choice != "Select a file":
    selected_name = file_choice.split(' (')[0]
    selected_file_info = next(file_info for file_info in vocab_files if file_info["name"] == selected_name)

    vocab_path = selected_file_info['path']
    all_vocab = gs.load_csv(vocab_path)

    if not all_vocab.empty:
        st.write(f"You selected: {file_choice}")
        options = ["Select One", "Test random words from a file", "Test words in order from a file", "Test based on a word class"]
        selected_option = st.selectbox("Choose an option:", options)

        if selected_option == "Test random words from a file":
            tester(all_vocab)

        elif selected_option == "Test based on a word class":
            word_classes = ["noun", "verb", "adjective", "adverb", "pronoun", "preposition", "conjunction",
                            "interjection"]

            # Create a radio button to select a word class
            word_class = st.radio("Select a word class:", word_classes)
            filtered_vocab = all_vocab[all_vocab['word_class'] == word_class].reset_index(drop=True)
            if filtered_vocab.empty:
                st.warning(f"No words found for the class '{word_class}'. Please try another class.")
            else:
                tester(filtered_vocab)

    else:
        st.warning(f"No data available in the selected file: {file_choice}")
else:
    st.info("Please select a file from the dropdown.")