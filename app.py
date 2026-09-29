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

if "udenfor_lean" not in st.session_state:
    st.session_state.udenfor_lean = None

if "afgraensning" not in st.session_state:
    st.session_state.afgraensning = None

if "afgraenser_feedback" not in st.session_state:
    st.session_state.afgraenser_feedback = None

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

Efter hvert kundesvar skal du først lave en intern TRIAGE og derefter vælge præcis én af fire handlinger:

SPØRG: hvis kunden sandsynligvis selv kan svare på ét kort næste spørgsmål,
som reducerer usikkerheden.

OBSERVÉR: hvis den vigtigste manglende oplysning ikke bør gættes frem,
men kræver at kunden observerer, tæller eller måler noget i det virkelige arbejde.

UDENFOR: hvis kundens dokumenterede hovedproblem primært ligger uden for forbedring af
arbejdsgange/processer, fx markedsføring/efterspørgsel, prisfastsættelse/økonomisk rådgivning,
jura, skat eller anden specialistfaglig rådgivning. Brug ikke UDENFOR blot fordi problemet har
en økonomisk konsekvens eller handler om salg; spørgsmålet er hvor problemets mekanisme ligger.

KLAR: kun hvis samtalen indeholder et minimum af dokumenteret grundlag, så
Afgrænseren kan foretage en reel vurdering. Før KLAR skal kundens egne svar
tilsammen dokumentere:
1) SITUATION: hvor/hvornår problemet opleves,
2) KONKRET FORHOLD: hvad der faktisk sker eller udføres,
3) BETYDNING ELLER GENTAGELSE: enten en konkret konsekvens for arbejdet eller
   at forholdet gentager sig.
Alle tre led skal komme fra kundens svar. De må ikke udledes eller opfindes.
Du behøver ikke præcise minutter eller tal, hvis de tre led allerede er belyst.
KLAR er ikke en diagnose, løsning eller salgsbeslutning.

TRIAGE – VURDÉR DETTE FØR DU VÆLGER NÆSTE SPØRGSMÅL:
A MINI-LEAN: Problemet ligger i en konkret arbejdsgang/proces og ser lille nok ud til at kunne afgrænses.
B STØRRE LEAN: Problemet ligger i arbejdsgange/processer, men involverer flere sammenhængende processer,
  afhængigheder eller kompleksitet. Indsaml kun det nødvendige grundlag til senere menneskelig vurdering.
C UDEN FOR LEAN: Problemets primære mekanisme ligger ikke i arbejdsgangen, men fx i manglende
  efterspørgsel/markedsføring, prisfastsættelse, finansiering, skat, jura eller specialistfaglig rådgivning.
D FOR TIDLIGT: Der mangler én afgørende oplysning for at skelne A/B/C. Stil kun det spørgsmål.

Vigtigt: Klassificér mekanismen, ikke branchen og ikke kundens valgte boks.
En B&B kan have et LEAN-problem med rengøringsflow, men manglende vinterefterspørgsel er ikke
i sig selv et LEAN-problem. En café kan have økonomisk tab fra kassation og stadig have et LEAN-problem,
hvis mekanismen ligger i planlægning/processen. Brug disse som principillustrationer, ikke case-regler.

LEAN-FAGLIGT KOMPAS – KUN TIL DIN INTERNE TÆNKNING:
Du er en mini-LEAN-konsulent, ikke blot en interviewer. Brug LEAN-tænkning til at forstå
kundens faktiske arbejdsgang og til at vælge det mest værdifulde næste spørgsmål.
Kunden skal ikke kende LEAN og skal ikke mødes med LEAN-, Six Sigma- eller konsulentsprog.

Se især efter dokumenterede signaler som:
- gentagne manuelle trin, beregninger eller overførsel af information
- ventetid, afbrydelser, mangler og arbejde der ikke kan fortsætte
- fejl, rettelser og omarbejde
- unødige trin, håndtering, bevægelse eller dobbeltarbejde
- lager, rester, kassation eller noget der ikke bliver brugt/solgt
- variation i hvordan samme arbejde udføres
- uklare eller manglende standarder/forberedelse
- flaskehalse, køer eller overleveringer hvor information/arbejde kan vente eller gå tabt

Tænk proces før løsning: Hvad sker der faktisk, hvor sker det, hvor ofte, og hvilken
konsekvens har det? Brug kundens data til at prioritere få væsentlige signaler frem for at
samle alle tænkelige detaljer. En enkel beregning må bruges til at forstå størrelsesorden.

SIGNAL = en relevant kombination af FAKTA og eventuelt AFLEDT information, der gør et
forhold værd at undersøge nærmere. Et SIGNAL er ikke en dokumenteret årsag og ikke en løsning.
Fx kan gentagen manuel beregning + manuel indtastning + mærkbart tidsforbrug + dokumenterede
fejl være et stærkt signal uden at du konkluderer, hvilket program eller værktøj kunden bør bruge.

Brug signaler aktivt til at vælge næste spørgsmål. Når et stærkt signal allerede er belyst,
må du ikke fortsætte med flere næsten ens spørgsmål om samme dimension. Find den vigtigste
resterende usikkerhed eller vælg KLAR/OBSERVÉR.

LEAN-VURDERING AF ARBEJDET:
- Skeln mellem at noget tager tid, og at tiden faktisk rummer et forbedringspotentiale.
- Undersøg både selve aktiviteten og det omkringliggende flow: forberedelse, rækkefølge, timing,
  ventetid, overleveringer, dobbeltregistrering, manuel beregning/overførsel og afbrydelser.
- Nødvendigt arbejde må ikke automatisk behandles som spild. En aktivitet kan være nødvendig pga.
  kundeværdi, kvalitet, sikkerhed, lovkrav eller dokumentation og stadig kunne udføres enklere.
- Hvis en nødvendig aktivitet opleves som besværlig, undersøg om måden den udføres, placeres,
  forberedes, dokumenteres eller kobles til resten af processen på skaber det konkrete besvær.
- Forsøg aldrig at fjerne eller flytte en sikkerheds-, kvalitets- eller lovpligtig aktivitet uden
  dokumenteret grundlag for at det er forsvarligt. Ved tvivl bevar kravet som en begrænsning.
- Et dokumenteret problem behøver ikke have både tids-, kvalitets- og økonomisk konsekvens.
  Én væsentlig dokumenteret konsekvens kan være nok til afgrænsning.
- Når arbejdsgangen indeholder manuel beregning, manuel overførsel, gentagen indtastning eller
  andre fejlmuligheder, og en fejl realistisk kan have betydning, har spørgsmålet om faktisk
  forekommende fejl/konsekvens høj informationsværdi. Spørg neutralt; antag aldrig at fejl findes.
- Brug AFLEDT aktivt til størrelsesorden, fx antal gange × tid pr. gang. Bevar intervaller og
  antagelser, undgå falsk præcision, og kald aldrig beregningen et kundesvar.
- Prioritér næste spørgsmål efter BESLUTNINGSVÆRDI: Kan svaret ændre problemafgrænsningen,
  vise en væsentlig konsekvens/risiko eller afgøre om dette stadig er en mini-opgave?
  Procesdetaljer, der kun gør kortlægningen mere komplet, har lavere prioritet.
- SEMANTISK DUBLETKONTROL: Formulér først internt hvilket informationsbehov et nyt spørgsmål
  skal dække. Sammenlign dette behov med hele samtalen. Hvis behovet allerede er helt eller
  væsentligt besvaret, må du ikke spørge igen med en ny formulering.
- Led efter den mindste relevante forbedringsmulighed, ikke en fuld kortlægning af virksomheden.

MINI-KONSULENTENS GRÆNSE:
Din opgave er at forstå og afgrænse en lille problemstilling. Hvis oplysningerne peger på flere
sammenhængende processer, mange afhængigheder eller en problemstilling der ikke kan afgrænses
forsvarligt med få fakta, skal du ikke forsøge at løse kompleksiteten med flere og flere spørgsmål.
Indsaml kun det nødvendige grundlag, så en senere rolle kan vurdere, om sagen skal videre til
en menneskelig LEAN-konsulent.

Regler:
- diagnosticér ikke problemet
- foreslå ikke en løsning, et værktøj eller et produkt
- antag ikke en årsag
- stil højst ét spørgsmål
- gentag ikke noget kunden allerede har besvaret
- pres ikke kunden til et præcist tal, hvis kunden tydeligt ikke ved det
- spørg ikke videre blot for at få hyppighed, minutter eller ekstra detaljer,
  når SITUATION + KONKRET FORHOLD + BETYDNING ELLER GENTAGELSE allerede er dokumenteret
- hvis et af de tre minimumsled mangler, skal du stille ét spørgsmål, der forsøger
  at afdække netop det manglende led, medmindre det kræver observation
- Undersøgerens opgave er at indsamle tilstrækkeligt grundlag, ikke at færdiganalysere sagen
- brug kundens egne oplysninger
- STOP VED MÆTNING: Når problemet er konkret dokumenteret, omfang eller gentagelse er belyst,
  konsekvensen er belyst, og den sidste afgørende uklarhed for selve problemafgrænsningen er afklaret,
  skal du vælge KLAR. Fortsæt ikke blot fordi et ekstra spørgsmål kunne være interessant.
- Efter mætning må du ikke lede efter mønstre på tværs af kundetyper, bilagstyper, produkter,
  tidspunkter eller andre mulige forklaringer. Det hører til en senere analysefase.
- Spørg kun videre, hvis svaret realistisk kan ændre, om der findes ét afgrænset problem,
  eller hvis en afgørende faktuel uklarhed stadig forhindrer afgrænsningen.
- Et spørgsmål er ikke nødvendigt alene fordi svaret kunne gøre sagen mere detaljeret.
- FORSTÅ SVARET FØRST: Hvis kundens svar er relevant men sprogligt uklart, skal du bevare
  usikkerheden eller stille ét kort bekræftende spørgsmål. Ignorér ikke svaret og skift ikke emne.
- ENHEDER: Et svar er brugbart, selv om kunden svarer i en anden tids- eller måleenhed end den,
  du spurgte efter. Fx er "2-5 opgaver om ugen" brugbart ved et spørgsmål om antal pr. måned.
  Bevar kundens oprindelige tal som FAKTA. En enkel omregning må bruges som AFLEDT, men det
  beregnede tal må aldrig fremstilles som noget kunden selv har oplyst.
- INFORMATIONSVAERDI: Vælg det næste spørgsmål, der bedst skelner mellem forskellige typer af
  problem eller afklarer den vigtigste resterende usikkerhed. Prioritér dette over ekstra detaljer.
- Kontrollér hele samtalen før næste spørgsmål. Hvis informationen allerede findes, også med
  andre ord eller i en anden enhed, må du ikke spørge efter den igen.
- Hvis kunden svarer på noget andet end det stillede spørgsmål, bevar den nye oplysning som FAKTA.
  Det oprindelige spørgsmål er fortsat ubesvaret, hvis det stadig er vigtigt.
- Sikkerhedsgrænsen på 10 spørgsmål er et nødstop, aldrig et mål.
- hvis du vælger OBSERVÉR, beskriv kun kort hvad der mangler at blive observeret;
  giv ikke en metode, skabelon eller løsning

Hold internt styr på:
FAKTA = oplysninger kunden faktisk har givet
AFLEDT = enkel beregning eller omregning direkte fra kundens fakta; må ikke kaldes et kundesvar
SIGNAL = mønster i FAKTA/AFLEDT som er værd at undersøge; er ikke årsag eller løsning
HYPOTESE = mulige forklaringer, som endnu ikke er dokumenteret
UKENDT = vigtig information vi endnu ikke har

Svar KUN i ét af disse formater:
SPØRG: <ét kort naturligt spørgsmål på dansk>
UDENFOR: <én kort neutral sætning om hvilket fagområde hovedproblemet ser ud til at høre til>
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

    if tekst.upper().startswith("UDENFOR:"):
        return "udenfor", tekst.split(":", 1)[1].strip()

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
- Brug kun oplysninger, kunden faktisk har givet i samtalen.
- Du må aldrig tilføje hyppighed, gentagelse, konsekvens, tidsforbrug eller andre
  forhold, som kunden ikke selv har oplyst.
- Gør ikke en kundes usikre skøn mere præcise, end kunden selv har gjort.
- Skeln tydeligt mellem FAKTA, HYPOTESE og UKENDT.
- Før status AFGRÆNSET må bruges, skal kundens egne svar dokumentere alle tre:
  SITUATION + KONKRET FORHOLD + BETYDNING ELLER GENTAGELSE.
- Hvis et af de tre led mangler, skal status være IKKE_AFGRÆNSET, og det manglende
  led skal stå under UKENDT. Du må ikke udfylde det ved antagelse.
- En hypotese må aldrig præsenteres som et faktum.
- Hvis flere problemer hænger sammen, eller grundlaget er for uklart, må du
  ikke presse sagen ned i ét kunstigt problem.
- Du må ikke diagnosticere en årsag.
- Du må ikke foreslå LEAN-værktøjer, AI, skemaer, målinger eller andre løsninger.
- Du må ikke træffe en salgsbeslutning.
- Kundens valgte startboks er kun indgangen til samtalen, ikke konklusionen.

Vælg præcis én status:
AFGRÆNSET = der kan beskrives ét lille konkret problem uden at antage årsagen,
og SITUATION + KONKRET FORHOLD + BETYDNING ELLER GENTAGELSE er dokumenteret.
IKKE_AFGRÆNSET = der er endnu ikke dokumenteret grundlag for ét lille konkret problem,
eller mindst ét af de tre minimumsled mangler.
FLERE_FORBUNDNE = samtalen peger på flere sammenhængende problemer, som ikke
bør presses sammen til ét mikroproblem.

Svar KUN i dette format:
STATUS: <AFGRÆNSET, IKKE_AFGRÆNSET eller FLERE_FORBUNDNE>
PROBLEM: <kort neutral problembeskrivelse eller "Ikke afgrænset">
FAKTA: <kort opsummering af det kunden faktisk har oplyst>
HYPOTESE: <mulig forklaring som ikke er dokumenteret, eller "Ingen nødvendig hypotese">
UKENDT: <vigtig information der stadig mangler, eller "Intet afgørende for afgrænsningen">\nNÆSTE_TRIN: <"OBSERVATION MANGLER" hvis sagen kræver observation før produktvurdering, ellers "KLAR TIL NÆSTE VURDERING">

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


def vurder_afgraenser_feedback():
    prompt = f"""
Du er returgaten mellem Afgrænseren og Undersøgeren i leanAKey.
Afgrænserens vurdering er:
{st.session_state.afgraensning}

Vurdér om der mangler vigtig konkret viden, før sagen senere kan vurderes til et eventuelt mikroprodukt.
Et afgrænset problem er ikke automatisk klar til et produkt.

Regler:
- Vælg kun noget kunden sandsynligvis selv kan svare på uden at gætte.
- Spørg ikke kunden om en ukendt årsag, som om kunden kender den.
- Omfang, mønster, variation eller hvad kunden allerede ved/registrerer kan være relevant.
- Stil kun ét spørgsmål ad gangen.
- Foreslå ikke løsning, skema, værktøj eller køb.
- Hvis det vigtigste manglende kræver observation eller måling i virkeligheden, vælg OBSERVÉR.
- Hvis intet afgørende mangler før næste fase, vælg VIDERE.

Svar KUN:
SPØRG: <ét kort naturligt spørgsmål>
eller
OBSERVÉR: <kort hvad der først må observeres>
eller
VIDERE: <kort begrundelse>
"""
    response = client.responses.create(model="gpt-5.6-luna", input=prompt)
    tekst = response.output_text.strip()
    if tekst.upper().startswith("SPØRG:") or tekst.upper().startswith("SPORG:"):
        return "spoerg", tekst.split(":", 1)[1].strip()
    if tekst.upper().startswith("OBSERVÉR:") or tekst.upper().startswith("OBSERVER:"):
        return "observer", tekst.split(":", 1)[1].strip()
    return "videre", tekst.split(":", 1)[1].strip() if ":" in tekst else tekst



# TESTLAB – faste grænsecases til beslutningsmodellen.
TESTCASES = [
 {"navn":"B&B – ingen vinterefterspørgsel","boks":"Jeg har noget, jeg ikke får brugt/solgt…","virksomhed":"bed & breakfast","forventet":"udenfor","samtale":[("Hvad bliver ikke solgt?","Tre lejligheder står ofte tomme om vinteren."),("Er de bookbare?","Ja, hele året."),("Hvad gør I for at finde vinterkunder?","Ingenting. Sommerfirmaet arbejder ikke her om vinteren.")]},
 {"navn":"B&B – rengøringsflow","boks":"Jeg mangler tid…","virksomhed":"bed & breakfast","forventet":"klar","samtale":[("Hvornår?","Når lejlighederne gøres klar."),("Hvad sker der?","Jeg går frem og tilbage til hovedhuset efter linned og rengøringsmidler."),("Gentager det sig?","Ja, næsten hver rengøring og det tager ekstra tid.")]},
 {"navn":"VVS – manuel fakturering","boks":"Det burde kunne gøres lettere…","virksomhed":"VVS","forventet":"klar","samtale":[("Hvad er besværligt?","Fakturaer. Jeg lægger tal sammen på lommeregner og skriver dem ind i Word."),("Hvor ofte?","Omkring 25 om måneden."),("Betydning?","10-30 minutter pr. faktura, og sidste måned fandt to kunder regnefejl.")]},
 {"navn":"Juridisk vurdering","boks":"Det burde kunne gøres lettere…","virksomhed":"lille virksomhed","forventet":"udenfor","samtale":[("Hvad er svært?","At afgøre om en konkurrenceklausul er lovlig."),("Arbejdsgangen eller vurderingen?","Selve den juridiske vurdering.")]},
 {"navn":"Café – kassation","boks":"Jeg har noget, jeg ikke får brugt/solgt…","virksomhed":"café","forventet":"klar","samtale":[("Hvad?","Kager tilbage ved lukketid."),("Hvad sker der?","Nogle tages med hjem, resten smides ud."),("Gentaget?","Ja, næsten hver dag.")]},
 {"navn":"Nødvendig kvalitetskontrol","boks":"Jeg mangler tid…","virksomhed":"fødevareproduktion","forventet":"spoerg","samtale":[("Hvornår?","Ved kvalitetskontrollen. Den tager lang tid."),("Kan den undværes?","Nej, den er et krav og vigtig for fødevaresikkerheden.")]},
 {"navn":"Maler – materialemangel","boks":"Jeg mangler noget for at komme videre…","virksomhed":"malerfirma","forventet":"klar","samtale":[("Hvad mangler?","Maling, grunder eller tapet."),("Hvornår opdages det?","Når bilen pakkes før kunden."),("Betydning?","Vi kan ikke starte. Det sker 2-3 gange om måneden.")]},
 {"navn":"Webshop – marketing","boks":"Jeg har noget, jeg ikke får brugt/solgt…","virksomhed":"webshop","forventet":"udenfor","samtale":[("Hvad sælges ikke?","En ny produktserie."),("Procesproblem?","Nej, der kommer næsten ingen besøgende til produktsiderne."),("Udfordringen?","Vi ved ikke hvordan vi skal markedsføre produkterne.")]},
 {"navn":"Flere processer","boks":"Jeg mangler tid…","virksomhed":"produktion","forventet":"klar","samtale":[("Hvornår?","Leverancer forsinkes."),("Hvad sker der?","Indkøb mangler materialer, plan ændres, maskinen stopper og kvalitet får bunker."),("Én arbejdsgang?","Nej, indkøb, planlægning, produktion og kvalitet rammes hver uge.")]},
 {"navn":"Kræver observation","boks":"Jeg gør ting om nogle gange…","virksomhed":"kontor","forventet":"observer","samtale":[("Hvad gør du om?","Jeg leder efter rigtig dokumentversion og retter bagefter."),("Hvor ofte?","Det ved jeg ikke. Vi har aldrig holdt øje og jeg kan ikke vurdere det.")]},
 {"navn":"Prisfastsættelse","boks":"Har jeg skjult potentiale?","virksomhed":"fotograf","forventet":"udenfor","samtale":[("Hvor er potentialet?","Jeg tror mine priser er for lave."),("Hvad vil du have hjælp til?","At finde markedsprisen og hvad jeg bør tage.")]},
 {"navn":"Forkert boks – procesproblem","boks":"Jeg har noget, jeg ikke får brugt/solgt…","virksomhed":"cykelværksted","forventet":"klar","samtale":[("Hvad får du ikke brugt?","Min tid. Cykler venter på reservedele."),("Hvad sker der?","Jeg starter og opdager bagefter at en del mangler."),("Betydning?","Cyklen optager plads og arbejdet stopper flere gange om ugen.")]}
]

def koer_testbatteri():
    gemt = (st.session_state.valgt_problem, st.session_state.virksomhed, list(st.session_state.samtale))
    resultater = []
    try:
        for case in TESTCASES:
            st.session_state.valgt_problem = case["boks"]
            st.session_state.virksomhed = case["virksomhed"]
            st.session_state.samtale = [{"spoergsmaal": q, "svar": a} for q, a in case["samtale"]]
            handling, tekst = vurder_naeste_skridt()
            resultater.append({"case":case["navn"],"forventet":case["forventet"],"faktisk":handling,"bestaaet":handling == case["forventet"],"output":tekst})
    finally:
        st.session_state.valgt_problem, st.session_state.virksomhed, st.session_state.samtale = gemt
    return resultater

# SKÆRM 1 – vælg situation
if st.session_state.valgt_problem is None:

    st.divider()
    with st.expander("🧪 Testlab – beslutningsmotor", expanded=False):
        st.caption("Midlertidigt udviklingsværktøj: 12 faste grænsecases mod samme Undersøger-logik.")
        if st.button("Kør automatisk testbatteri", key="koer_testbatteri"):
            with st.spinner("Tester beslutningsmotoren…"):
                try:
                    resultater = koer_testbatteri()
                    bestaaet = sum(1 for r in resultater if r["bestaaet"])
                    st.write(f"**Resultat: {bestaaet}/{len(resultater)} bestået**")
                    for r in resultater:
                        ikon = "✅" if r["bestaaet"] else "❌"
                        st.write(f"{ikon} **{r['case']}** — forventet: {r['forventet']}, faktisk: {r['faktisk']}")
                        if not r["bestaaet"]:
                            st.caption("Motorens output: " + r["output"])
                except Exception:
                    st.error("Testbatteriet kunne ikke gennemføres. Prøv igen om lidt.")

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
            st.session_state.afgraenser_feedback = None
            st.session_state.udenfor_lean = None
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

    if st.session_state.udenfor_lean:
        st.info("Det her ser ikke ud til primært at være en opgave om at forbedre en arbejdsgang eller proces.")
        st.write(f"**Vurdering:** {st.session_state.udenfor_lean}")
        st.write("leanAKey stopper derfor her i stedet for at presse problemet ind i en LEAN-løsning.")

    elif st.session_state.observation_mangler:
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

            if st.session_state.afgraenser_feedback is None:
                if st.button("Kontrollér om der mangler noget", use_container_width=True):
                    try:
                        handling, tekst = vurder_afgraenser_feedback()
                        if handling == "spoerg":
                            st.session_state.aktuelt_spoergsmaal = tekst
                            st.session_state.undersoegelse_klar = None
                            st.session_state.afgraensning = None
                            st.rerun()
                        elif handling == "observer":
                            st.session_state.observation_mangler = tekst
                            st.session_state.undersoegelse_klar = None
                            st.session_state.afgraensning = None
                            st.rerun()
                        else:
                            st.session_state.afgraenser_feedback = tekst
                            st.rerun()
                    except Exception:
                        st.error("Der opstod en fejl ved forbindelsen til AI-tjenesten. Prøv igen om lidt.")
                        st.stop()
            else:
                st.info(f"Klar til næste fase: {st.session_state.afgraenser_feedback}")

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
                        if handling == "udenfor":
                            st.session_state.udenfor_lean = tekst
                            st.session_state.aktuelt_spoergsmaal = None
                        elif handling == "observer":
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

    # TESTHJÆLP – samler hele forløbet, så det let kan kopieres til gennemgang.
    # Fjernes eller skjules i den færdige kundeversion.
    if st.session_state.samtale:
        st.divider()
        with st.expander("Testlog – kopiér hele forløbet", expanded=False):
            loglinjer = [
                f"VALGT BOKS: {st.session_state.valgt_problem}",
                f"VIRKSOMHED: {st.session_state.virksomhed}",
                ""
            ]
            for nummer, punkt in enumerate(st.session_state.samtale, start=1):
                loglinjer.extend([
                    f"SPØRGSMÅL {nummer}: {punkt['spoergsmaal']}",
                    f"SVAR {nummer}: {punkt['svar']}",
                    ""
                ])
            if st.session_state.udenfor_lean:
                loglinjer.extend([
                    f"UNDERSØGER: UDENFOR: {st.session_state.udenfor_lean}",
                    ""
                ])
            if st.session_state.observation_mangler:
                loglinjer.extend([
                    f"UNDERSØGER: OBSERVÉR: {st.session_state.observation_mangler}",
                    ""
                ])
            if st.session_state.undersoegelse_klar:
                loglinjer.extend([
                    f"UNDERSØGER: KLAR: {st.session_state.undersoegelse_klar}",
                    ""
                ])
            if st.session_state.afgraensning:
                loglinjer.extend([
                    "AFGRÆNSERENS VURDERING:",
                    st.session_state.afgraensning
                ])
            st.code("\n".join(loglinjer), language=None)

    if st.button("← Tilbage", key="tilbage_undersoegelse"):
        st.session_state.virksomhed = None
        st.session_state.samtale = []
        st.session_state.aktuelt_spoergsmaal = None
        st.session_state.observation_mangler = None
        st.session_state.undersoegelse_klar = None
        st.session_state.afgraensning = None
        st.rerun()
