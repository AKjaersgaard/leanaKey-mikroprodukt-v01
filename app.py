import streamlit as st

st.set_page_config(
    page_title="leanAKey – testprototype",
    page_icon="🔑",
    layout="centered"
)

# Appens hukommelse
if "valgt_problem" not in st.session_state:
    st.session_state.valgt_problem = None

st.title("leanAKey")

# SKÆRM 1 – vælg situation
if st.session_state.valgt_problem is None:

    st.subheader("Noget du kan genkende?")

    st.write(
        "Vælg den situation, der passer bedst på det, du oplever lige nu."
    )

    problemer = [
        "Jeg mangler tid…",
        "Jeg mangler noget for at komme videre…",
        "Jeg gør ting om nogle gange…",
        "Det burde kunne gøres lettere…",
        "Jeg har noget, jeg ikke får brugt/solgt…",
        "Har jeg skjult potentiale?"
    ]

    for problem in problemer:
        if st.button(problem, use_container_width=True):
            st.session_state.valgt_problem = problem
            st.rerun()

# SKÆRM 2 – virksomhedens kontekst
else:

    st.subheader("Fortæl lidt om din virksomhed")

    st.write(
        f"Du valgte: **{st.session_state.valgt_problem}**"
    )

    virksomhed = st.text_input(
        "Hvad arbejder din virksomhed med?",
        placeholder="Fx frisørsalon, tømrervirksomhed, café eller mindre produktion"
    )

    if st.button("Fortsæt", use_container_width=True):
        if virksomhed.strip():
            st.success(
                f"Tak. Jeg har nu registreret, at virksomheden arbejder med: {virksomhed}"
            )
        else:
            st.warning(
                "Skriv kort, hvad virksomheden arbejder med, før du fortsætter."
            )

    if st.button("← Tilbage"):
        st.session_state.valgt_problem = None
        st.rerun()
