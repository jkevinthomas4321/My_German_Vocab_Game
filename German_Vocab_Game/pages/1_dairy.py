import streamlit as st
import main_page as gs
import pandas as pd
gs.set_background("images\diary_page_bg.jpg")
gs.sidebar()
st.markdown("<h1 style='text-align: center; font-weight: bold;'>📝 This is your personal Diary</h1>",unsafe_allow_html=True)

# Load all vocab files
vocab_files = gs.load_vocab_files()
print(vocab_files)

# Initialize paths and dataframes
vocab_diary = None
vocab_backup = None
diary_path = None
backup_path = None

# Find paths for diary and backup
for f in vocab_files:
    if f['name'] == 'diary.csv':
        diary_path = f['path']
        vocab_diary = gs.load_csv(diary_path)
    elif f['name'] == 'diary_backup.csv':
        backup_path = f['path']
        vocab_backup = gs.load_csv(backup_path)

# Show warning if diary is not found
if vocab_diary is None:
    st.warning("⚠️ 'diary.csv' not found.")
else:
    # Show editable diary
    st.subheader("Editable Diary")
    edited_diary = st.data_editor(
        vocab_diary,
        num_rows="dynamic",
        use_container_width=True,
        key="diary_editor"
    )

    # Save button
    if st.button("💾 Save Changes"):
        # Backup current diary before saving new version
        if backup_path:
            gs.save_csv(vocab_diary, backup_path)
            st.info("🔄 Backup saved to 'diary_backup.csv'")
        else:
            st.warning("⚠️ Could not save backup. 'diary_backup.csv' not found.")

        # Save updated diary
        gs.save_csv(edited_diary, diary_path)
        st.success("✅ Diary saved successfully!")

    # Undo button
    if st.button("↩️ Undo Last Change"):
        if vocab_backup is not None:
            gs.save_csv(vocab_backup, diary_path)
            st.success("✅ Reverted to last backup from 'diary_backup.csv'")
        else:
            st.warning("⚠️ No backup found to revert.")
