import streamlit as st
import main_page as gs
import pandas as pd

st.title("Score & Achievements")

# Load scores
score_file = gs.load_csv(gs.VOCAB_FOLDER + "/score_history.csv", expected_columns=["Date", "ScorePercent", "TotalQuestions"])

if score_file.empty:
    st.info("No scores recorded yet.")
else:
    st.subheader("Score History")
    st.dataframe(score_file)

    # Stats
    best_score = score_file["ScorePercent"].max()
    avg_score = round(score_file["ScorePercent"].mean(), 1)
    total_games = len(score_file)

    st.subheader("Statistics")
    st.write(f"🏆 Best Score: {best_score}%")
    st.write(f"📊 Average Score: {avg_score}%")
    st.write(f"🎮 Total Games Played: {total_games}")

    # Example achievement: 5 full marks in a row
    scores = score_file["ScorePercent"].tolist()
    streak = 0
    max_streak = 0
    for s in scores:
        if s == 100:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    st.write(f"🔥 Max Full Marks Streak: {max_streak}")
