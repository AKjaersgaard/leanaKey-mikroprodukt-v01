import streamlit as st

st.set_page_config(
    page_title="leanAKey – testprototype",
    page_icon="🔑",
    layout="centered"
)

st.title("leanAKey")

st.subheader("Noget du kan genkende?")

st.write(
    "Vælg den situation, der passer bedst på det, du oplever lige nu."
)

if st.button("Jeg mangler tid…", use_container_width=True):
    st.write("Du valgte: Jeg mangler tid…")

if st.button("Jeg mangler noget for at komme videre…", use_container_width=True):
    st.write("Du valgte: Jeg mangler noget for at komme videre…")

if st.button("Jeg gør ting om nogle gange…", use_container_width=True):
    st.write("Du valgte: Jeg gør ting om nogle gange…")

if st.button("Det burde kunne gøres lettere…", use_container_width=True):
    st.write("Du valgte: Det burde kunne gøres lettere…")

if st.button("Jeg har noget, jeg ikke får brugt/solgt…", use_container_width=True):
    st.write("Du valgte: Jeg har noget, jeg ikke får brugt/solgt…")

if st.button("Har jeg skjult potentiale?", use_container_width=True):
    st.write("Du valgte: Har jeg skjult potentiale?")
