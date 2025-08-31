import unicodedata
import random
import pandas as pd
import shutil
import os
import ast
import re

# ----------------- Constants -----------------
VOCAB_FOLDER = "vocab_data"       # Folder to store all vocabulary-related CSV files
DIARY_FILE = "diary.csv"          # Main diary CSV file where user's words are stored
DIARY_BACKUP = "diary_backup.csv" # Backup of the diary
VOCAB_COLUMNS = ['English', 'German', 'Word Class', 'Verb Tenses'] # Columns used in CSV files

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
        user_input = check_num_input(input(f"\nHow many words would you like to take now? Enter a number between 1 and {maximum}: "))
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

def load_csv(file_path):
    """
    Loads a CSV file into a pandas DataFrame.
    Ensures all columns are present and verb tenses are parsed correctly.
    Creates the CSV file if it does not exist.
    """
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=VOCAB_COLUMNS)
        df.to_csv(file_path, index=False, encoding='utf-8')
        return df

    df = pd.read_csv(file_path, encoding='utf-8')
    for col in VOCAB_COLUMNS:
        if col not in df.columns:
            df[col] = None

    # Parse 'Verb Tenses' column safely
    def parse_tenses(x):
        if isinstance(x, str) and x.startswith('['):
            try:
                tenses = ast.literal_eval(x)
                if isinstance(tenses, list):
                    tenses += [None]*(2 - len(tenses))  # Ensure list has length 2
                    return tenses
            except:
                return [None, None]
        return [None, None] if x is None else x

    df['Verb Tenses'] = df['Verb Tenses'].apply(parse_tenses)
    return df

def save_csv(df, file_path):
    """
    Saves a pandas DataFrame to a CSV file.
    """
    df.to_csv(file_path, index=False, encoding='utf-8')

# ----------------- Words Class -----------------
class Words:
    """
    Handles all operations related to user's diary words:
    loading, adding, and saving vocabulary.
    """
    def __init__(self, diary_path=os.path.join(VOCAB_FOLDER, "diary.csv")):
        self.diary_path = diary_path
        self.vocab = self.load_diary()

    def load_diary(self):
        """
        Loads the diary CSV file into a DataFrame.
        Creates it if it does not exist.
        """
        if os.path.exists(self.diary_path):
            return pd.read_csv(self.diary_path, encoding='utf-8')
        else:
            diary = pd.DataFrame(columns=VOCAB_COLUMNS)
            diary.to_csv(self.diary_path, index=False, encoding='utf-8')
            return diary

    def add_words(self):
        """
        Allows the user to add new words to the diary.
        Handles Noun, Verb, Adjective and verb tense updates.
        """
        main_add_list = []
        while True:
            # Ask user for word class
            class_choice = None
            while class_choice not in [1, 2, 3, 4, 5, 6, 7, 8]:
                class_choice = check_num_input(input("\nSelect word class to add:\n1. Noun\n2. Verb\n3. Adjective\n4. Adverb\n5. Pronoun\n6. Preposition\n7. Conjunction\n8. Interjection\nYour choice: "))
            word_class = {1: "Noun", 2: "Verb", 3: "Adjective", 4: "Adverb", 5: "Pronoun", 6: "Preposition",7: "Conjunction", 8: "Interjection"}[class_choice]
            x = 'c'
            while x == 'c':
                # Ask English word
                english_word = check_char_input(input(f"\nEnter the English {word_class}: "))
                if english_word is None:
                    continue

                # Check if word exists
                existing_index = None
                mask_existing = self.vocab['English'].apply(lambda x: normalize_string(x) == normalize_string(english_word))
                if mask_existing.any():
                    existing_index = self.vocab.index[mask_existing][0]

                # Handle verb tense updates for existing verbs
                if word_class == "Verb" and existing_index is not None:
                    existing_tenses = self.vocab.at[existing_index, 'Verb Tenses']
                    if existing_tenses is None or len(existing_tenses) < 2 or any(t is None for t in existing_tenses):
                        print(f"The verb '{english_word}' exists but has incomplete tenses.")
                        verb_tense_choice = check_char_input(input("Do you want to add missing past and perfect tenses? (Y/N): "))
                        if verb_tense_choice and verb_tense_choice.upper() == "Y":
                            past_tense = check_char_input(input(f"Enter the Past tense of '{english_word}': "))
                            perf_tense = check_char_input(input(f"Enter the Perfect tense of '{english_word}': "))
                            self.vocab.at[existing_index, 'Verb Tenses'] = [past_tense, perf_tense]
                            save_csv(self.vocab, self.diary_path)
                            print(f"Verb tenses updated for '{english_word}'.")
                        continue  # Skip adding as new word

                # Ask German translation
                german_word = check_char_input(input(f"Enter the German {word_class}: "))
                temp_list = [english_word, german_word, word_class, None]

                # Ask verb tenses if new verb
                if word_class == "Verb" and existing_index is None:
                    verb_tense_choice = check_char_input(input(f"Do you wish to add past and perfect tenses? (Y/N): ")).strip().upper()
                    if verb_tense_choice == 'Y':
                        past_tense = check_char_input(input(f"Enter the Past tense of '{german_word}': "))
                        perf_tense = check_char_input(input(f"Enter the Perfect tense of '{german_word}': "))
                        temp_list[3] = [past_tense, perf_tense]

                main_add_list.append(temp_list)

                # Ask user to continue, switch class, or stop
                while True:
                    choice = input("\nC - Continue with same class, N - New word class, S - Stop adding words: ").lower().strip()
                    if choice == 'c':
                        x = 'c'
                        break
                    elif choice == 'n':
                        self.save_vocabulary(main_add_list)
                        print("\nWords saved. Switching to new word class...")
                        break
                    elif choice == 's':
                        self.save_vocabulary(main_add_list)
                        print("\nWords saved. Ending adding words.")
                        return
                    else:
                        print("\nInvalid input. Enter C, N, or S.")

    def add_from_test(self, correct_results):
        """
        Adds correctly answered words from a test into the diary.
        Handles adding missing verb tenses for existing verbs.
        """
        words_added = 0
        diary = self.vocab.copy()
        for entry in correct_results:
            english_word = entry['English']
            german_word = entry['German']
            form = entry['Form']
            word_class = entry.get('Word Class', 'Noun')

            mask_existing = diary['English'].apply(lambda x: normalize_string(x) == normalize_string(english_word))

            # Update existing word's verb tenses
            if mask_existing.any():
                existing_index = diary.index[mask_existing][0]
                existing_tenses = diary.at[existing_index, 'Verb Tenses']
                if existing_tenses is None or not isinstance(existing_tenses, list):
                    existing_tenses = [None, None]

                if form == "Past" and existing_tenses[0] is None:
                    existing_tenses[0] = german_word
                    diary.at[existing_index, 'Verb Tenses'] = existing_tenses
                    words_added += 1
                elif form == "Perfect" and existing_tenses[1] is None:
                    existing_tenses[1] = german_word
                    diary.at[existing_index, 'Verb Tenses'] = existing_tenses
                    words_added += 1
                continue

            # Add new word to diary
            if form == "Base":
                temp_list = [english_word, german_word, word_class, None]
                diary = pd.concat([diary, pd.DataFrame([temp_list], columns=diary.columns)], ignore_index=True)
                words_added += 1

        if words_added > 0:
            save_csv(diary, self.diary_path)
            self.vocab = diary
            print(f"\n{words_added} words/verb tenses added or updated in your Diary.")
        else:
            print("\nNo new words or tenses were added.")

    def save_vocabulary(self, main_add_list):
        """
        Saves newly added words to the diary.
        Creates backup before saving.
        """
        backup_diary_once()
        diary = load_csv(self.diary_path)
        new_vocab = pd.DataFrame(main_add_list, columns=diary.columns)
        final_vocab = pd.concat([diary, new_vocab], ignore_index=True)
        save_csv(final_vocab, self.diary_path)
        self.vocab = final_vocab

# ----------------- Modification Class -----------------
class Modification:
    """
    Handles modifications in the diary: delete, update, undo.
    """
    def __init__(self):
        self.diary_path = os.path.join(VOCAB_FOLDER, DIARY_FILE)
        self.backup_path = os.path.join(VOCAB_FOLDER, DIARY_BACKUP)

    def create_backup_once(self):
        backup_diary_once()

    def undo_last_change(self):
        """
        Restores diary from last backup.
        """
        if os.path.exists(self.backup_path):
            shutil.copy(self.backup_path, self.diary_path)
            print("Your Diary has been restored from the last backup.")
        else:
            print("No backup found to restore.")

    def delete_word(self, english_word):
        """
        Deletes a word from diary.
        """
        self.create_backup_once()
        diary = load_csv(self.diary_path)
        english_word = normalize_string(english_word)
        if english_word in diary['English'].values:
            diary = diary[diary['English'] != english_word]
            save_csv(diary, self.diary_path)
            print(f"The word '{english_word}' has been deleted from your Diary.")
        else:
            print(f"The word '{english_word}' was not found in your Diary.")

    def update_word(self, english_word, new_german=None, new_class=None, new_tenses=None):
        """
        Updates a word in the diary: translation, class, or verb tenses.
        """
        self.create_backup_once()
        diary = load_csv(self.diary_path)
        mask_existing = diary['English'].apply(lambda x: normalize_string(x) == normalize_string(english_word))
        if not mask_existing.any():
            print(f"The word '{english_word}' was not found in your Diary.")
            return
        index_existing = diary.index[mask_existing][0]
        if new_german:
            diary.at[index_existing, 'German'] = normalize_string(new_german)
        if new_class:
            diary.at[index_existing, 'Word Class'] = new_class
        if new_tenses is not None:
            # Ensure verb tenses is a list of length 2
            if isinstance(new_tenses, list):
                new_tenses += [None]*(2-len(new_tenses))
                diary.at[index_existing, 'Verb Tenses'] = new_tenses
        save_csv(diary, self.diary_path)
        print(f"The word '{english_word}' has been updated in your Diary.")

# ----------------- Test Class -----------------
class Test:
    """
    Handles testing vocabulary from available CSV files.
    """
    def test_choice(self):
        """
        Allows user to choose which vocabulary file to test and test mode.
        """
        vocab_files = load_vocab_files()
        vocab_files = [f for f in vocab_files if f['name'] not in ['diary_backup.csv', 'score_history.csv', 'achievements.csv']]

        print("\nAvailable vocabulary files to test:")
        for i, file_info in enumerate(vocab_files, start=1):
            access = "Editable (Diary)" if file_info["editable"] else "Read-only"
            print(f"{i}. {file_info['name']} ({access})")

        # User selects file
        file_choice = None
        while file_choice is None:
            user_input = check_num_input(input("Select a file by number: "))
            if user_input is not None and 1 <= user_input <= len(vocab_files):
                file_choice = user_input
        vocab_path = vocab_files[file_choice - 1]['path']
        vocab_data = load_csv(vocab_path)

        # Select test mode
        print("\nSelect test mode:")
        print("1. Random words")
        print("2. Test by word class")
        print("3. Verb and tenses")
        print("4. Test in order")
        test_mode = None
        while test_mode not in [1, 2, 3, 4]:
            test_mode = check_num_input(input("Your choice: "))

        if test_mode == 1:
            return self.test_random(vocab_data)
        elif test_mode == 2:
            return self.test_word_class(vocab_data)
        elif test_mode == 3:
            return self.test_verb_tense(vocab_data)
        elif test_mode == 4:
            return self.test_in_order(vocab_data)
        return None

    import random

    def test_random(self, vocab):
        """
        Tests a random selection of words from the vocabulary.
        Each verb form becomes a separate question, shuffled with other words.
        """
        all_words = [
            [index, row['English'], row['Word Class'], row['German'], row['Verb Tenses']]
            for index, row in vocab.iterrows()
        ]
        words_available = len(all_words)
        num_questions = count(words_available)  # Number of questions user wants

        # Build a flat list of (English, Word Class, Form Name, Correct Answer) questions
        all_questions = []
        for word_data in all_words:
            _, english_word, word_class, german_word, verb_tenses = word_data

            if word_class.lower() == "verb" and isinstance(verb_tenses, list):
                # Add each verb form as a separate question
                all_questions.append((english_word, word_class, "Base", german_word))
                if verb_tenses[0]:
                    all_questions.append((english_word, word_class, "Past", verb_tenses[0]))
                if verb_tenses[1]:
                    all_questions.append((english_word, word_class, "Perfect", verb_tenses[1]))
            else:
                # Single question for non-verbs
                all_questions.append((english_word, word_class, "Base", german_word))

        # Shuffle all individual questions
        random.shuffle(all_questions)

        # Pick only the number of questions the user requested (or fewer if not enough)
        selected_questions = all_questions[:num_questions]

        total_score = 0
        total_questions = 0
        revision_list = []
        correct_answers = []

        for english_word, word_class, form_name, correct_german in selected_questions:
            user_input = check_char_input(input(f"\n{form_name} form of '{english_word}': "))
            total_questions += 1
            if user_input and normalize_string(user_input).casefold() == normalize_string(correct_german).casefold():
                print("✔ Correct!")
                correct_answers.append({
                    'English': english_word,
                    'Form': form_name,
                    'German': correct_german,
                    'Word Class': word_class
                })
                total_score += 1
            else:
                print(f"✘ Wrong. Correct answer: {correct_german}")
                revision_list.append([english_word, word_class, form_name, correct_german])

        if total_questions > 0:
            print(f"\nYour total score: {(total_score / total_questions) * 100:.2f}%")

        if revision_list:
            revision_df = pd.DataFrame(revision_list, columns=["English", "Word Class", "Form", "Correct German"])
            print("\nWords to revise:\n", revision_df)

        return correct_answers, total_questions

    def test_in_order(self, vocab):
        """
        Tests all words in the vocab file in order (no shuffling).
        Also handles verbs with tenses.
        """
        print("\nMaximum number of words available in the chosen vocabulary file is:", vocab.shape[0])
        print("\nWords will be tested in order from the starting index to the ending index you choose.")
        start = check_num_input(input("Select a starting index: "))
        end = check_num_input(input("Select an ending index: "))

        # slice the vocab DataFrame
        selected_range = vocab.iloc[start - 1:end]  # user-friendly: 1-based indexing

        print("\n📝 In-order test started!\n")

        score = 0
        total = 0

        for _, row in selected_range.iterrows():
            english_word = row['English']
            word_class = row['Word Class']
            german_word = row['German']
            verb_tenses = row['Verb Tenses']

            # === Non-verbs ===
            if word_class != "Verb":
                user_answer = input(f"➡️  Translate '{english_word}' ({word_class}): ").strip()
                if user_answer.lower() == str(german_word).lower():
                    print("✅ Correct!\n")
                    score += 1
                else:
                    print(f"❌ Incorrect. Correct answer: {german_word}\n")
                total += 1

            # === Verbs ===
            else:
                print(f"\n➡️  Verb: {english_word}")
                # Base form
                user_base = input("   Base form: ").strip()
                if user_base.lower() == str(german_word).lower():
                    print("   ✅ Correct base form")
                    score += 1
                else:
                    print(f"   ❌ Incorrect. Correct base form: {german_word}")
                total += 1

                # Verb tenses (Past, Perfect)
                if isinstance(verb_tenses, list):
                    if len(verb_tenses) > 0 and verb_tenses[0]:
                        user_past = input("   Past tense: ").strip()
                        if user_past.lower() == str(verb_tenses[0]).lower():
                            print("   ✅ Correct past tense")
                            score += 1
                        else:
                            print(f"   ❌ Incorrect. Correct past tense: {verb_tenses[0]}")
                        total += 1
                    if len(verb_tenses) > 1 and verb_tenses[1]:
                        user_perf = input("   Perfect tense: ").strip()
                        if user_perf.lower() == str(verb_tenses[1]).lower():
                            print("   ✅ Correct perfect tense")
                            score += 1
                        else:
                            print(f"   ❌ Incorrect. Correct perfect tense: {verb_tenses[1]}")
                        total += 1

        print(f"\n🏆 Test finished! Your score: {score}/{total} ({(score/total*100):.1f}%)")


    def test_word_class(self, vocab):
        """
        Tests words filtered by a specific word class.
        """
        word_class = check_char_input(input("\nEnter the word class to test (Noun/Verb/Adjective): ")).capitalize()
        filtered_vocab = vocab[vocab['Word Class'] == word_class].reset_index(drop=True)
        return self.test_random(filtered_vocab)

    def test_verb_tense(self, vocab):
        """
        Tests only verbs and their tenses.
        """
        filtered_vocab = vocab[vocab['Word Class'] == "Verb"].reset_index(drop=True)
        return self.test_random(filtered_vocab)

# ----------------- Learn -----------------
class Learn:
    def learn_choice(self):
        """
        Allows user to choose which vocabulary file to learn from.
        """
        vocab_files = load_vocab_files()
        vocab_files = [f for f in vocab_files if f['name'] not in ['diary_backup.csv', 'score_history.csv', 'achievements.csv']]

        print("\nAvailable vocabulary files to learn from:")
        for i, file_info in enumerate(vocab_files, start=1):
            access = "Editable (Diary)" if file_info["editable"] else "Read-only"
            print(f"{i}. {file_info['name']} ({access})")

        # User selects file
        file_choice = None
        while file_choice is None:
            user_input = check_num_input(input("Select a file by number: "))
            if user_input is not None and 1 <= user_input <= len(vocab_files):
                file_choice = user_input
        vocab_path = vocab_files[file_choice - 1]['path']
        vocab_data = load_csv(vocab_path)

        # Select learning mode
        print("\nSelect learning mode:")
        print("1. Random words")
        print("2. Learn by word class")
        print("3. Verb and tenses")
        print("4. Learn in order")
        learn_mode = None
        while learn_mode not in [1, 2, 3, 4]:
            learn_mode = check_num_input(input("Your choice: "))

        if learn_mode == 1:
            return self.learn_random(vocab_data)
        elif learn_mode == 2:
            return self.learn_word_class(vocab_data)
        elif learn_mode == 3:
            return self.learn_verb_tense(vocab_data)
        elif learn_mode == 4:
            return self.learn_in_order(vocab_data)

    def learn_in_order(self, vocab):
        """
        Lets the user learn words in order by displaying their translation.
        """
        print("\nMaximum number of words available in the chosen vocabulary file is: ", vocab.shape[0])
        print("\nWords will be shown in order from the starting index to the ending index you choose. Example: words 51 to 70 in the vocab file")
        start = check_num_input(input("Select a starting index: "))
        end = check_num_input(input("Select a ending index: "))
        selected_range = vocab.iloc[start-1:end]
        print("\n📖 Learning session started!\n")
        for _, row in selected_range.iterrows():
            english_word = row['English']
            word_class = row['Word Class']
            german_word = row['German']
            print(f"➡️  {english_word} ({word_class}) translates to {german_word}")
            input("Press Enter to continue...")

        print("\n✅ End of learning session.")


    def learn_random(self, vocab):
        """
        Lets the user review random words by displaying their translation.
        """
        num_of_words = count(vocab.shape[0])
        all_words = [
            [index, row['English'], row['Word Class'], row['German']]
            for index, row in vocab.iterrows()
        ]
        selected_words = random.sample(all_words, num_of_words)

        print("\n📖 Learning session started!\n")
        for _, english_word, word_class, german_word in selected_words:
            print(f"➡️  {english_word} ({word_class}) translates to {german_word}")
            input("Press Enter to continue...")

        print("\n✅ End of learning session.")

    def learn_word_class(self, vocab):
        """
        Lets the user review words of a specific word class.
        """
        word_class = check_char_input(input("\nEnter the word class to learn (Noun/Verb/Adjective/...): ")).capitalize()
        filtered_vocab = vocab[vocab['Word Class'] == word_class].reset_index(drop=True)

        if filtered_vocab.empty:
            print(f"\n⚠️ No words found for the class '{word_class}'.")
            return None

        return self.learn_random(filtered_vocab)

    def learn_verb_tense(self, vocab):
        """
        Lets the user review verbs and their different tenses.
        """
        filtered_vocab = vocab[vocab['Word Class'] == "Verb"].reset_index(drop=True)

        if filtered_vocab.empty:
            print("\n⚠️ No verbs found in the selected file.")
            return

        num_of_words = count(filtered_vocab.shape[0])
        all_verbs = [
            [row['English'], row['German'], row['Verb Tenses']]
            for _, row in filtered_vocab.iterrows()
        ]
        selected_verbs = random.sample(all_verbs, num_of_words)

        print("\n📖 Learning verbs and their tenses!\n")
        for english_word, german_base, tenses in selected_verbs:
            print(f"➡️  {english_word} (Verb):")
            print(f"    - Base: {german_base}")
            if isinstance(tenses, list):
                if tenses[0]:
                    print(f"    - Past: {tenses[0]}")
                if tenses[1]:
                    print(f"    - Perfect: {tenses[1]}")
            input("Press Enter to continue...")

        print("✅ End of verb learning session.")

# ----------------- Gameplay -----------------
class ScoreManager:
    """
    Handles storing scores, checking achievements, and unlocking new achievements.
    """
    def __init__(self):
        self.score_file = os.path.join(VOCAB_FOLDER, "score_history.csv")
        self.achievements_file = os.path.join(VOCAB_FOLDER, "achievements.csv")
        if not os.path.exists(VOCAB_FOLDER):
            os.makedirs(VOCAB_FOLDER)
        self.load_scores()
        self.load_achievements()

    def load_scores(self):
        """
        Loads score history from CSV or creates new CSV if none exists.
        """
        if os.path.exists(self.score_file):
            self.score_history = pd.read_csv(self.score_file)
        else:
            self.score_history = pd.DataFrame(columns=["Date", "ScorePercent", "TotalQuestions"])
            self.score_history.to_csv(self.score_file, index=False)

    def load_achievements(self):
        """
        Loads achievements from CSV or creates new CSV if none exists.
        """
        if os.path.exists(self.achievements_file):
            self.achievements = pd.read_csv(self.achievements_file)
        else:
            self.achievements = pd.DataFrame(columns=["Achievement", "DateEarned"])
            self.achievements.to_csv(self.achievements_file, index=False)

    def add_score(self, score_percent, total_questions):
        """
        Adds new score entry and checks for achievements.
        """
        from datetime import datetime
        new_entry = {"Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "ScorePercent": score_percent, "TotalQuestions": total_questions}
        self.score_history = pd.concat([self.score_history, pd.DataFrame([new_entry])], ignore_index=True)
        self.score_history.to_csv(self.score_file, index=False)
        self.check_achievements(score_percent)

    def check_achievements(self, score_percent):
        """
        Checks if any achievement conditions are met after a new score.
        """
        perfect_score_streak = 5
        perfect_games = self.score_history.tail(perfect_score_streak)
        if len(perfect_games) == perfect_score_streak and (perfect_games['ScorePercent'] == 100).all():
            self.unlock_achievement(f"Perfect 5 games in a row!")

        if score_percent == 100 and "First 100% score" not in self.achievements['Achievement'].values:
            self.unlock_achievement("First 100% score!")

    def unlock_achievement(self, achievement_name):
        """
        Unlocks a new achievement and saves it to CSV.
        """
        from datetime import datetime
        if achievement_name not in self.achievements['Achievement'].values:
            new_ach = {"Achievement": achievement_name, "DateEarned": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            self.achievements = pd.concat([self.achievements, pd.DataFrame([new_ach])], ignore_index=True)
            self.achievements.to_csv(self.achievements_file, index=False)
            print(f"\n🎉 Achievement unlocked: {achievement_name} 🎉")

    def show_achievements(self):
        """
        Displays user's achievements.
        """
        if self.achievements.empty:
            print("No achievements earned yet.")
        else:
            print("\nYour Achievements:")
            print(self.achievements)

class Gameplay:
    """
    Main gameplay loop. Handles user interaction for adding, testing, modifying words, and viewing achievements.
    """
    def welcome(self):
        print("\nHello! Welcome to your German Vocabulary Game!")
        print("You can learn, test, and maintain your vocabulary in a fun way.")
        self.score_manager = ScoreManager()
        self.start()

    def start(self):
        """
        Main loop to interact with the user.
        """
        diary_words = Words()
        tester = Test()

        while True:
            action = check_char_input(input(
                "\nWhat would you like to do?\nL - Learn words from vocab files\nA - Add words to Diary\nT - Test your vocabulary\nM - Modify Diary\nS - Show Achievements\nE - Exit\nYour choice: ")).lower().strip()

            if action is None:
                continue

            if action == 'a':
                diary_words.add_words()

            elif action == 't':
                tester.test_choice()
                '''
                correct_results, total_questions = tester.test_choice()
                if correct_results:
                    add_to_diary = input(
                        "\nDo you want to add the correct answers to your Diary? (Y/N): ").strip().upper()
                    if add_to_diary == 'Y':
                        diary_words.add_from_test(correct_results)

                score_percent = (len(correct_results) / total_questions * 100) if total_questions > 0 else 0
                self.score_manager.add_score(score_percent, total_questions)
                '''

            elif action == 'l':
                learner = Learn()
                learner.learn_choice()

            elif action == 'm':
                mod = Modification()
                while True:
                    modify_choice = check_char_input(input(
                        "\nD - Delete a word\nU - Update a word\nR - Undo last change\nE - Exit Modify\nYour choice: ")).lower().strip()
                    if modify_choice is None:
                        continue
                    if modify_choice == 'd':
                        word_to_delete = check_char_input(input("Enter the English word to delete: "))
                        if word_to_delete:
                            mod.delete_word(word_to_delete)
                    elif modify_choice == 'u':
                        word_to_update = check_char_input(input("Enter the English word to update: "))
                        if word_to_update:
                            new_german = input("Enter new German translation (leave blank to skip): ").strip() or None
                            new_class = input("Enter new Word Class (leave blank to skip): ").strip() or None
                            new_tenses = input("Enter new Verb Tenses (comma-separated, leave blank to skip): ").strip()
                            new_tenses = new_tenses.split(",") if new_tenses else None
                            mod.update_word(word_to_update, new_german, new_class, new_tenses)
                    elif modify_choice == 'r':
                        mod.undo_last_change()
                    elif modify_choice == 'e':
                        break
                    else:
                        print("Invalid input. Please try again.")

            elif action == 's':
                self.score_manager.show_achievements()

            elif action == 'e':
                print("\nThank you for using the German Vocabulary Game! Goodbye!")
                exit()

            else:
                print("Invalid input. Please enter A, T, M, S, or E.")

# ----------------- Main -----------------
def main():
    """
    Entry point of the program.
    """
    game = Gameplay()
    game.welcome()

if __name__ == "__main__":
    main()
