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

if "samtale" not in st.session_state:
    st.session_state.samtale = []

if "aktuelt_spoergsmaal" not in st.session_state:
    st.session_state.aktuelt_spoergsmaal = None

st.title("leanAKey")


def foerste_spoergsmaal(problem, virksomhed):
    """Boksen bestemmer første spørgsmål – ikke konklusionen."""
    if problem == "Jeg mangler tid…":
        return (
            f"Når du tænker på arbejdet i din {virksomhed}, "
            "hvornår oplever du især, at tiden ikke slår til?"
        )
    elif problem == "Jeg mangler noget for at komme videre…":
        return (
            f"Når arbejdet går i stå i din {virksomhed}, "
            "hvad oplever du typisk, at du mangler for at kunne fortsætte?"
        )
    elif problem == "Jeg gør ting om nogle gange…":
        return (
            f"Hvilke ting i din {virksomhed} oplever du, "
            "at du nogle gange må gøre om?"
        )
    elif problem == "Det burde kunne gøres lettere…":
        return (
            f"Hvilken del af arbejdet i din {virksomhed} "
            "føles mere besværlig, end du synes den burde være?"
        )
    elif problem == "Jeg har noget, jeg ikke får brugt/solgt…":
        return (
            f"Hvad har du i din {virksomhed}, "
            "som du oplever ikke bliver brugt eller solgt som forventet?"
        )
    else:
        return (
            f"Hvis du ser på din {virksomhed} som helhed, "
            "hvor kunne du bedst tænke dig at undersøge, "
            "om der gemmer sig et uudnyttet potentiale?"
        )


def lav_naeste_spoergsmaal():
    historik = "\n\n".join(
        f"Spørgsmål: {punkt['spoergsmaal']}\nSvar: {punkt['svar']}"
        for punkt in st.session_state.samtale
    )

    prompt = f"""
Du er Undersøgeren i leanAKey.

Din opgave er kun at stille ét næste spørgsmål, som reducerer usikkerheden
og hjælper med at forstå kundens konkrete situation bedre.

Du må ikke:
- diagnosticere problemet
- foreslå en løsning
- foreslå et værktøj eller produkt
- antage en årsag
- stille flere spørgsmål på én gang
- stille et spørgsmål, kunden allerede har besvaret

Brug kundens egne oplysninger. Stil ét kort og naturligt spørgsmål på dansk.
Svar kun med selve spørgsmålet.

Kunden valgte:
{st.session_state.valgt_problem}

Virksomheden arbejder med:
{st.session_state.virksomhed}

Samtalen indtil nu:
{historik}
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=prompt
    )
    return response.output_text.strip()


# SKÆRM 1 – vælg situation
if st.session_state.valgt_problem is None:
    st.subheader("Noget du kan genkende?")
    st.write("Vælg den situation, der passer bedst på det, du oplever lige nu.")

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
            st.session_state.samtale = []
            st.session_state.aktuelt_spoergsmaal = None
            st.rerun()


# SKÆRM 2 – virksomhedens kontekst
elif st.session_state.virksomhed is None:
    st.subheader("Fortæl lidt om din virksomhed")
    st.write(f"Du valgte: **{st.session_state.valgt_problem}**")

    virksomhed = st.text_input(
        "Hvad arbejder din virksomhed med?",
        placeholder="Fx frisørsalon, tømrervirksomhed, café eller mindre produktion"
    )

    if st.button("Fortsæt", use_container_width=True):
        if virksomhed.strip():
            st.session_state.virksomhed = virksomhed.strip()
            st.session_state.aktuelt_spoergsmaal = foerste_spoergsmaal(
                st.session_state.valgt_problem,
                st.session_state.virksomhed
            )
            st.rerun()
        else:
            st.warning("Skriv kort, hvad virksomheden arbejder med, før du fortsætter.")

    if st.button("← Tilbage", key="tilbage_virksomhed"):
        st.session_state.valgt_problem = None
        st.rerun()


# SKÆRM 3 – dynamisk undersøgelse
else:
    st.subheader("Lad os se lidt nærmere på det")

    # Vis tidligere spørgsmål og svar diskret
    for nummer, punkt in enumerate(st.session_state.samtale, start=1):
        with st.expander(f"Tidligere svar {nummer}", expanded=False):
            st.write(f"**Spørgsmål:** {punkt['spoergsmaal']}")
            st.write(f"**Dit svar:** {punkt['svar']}")

    # V0.6: test op til 6 spørgsmål. Ingen diagnose eller salgsbeslutning endnu.
    if len(st.session_state.samtale) >= 6:
        st.info(
            "Testgrænsen på 6 spørgsmål er nået. "
            "V0.6 stopper her uden at konkludere eller foreslå en løsning."
        )
    else:
        st.write(st.session_state.aktuelt_spoergsmaal)

        svar = st.text_area(
            "Skriv med dine egne ord:",
            placeholder="Du behøver ikke kende årsagen – beskriv bare, hvad du oplever.",
            key=f"svar_{len(st.session_state.samtale)}"
        )

        if st.button("Gem svar og fortsæt", use_container_width=True):
            if svar.strip():
                st.session_state.samtale.append(
                    {
                        "spoergsmaal": st.session_state.aktuelt_spoergsmaal,
                        "svar": svar.strip()
                    }
                )

                if len(st.session_state.samtale) < 6:
                    try:
                        st.session_state.aktuelt_spoergsmaal = lav_naeste_spoergsmaal()
                    except Exception:
                        st.error(
                            "Der opstod en fejl ved forbindelsen til AI-tjenesten. "
                            "Prøv igen om lidt."
                        )
                        st.stop()

                st.rerun()
            else:
                st.warning("Skriv lidt om det, du oplever, før du fortsætter.")

    if st.button("← Tilbage", key="tilbage_undersoegelse"):
        st.session_state.virksomhed = None
        st.session_state.samtale = []
        st.session_state.aktuelt_spoergsmaal = None
        st.rerun()
