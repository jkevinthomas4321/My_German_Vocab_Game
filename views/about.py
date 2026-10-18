import streamlit as st

from ui import components as C

st.title("About Wortschatz")
st.markdown("""
**Wortschatz** (*word treasure*) is a German vocabulary trainer built around one idea: learning is a data problem.
Every answer is logged, the next review is scheduled from that log, and the dashboards are computed from it.

#### How a session works
1. **Plan.** Words that are due for review come first, then new words in order of real-world frequency, so the most
   useful vocabulary is learned first. If many reviews are overdue, fewer new words are added.
2. **Ask.** Five question types, getting harder as a word sticks: pick the translation, pick the German word (nouns
   come with an article and one wrong-article decoy), der/die/das, typing, and verb forms.
3. **Grade.** Case, extra spaces and `ae`/`oe`/`ue`/`ss` for umlauts are forgiven; spelling is not. A dash or an
   empty answer is never correct.
4. **Schedule.** A Leitner box system: a right answer moves the word one box up (longer wait), a wrong answer drops it
   two boxes. Box 5 counts as *mastered*.
5. **Learn from the data.** The Progress page shows learning and forgetting curves, which articles you mix up, your
   hardest words and when you study best.

#### Methods used in the analytics
- **Wilson score intervals** on every accuracy, so small samples look as uncertain as they are.
- **Beta-prior smoothing** of per-word error rates, so a word asked twice does not outrank one asked ten times.
- **Forgetting curve** from consecutive attempts of the same word, conditioned on a previous success.
- **Spearman rank correlation** between word frequency and accuracy.
- **Auto-generated findings** that stay silent when the sample is too small to say anything.

#### The data
- `data/wordlists/german_core.csv`: 515 common German words with article, plural, Präteritum and Perfekt, written by
  hand, validated by `tools/build_wordlist.py`, and sorted by measured frequency. Translations and forms are
  worth a quick check against your own textbook.
- Frequency comes from the [`wordfreq`](https://github.com/rspeer/wordfreq) package (Zipf scale), whose data is
  licensed CC BY-SA 4.0.
- **Everything stays on your computer**: progress is saved in `user_data/` as plain CSV.
- The **demo profile** is produced by a simulated learner (`wortschatz/simulate.py`), not by a real person.
""")
C.note("Built with Python, pandas, NumPy, Altair and Streamlit.")
