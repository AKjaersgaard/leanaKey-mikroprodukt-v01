import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(
    page_title="leanAKey – testprototype",
    page_icon="🔑",
    layout="centered"
)

# Appens hukommelse
if "valgt_problem" not in st.session_state:
    st.session_state.valgt_problem = None

if "virksomhed" not in st.session_state:
    st.session_state.virksomhed = None

if "svar_1" not in st.session_state:
    st.session_state.svar_1 = None

if "ai_spoergsmaal" not in st.session_state:
    st.session_state.ai_spoergsmaal = None

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
elif st.session_state.virksomhed is None:

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
            st.session_state.virksomhed = virksomhed.strip()
            st.rerun()
        else:
            st.warning(
                "Skriv kort, hvad virksomheden arbejder med, før du fortsætter."
            )

    if st.button("← Tilbage", key="tilbage_virksomhed"):
        st.session_state.valgt_problem = None
        st.rerun()


# SKÆRM 3 – første spørgsmål
else:

    st.subheader("Lad os se lidt nærmere på det")

    problem = st.session_state.valgt_problem
    virksomhed = st.session_state.virksomhed

    # Boksen bestemmer det første spørgsmål – ikke konklusionen
    if problem == "Jeg mangler tid…":
        spoergsmaal = (
            f"Når du tænker på arbejdet i din {virksomhed}, "
            "hvornår oplever du især, at tiden ikke slår til?"
        )

    elif problem == "Jeg mangler noget for at komme videre…":
        spoergsmaal = (
            f"Når arbejdet går i stå i din {virksomhed}, "
            "hvad oplever du typisk, at du mangler for at kunne fortsætte?"
        )

    elif problem == "Jeg gør ting om nogle gange…":
        spoergsmaal = (
            f"Hvilke ting i din {virksomhed} oplever du, "
            "at du nogle gange må gøre om?"
        )

    elif problem == "Det burde kunne gøres lettere…":
        spoergsmaal = (
            f"Hvilken del af arbejdet i din {virksomhed} "
            "føles mere besværlig, end du synes den burde være?"
        )

    elif problem == "Jeg har noget, jeg ikke får brugt/solgt…":
        spoergsmaal = (
            f"Hvad har du i din {virksomhed}, "
            "som du oplever ikke bliver brugt eller solgt som forventet?"
        )

    else:
        spoergsmaal = (
            f"Hvis du ser på din {virksomhed} som helhed, "
            "hvor kunne du bedst tænke dig at undersøge, "
            "om der gemmer sig et uudnyttet potentiale?"
        )

    st.write(spoergsmaal)

    svar = st.text_area(
        "Skriv med dine egne ord:",
        placeholder="Du behøver ikke kende årsagen – beskriv bare, hvad du oplever."
    )

    if st.button("Gem svar og fortsæt", use_container_width=True):
        if svar.strip():
            st.session_state.svar_1 = svar.strip()
    
            prompt = f"""
    Du er Undersøgeren i leanAKey.
    
    Din opgave er kun at stille ét næste spørgsmål, som hjælper med at forstå
    kundens konkrete situation bedre.
    
    Du må ikke:
    - diagnosticere problemet
    - foreslå en løsning
    - foreslå et værktøj eller produkt
    - antage en årsag
    - stille flere spørgsmål på én gang
    
    Brug kundens egne oplysninger og stil ét kort, naturligt spørgsmål på dansk.
    
    Kunden valgte:
    {st.session_state.valgt_problem}
    
    Virksomheden arbejder med:
    {st.session_state.virksomhed}
    
    Kundens første svar:
    {st.session_state.svar_1}
    """
    
            response = client.responses.create(
                model="gpt-5.6-luna",
                input=prompt
            )
    
            st.session_state.ai_spoergsmaal = response.output_text
            st.rerun()

    else:
        st.warning("Skriv lidt om det, du oplever, før du fortsætter.")

        if st.button("← Tilbage"):
            st.session_state.virksomhed = None
            st.session_state.svar_1 = None
            st.rerun()

