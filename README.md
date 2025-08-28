# 🇩🇪 German Vocabulary Game

A **Streamlit-based learning app** to practice German vocabulary through quizzes, tests, flashcards, and progress tracking.  
Designed to help learners memorize German nouns, verbs, and more — while keeping a personal vocabulary diary and earning achievements.  

---

## ✨ Features

- 📘 **Vocabulary Diary**  
  Store and manage your German words in a central CSV (`diary.csv`).  
  Add new words, edit existing ones, and back up automatically.  

- 📖 **Learning Mode**  
  Displays your vocabulary in a **flashcard-style table**.  
  Lets you browse and review words before taking tests.  

- 🎮 **Test & Quiz Mode**  
  Choose random words or focus on specific word classes (noun, verb, etc.)  
  Get instant feedback and scoring.  

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
