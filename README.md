# 🇩🇪 German Vocabulary Game

## ✨ What is this?
A **Streamlit-based learning app** to learn and practice German vocabulary through tests and progress tracking.  
Designed to help learners memorize German nouns, verbs, and more — while keeping a personal vocabulary diary and earning achievements.  

## ✨ Background
I am a student. I learned python and pandas, wanted to create something sso I created this to solve my own problem, which is German vocab learning. 
The core idea is to create a virtual vocabulary diary for users.
The current version has all basic ideas I had and it is mostly stable.
This game works based on csv files, which acts as repos containing the language data. I have added a repo which can be used initially. 
You can ask any AI to create a .csv with words you require and can use it to learn vocabulary. Remember to add the vocab file in vocab data folder.
(Beta: You can also ask AI to create a csv of vocab in any language based on the column headings in the diary .csv file and use it to learn the language.)
Any improvements like features or bug reports or fixes are widely welcome.
This is currently local and works in our system. It is currently not equipped to host this in a server and add login features.
---***

## ✨ Features

- 📘 **Vocabulary Diary**  
  Store and manage your German words in a central CSV (`diary.csv`).  
  Add new words, edit existing ones, and back up automatically.  

- 📖 **Learning Mode**  
  Displays your vocabulary in a **flashcard-style table**.  
  Lets you learn words before taking tests.  

- 🎮 **Test Mode**  
  Choose random words or focus on specific word classes (noun, verb, etc.)  
  Get instant feedback and scoring.
  If your answer is correct then you get an option to add it to your diary.

- 🏆 **Achievements & Score History**  
  Your test results are saved in `score_history.csv` with:
  - Date & Time  
  - Score (%)  
  - Number of Questions  
  Track progress, best streaks, and performance trends.  

- 🔄 **Multiple Vocabulary Files**  
  You can load other CSVs besides the diary, with automatic handling of missing/new columns.   

- 🛡️ **Safe by Design**  
  A backup (`diary_backup.csv`) is always created before changes.  

- Use of AI
  I have used ChatGPT to revise the version I have been using personally and asked ChatGPT to make it clean and add comments    to each part so that you can understand the code easily.
---

## 🗂️ Project Structure

📦 German_Vocab_Game
├── main_page.py # Entry point (welcome, vocab loader, helpers)
├── pages/
│ ├── 1_dairy.py # Add / edit words in diary
│ ├── 2_learn_vocab.py # Flashcards / learning mode
│ ├── 3_test_game.py # Quiz/test mode
│ └── 4_achievements.py # Achievements & score history
├── vocab_data/
│ ├── diary.csv # Main vocabulary diary
│ ├── diary_backup.csv # Backup (auto-generated)
│ ├── 1000_german_vocab
│ └── score_history.csv # Stores game results
└── README.md

Requirements:
Install the following packages
streamlit
pandas

Use:
Clone the repo
run the app with the command: streamlit run main_page.py
