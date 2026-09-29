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

if "observation_mangler" not in st.session_state:
    st.session_state.observation_mangler = None

if "undersoegelse_klar" not in st.session_state:
    st.session_state.undersoegelse_klar = None

if "afgraensning" not in st.session_state:
    st.session_state.afgraensning = None

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


def vurder_naeste_skridt():
    historik = "\n\n".join(
        f"Spørgsmål: {punkt['spoergsmaal']}\nSvar: {punkt['svar']}"
        for punkt in st.session_state.samtale
    )

    prompt = f"""
Du er Undersøgeren i leanAKey.

Efter hvert kundesvar skal du vælge præcis én af tre handlinger:

SPØRG: hvis kunden sandsynligvis selv kan svare på ét kort næste spørgsmål,
som reducerer usikkerheden.

OBSERVÉR: hvis den vigtigste manglende oplysning ikke bør gættes frem,
men kræver at kunden observerer, tæller eller måler noget i det virkelige arbejde.

KLAR: hvis samtalen indeholder nok konkrete oplysninger til, at Afgrænseren
kan foretage en reel vurdering. Du behøver IKKE forstå alle detaljer først.
Stop hellere og aflever sagen end at fortsætte med spørgsmål, der kun gør
allerede kendte forhold mere præcise. KLAR er ikke en diagnose, løsning eller
salgsbeslutning.

Regler:
- diagnosticér ikke problemet
- foreslå ikke en løsning, et værktøj eller et produkt
- antag ikke en årsag
- stil højst ét spørgsmål
- gentag ikke noget kunden allerede har besvaret
- pres ikke kunden til et præcist tal, hvis kunden tydeligt ikke ved det
- spørg ikke videre blot for at få hyppighed, minutter eller ekstra detaljer,
  hvis der allerede er et konkret tilbagevendende forhold, som Afgrænseren kan vurdere
- Undersøgerens opgave er at indsamle tilstrækkeligt grundlag, ikke at færdiganalysere sagen
- brug kundens egne oplysninger
- hvis du vælger OBSERVÉR, beskriv kun kort hvad der mangler at blive observeret;
  giv ikke en metode, skabelon eller løsning

Hold internt styr på:
FAKTA = oplysninger kunden faktisk har givet
HYPOTESE = mulige forklaringer, som endnu ikke er dokumenteret
UKENDT = vigtig information vi endnu ikke har

Svar KUN i ét af disse formater:
SPØRG: <ét kort naturligt spørgsmål på dansk>
OBSERVÉR: <én kort sætning om hvad der mangler at blive observeret>
KLAR: <én kort neutral sætning om hvilket konkret grundlag der nu er afdækket>

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
    tekst = response.output_text.strip()

    if tekst.upper().startswith("OBSERVÉR:") or tekst.upper().startswith("OBSERVER:"):
        return "observer", tekst.split(":", 1)[1].strip()

    if tekst.upper().startswith("KLAR:"):
        return "klar", tekst.split(":", 1)[1].strip()

    if tekst.upper().startswith("SPØRG:") or tekst.upper().startswith("SPORG:"):
        return "spoerg", tekst.split(":", 1)[1].strip()

    # Sikker fallback: behandl et uventet svar som ét næste spørgsmål.
    return "spoerg", tekst


def lav_afgraensning():
    historik = "\n\n".join(
        f"Spørgsmål: {punkt['spoergsmaal']}\nSvar: {punkt['svar']}"
        for punkt in st.session_state.samtale
    )

    prompt = f"""
Du er Afgrænseren i leanAKey.

Undersøgeren har afleveret sagen. Den kan være afleveret som KLAR eller fordi
der mangler en observation i det virkelige arbejde. Din opgave er IKKE at stille
flere spørgsmål og IKKE at foreslå en løsning, et værktøj, et produkt eller et køb.

Du skal alene strukturere grundlaget og vurdere, om der kan afgrænses ét lille,
konkret problem på baggrund af kundens egne oplysninger.

Vigtige regler:
- Brug kun oplysninger fra samtalen.
- Gør ikke en kundes usikre skøn mere præcise, end kunden selv har gjort.
- Skeln tydeligt mellem FAKTA, HYPOTESE og UKENDT.
- En hypotese må aldrig præsenteres som et faktum.
- Hvis flere problemer hænger sammen, eller grundlaget er for uklart, må du
  ikke presse sagen ned i ét kunstigt problem.
- Du må ikke diagnosticere en årsag.
- Du må ikke foreslå LEAN-værktøjer, AI, skemaer, målinger eller andre løsninger.
- Du må ikke træffe en salgsbeslutning.
- Kundens valgte startboks er kun indgangen til samtalen, ikke konklusionen.

Vælg præcis én status:
AFGRÆNSET = der kan beskrives ét lille konkret problem uden at antage årsagen.
IKKE_AFGRÆNSET = der er endnu ikke grundlag for ét lille konkret problem.
FLERE_FORBUNDNE = samtalen peger på flere sammenhængende problemer, som ikke
bør presses sammen til ét mikroproblem.

Svar KUN i dette format:
STATUS: <AFGRÆNSET, IKKE_AFGRÆNSET eller FLERE_FORBUNDNE>
PROBLEM: <kort neutral problembeskrivelse eller "Ikke afgrænset">
FAKTA: <kort opsummering af det kunden faktisk har oplyst>
HYPOTESE: <mulig forklaring som ikke er dokumenteret, eller "Ingen nødvendig hypotese">
UKENDT: <vigtig information der stadig mangler, eller "Intet afgørende for afgrænsningen">

Kunden valgte:
{st.session_state.valgt_problem}

Virksomheden arbejder med:
{st.session_state.virksomhed}

Undersøgerens KLAR-grundlag:
{st.session_state.undersoegelse_klar}

Undersøgerens manglende observation:
{st.session_state.observation_mangler}

Samtalen:
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
            st.session_state.observation_mangler = None
            st.session_state.undersoegelse_klar = None
            st.session_state.afgraensning = None
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

    for nummer, punkt in enumerate(st.session_state.samtale, start=1):
        with st.expander(f"Tidligere svar {nummer}", expanded=False):
            st.write(f"**Spørgsmål:** {punkt['spoergsmaal']}")
            st.write(f"**Dit svar:** {punkt['svar']}")

    if st.session_state.observation_mangler:
        st.info(
            "Her giver det mere mening at undersøge noget i det virkelige arbejde "
            "end at gætte videre med flere spørgsmål."
        )
        st.write(f"**Det vi mangler at vide:** {st.session_state.observation_mangler}")

        if st.session_state.afgraensning is None:
            if st.button("Send til Afgrænseren", use_container_width=True):
                try:
                    st.session_state.afgraensning = lav_afgraensning()
                    st.rerun()
                except Exception:
                    st.error(
                        "Der opstod en fejl ved forbindelsen til AI-tjenesten. "
                        "Prøv igen om lidt."
                    )
                    st.stop()
        else:
            st.divider()
            st.subheader("Afgrænserens vurdering")
            st.text(st.session_state.afgraensning)

    elif st.session_state.undersoegelse_klar:
        st.success("Undersøgeren vurderer, at der nu er nok konkret information til næste fase.")
        st.write(f"**Afdækket grundlag:** {st.session_state.undersoegelse_klar}")

        if st.session_state.afgraensning is None:
            if st.button("Send til Afgrænseren", use_container_width=True):
                try:
                    st.session_state.afgraensning = lav_afgraensning()
                    st.rerun()
                except Exception:
                    st.error(
                        "Der opstod en fejl ved forbindelsen til AI-tjenesten. "
                        "Prøv igen om lidt."
                    )
                    st.stop()
        else:
            st.divider()
            st.subheader("Afgrænserens vurdering")
            st.text(st.session_state.afgraensning)

    elif len(st.session_state.samtale) >= 10:
        st.info(
            "Sikkerhedsgrænsen på 10 spørgsmål er nået. "
            "Sagen kan nu sendes videre til Afgrænseren uden at Undersøgeren konkluderer."
        )

        if st.session_state.afgraensning is None:
            if st.button("Send til Afgrænseren", use_container_width=True):
                try:
                    st.session_state.afgraensning = lav_afgraensning()
                    st.rerun()
                except Exception:
                    st.error(
                        "Der opstod en fejl ved forbindelsen til AI-tjenesten. "
                        "Prøv igen om lidt."
                    )
                    st.stop()
        else:
            st.divider()
            st.subheader("Afgrænserens vurdering")
            st.text(st.session_state.afgraensning)

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

                if len(st.session_state.samtale) < 10:
                    try:
                        handling, tekst = vurder_naeste_skridt()
                        if handling == "observer":
                            st.session_state.observation_mangler = tekst
                            st.session_state.aktuelt_spoergsmaal = None
                        elif handling == "klar":
                            st.session_state.undersoegelse_klar = tekst
                            st.session_state.aktuelt_spoergsmaal = None
                        else:
                            st.session_state.aktuelt_spoergsmaal = tekst
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
        st.session_state.observation_mangler = None
        st.session_state.undersoegelse_klar = None
        st.session_state.afgraensning = None
        st.rerun()
