import streamlit as st
import random
import main_page as gs
import pandas as pd
gs.set_background("images\\learn_page_bg.jpg")
gs.sidebar()

st.markdown("<h1 style='text-align: center; font-weight: bold;'>Learn New Vocabulary</h1>",unsafe_allow_html=True)

# Load vocabulary files and filter out unwanted ones
vocab_files = gs.load_vocab_files()

print("vocab_files",vocab_files)

vocab_files = [f for f in vocab_files if f['name'] not in ['diary_backup.csv', 'score_history.csv', 'achievements.csv']]

# Display the available vocabulary files to the user
st.write("\nAvailable vocabulary files to learn from:")
file_options = []

for i, file_info in enumerate(vocab_files, start=1):
    access = "Read-only"
    file_options.append(f"{file_info['name']} ({access})")
    st.write(f"{i}. {file_info['name']} ({access})")

# Add a placeholder option at the top of the selectbox
file_choice = st.selectbox("Select a file:", ["Select a file"] + file_options)

# Check if the user has made a valid selection and load the vocab data
if file_choice != "Select a file":
    # Extract the file name and access level from the selected choice
    selected_name = file_choice.split(' (')[0]  # Extract just the file name
    selected_file_info = next(file_info for file_info in vocab_files if file_info["name"] == selected_name)

    # Load the vocab data from the selected file
    vocab_path = selected_file_info['path']
    vocab_data = gs.load_csv(vocab_path)

    # Check if the vocab data is empty
    if not vocab_data.empty:
        st.write(f"You selected: {file_choice}")
        options = ["Learn random words from a file", "Learn in order from a file", "Learn based on a word class"]
        selected_option = st.selectbox("Choose an option:", options)

        if selected_option == "Learn random words from a file":
            word_num = st.slider("How many words would you like to learn?", min_value=0, max_value=vocab_data.shape[0], step=1)
            selected_words = random.sample(range(vocab_data.shape[0]), word_num)
            show = pd.DataFrame()
            for i in selected_words:
                show = pd.concat([show, vocab_data.iloc[[i]]], axis=0)
            if show.shape[0] > 0:
                st.dataframe(show)

        elif selected_option == "Learn in order from a file":
            start = st.number_input(f"Enter the starting index from which you would like to learn from the selected file", min_value=0, max_value=vocab_data.shape[0]-1)
            end = st.number_input(f"Enter the ending index up to which you would like to learn from the selected file", min_value=start, max_value=vocab_data.shape[0]-1)
            ordered_data = vocab_data.iloc[start:end+1]
            st.dataframe(ordered_data)

        elif selected_option == "Learn based on a word class":
            # Define a list of possible word classes (these should match what's in your vocab_data)
            word_classes = vocab_data['word_class'].dropna().str.strip().str.lower().unique().tolist()

            # Create a radio button to select a word class
            word_class = st.radio("Select a word class:", word_classes)

            # Filter the vocab_data based on the selected word class
            filtered_vocab = vocab_data[vocab_data['word_class'] == word_class].reset_index(drop=True)

            if filtered_vocab.empty:
                st.warning(f"No words found for the class '{word_class}'. Please try another class.")
            else:
                word_num = st.slider(f"How many words would you like to learn from the class '{word_class}'?",min_value=0, max_value=filtered_vocab.shape[0], step=1)
                selected_words = random.sample(range(filtered_vocab.shape[0]), word_num)
                show = pd.DataFrame()

                for i in selected_words:
                    show = pd.concat([show, filtered_vocab.iloc[[i]]], axis=0)

                if show.shape[0] > 0:
                    st.dataframe(show)

    else:
        st.write(f"No data available in the selected file: {file_choice}")
else:
    st.write("Please select a file from the dropdown.")
