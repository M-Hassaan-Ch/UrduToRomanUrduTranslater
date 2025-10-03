
import streamlit as st
from utils.romanizer import romanize

def main():
    st.title("Urdu to Roman Urdu Translator")
    st.write("Enter Urdu text below and get its Roman Urdu transliteration.")
    urdu_input = st.text_area("Urdu Input", height=150)
    if st.button("Convert to Roman Urdu"):
        if urdu_input.strip():
            roman_output = romanize(urdu_input)
            st.markdown("**Roman Urdu Output:**")
            st.code(roman_output, language="text")
        else:
            st.warning("Please enter some Urdu text.")

if __name__ == "__main__":
    main()