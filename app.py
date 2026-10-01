import streamlit as st
from openai import OpenAI
from datetime import datetime, timezone

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

for navn, standard in {
    "flow_fase": "spoergsmaal", "flow_retning": None, "flow_besked": None,
    "flow_fejl": None, "flow_haendelser": [], "flow_kald": 0,
    "flow_log_aktiv": False, "flow_raa_output": None,
}.items():
    if navn not in st.session_state:
        st.session_state[navn] = standard

st.title("leanAKey")


def gem_flow_output(output):
    if st.session_state.get("flow_log_aktiv", False):
        st.session_state.flow_raa_output = output


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
- NØDVENDIGT ARBEJDE ER EN SÆRLIG GRÆNSE: Hvis aktiviteten er nødvendig pga. lovkrav, sikkerhed,
  kvalitet, fødevaresikkerhed eller tilsvarende binding, er "det tager lang tid" alene IKKE et
  dokumenteret forbedringsproblem. Før KLAR skal der være mindst ét kundedokumenteret tegn på
  procespåvirkning omkring aktiviteten, fx ventetid, forsinkelse, afbrydelse, dobbeltarbejde,
  gentagelse/omarbejde eller anden konkret påvirkning. Antag aldrig at en sådan påvirkning findes.
  Hvis den mangler, vælg SPØRG med ét neutralt spørgsmål om hvad tidsforbruget konkret betyder for
  arbejdet før/under/efter aktiviteten. Selve det nødvendige krav må ikke behandles som spild eller
  foreslås fjernet. Denne regel gælder generelt og har forrang for minimumsreglen
  SITUATION + KONKRET FORHOLD + BETYDNING ELLER GENTAGELSE.
- STOP FØR ÅRSAGSKORTLÆGNING: Når et gentaget konkret tab/problem og dets betydning allerede er
  dokumenteret, må du ikke spørge hvordan virksomheden beslutter, planlægger eller styrer det blot
  for at lede efter en mulig årsag. Det hører til senere analyse. Vælg KLAR, medmindre svaret på et
  nyt spørgsmål realistisk kan ændre triage eller selve problemafgrænsningen.
- KOMPLEKSITET ER OGSÅ ET STOP-SIGNAL: Hvis kundens egne svar allerede viser flere samtidige,
  tværgående processer eller funktioner, skal du ikke kortlægge relationerne mellem dem. Der er
  allerede nok grundlag til at sende sagen til Afgrænseren, som skal vurdere FLERE_FORBUNDNE.
- Et næste spørgsmål skal være NØDVENDIGT, ikke blot nyttigt eller interessant. Før du vælger SPØRG,
  kontrollér internt: "Hvis kunden ikke svarer på dette, kan jeg så stadig afgrænse problemet eller
  afgøre at det er komplekst/udenfor?" Hvis ja, vælg ikke SPØRG.

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
    gem_flow_output(response.output_text)
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
    gem_flow_output(response.output_text)
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
    gem_flow_output(response.output_text)
    tekst = response.output_text.strip()
    if tekst.upper().startswith("SPØRG:") or tekst.upper().startswith("SPORG:"):
        return "spoerg", tekst.split(":", 1)[1].strip()
    if tekst.upper().startswith("OBSERVÉR:") or tekst.upper().startswith("OBSERVER:"):
        return "observer", tekst.split(":", 1)[1].strip()
    return "videre", tekst.split(":", 1)[1].strip() if ":" in tekst else tekst



def vurder_produktport(afgraensning):
    prompt = f"""
Du er Produktporten i leanAKey. Du kommer EFTER Afgrænseren.
Din opgave er ikke at bygge eller sælge et produkt. Du skal beskytte kunden mod et forkert køb.

Vælg præcis én retning:
MIKROPRODUKT = ét lille, klart afgrænset procesproblem kan realistisk undersøges med ét enkelt
værktøj, og kunden kender ikke allerede det svar, værktøjet ville vise.
GRATIS = der mangler nødvendig information for at vurdere et relevant enkelt værktøj, eller
kunden kan komme videre med en kort gratis instruktion uden et nyt køb. Der må ikke sælges endnu.
MØDE = dokumenterede flere forbundne problemer, afhængigheder eller kompleksitet gør sagen uegnet til ét
mikroprodukt. Kunden bør tilbydes et gratis, uforpligtende møde med Annette.
STOP = sagen er uden for LEAN/procesforbedring, eller der er ikke et reelt forbedringsproblem.

Hårde regler:
- Et AFGRÆNSET problem er IKKE automatisk et MIKROPRODUKT.
- 49 kr. må kun være ét lille problem + ét enkelt værktøj + kort vejledning.
- Hvis kunden allerede ved, hvad et oplagt registrerings-/måleværktøj vil vise, vælg ikke MIKROPRODUKT.
- Skeln mellem manglende grundlag for at forstå/afgrænse problemet og en ukendt årsag til et
  allerede dokumenteret problem. En ukendt årsag er ikke i sig selv grund til GRATIS.
- Når ét lille, afgrænset problem og dets betydning eller gentagelse er dokumenteret, kan
  MIKROPRODUKT være relevant, hvis ét enkelt undersøgelsesværktøj realistisk kan give ny viden
  om et mønster. Kræv ikke, at årsagen eller stedet i procesforløbet allerede er kortlagt.
- Ny viden skal være nødvendig eller relevant for at forstå det allerede dokumenterede og
  afgrænsede problem. At yderligere information kunne være interessant, er ikke nok.
- Skab ikke et nyt undersøgelsesspørgsmål, mønster eller en ny ukendt alene for at gøre et
  MIKROPRODUKT relevant. Behovet for ny viden skal have grundlag i sagens oplysninger;
  fortsæt ikke undersøgelsen, indtil der findes noget, der kan sælges.
- Hvis kunden allerede har den centrale viden, som det oplagte simple undersøgelsesværktøj
  skulle frembringe, må du ikke retfærdiggøre et salg ved selv at introducere et nyt mønster,
  spørgsmål eller ukendt. Uden selvstændigt dokumenteret grundlag for MØDE eller STOP skal
  retningen være GRATIS. Denne regel gælder også, selv om mere registrering er mulig.
- Vælg GRATIS, hvis nødvendig information mangler for overhovedet at vurdere et relevant enkelt
  værktøj. Opfind ikke et produkt eller gæt på et problem for at omgå manglende grundlag.
- Manglende mikroprodukt-egnethed er ikke i sig selv grund til MØDE. MØDE kræver selvstændigt
  dokumenteret kompleksitet, flere forbundne problemer eller afhængigheder i sagens oplysninger.
- Hvis et oplagt værktøj blot gentager kendt viden, og der ikke er et selvstændigt grundlag for
  MØDE eller STOP, vælg GRATIS. Opfind ikke afhængigheder eller kompleksitet.
- FLERE_FORBUNDNE skal normalt blive MØDE, når sagens oplysninger dokumenterer de forbundne
  problemer; pres ikke kompleksitet ned i et produkt.
- Startboksen "Har jeg skjult potentiale?" må aldrig ende direkte i MIKROPRODUKT. Brug GRATIS,
  MØDE eller STOP. Et eventuelt konkret lille problem må undersøges separat senere.
- Opfind ikke fakta, årsager, økonomisk gevinst eller forbedringer.
- Foreslå endnu ikke hvilket værktøj der skal bruges.

Svar KUN:
RETNING: <MIKROPRODUKT, GRATIS, MØDE eller STOP>
BEGRUNDELSE: <kort, konkret begrundelse baseret på sagen>

Kundens startboks:\n{st.session_state.valgt_problem}\n\nAfgrænserens output:\n{afgraensning}
"""
    response = client.responses.create(model="gpt-5.6-luna", input=prompt)
    gem_flow_output(response.output_text)
    # Bevar rå output til Testlab uden at ændre den eksisterende fortolkning.
    st.session_state.produktport_raa_output = response.output_text
    tekst = response.output_text.strip()
    retning = "stop"
    for linje in tekst.splitlines():
        if linje.upper().startswith("RETNING:"):
            vaerdi = linje.split(":", 1)[1].strip().upper()
            mapping = {"MIKROPRODUKT":"mikroprodukt","GRATIS":"gratis","MØDE":"moede","MODE":"moede","STOP":"stop"}
            retning = mapping.get(vaerdi, "stop")
            break
    return retning, tekst

PRODUTPORT_CASES = [
 {"navn":"Lille konkret materialemangel","forventet":"mikroprodukt","afgraensning":"""STATUS: AFGRÆNSET
PROBLEM: Malerhold opdager gentagne gange først ved pakning, at standardmaterialer mangler, så arbejdet hos kunden ikke kan starte.
FAKTA: Maling, grunder eller tapet mangler 2-3 gange om måneden og opdages ved pakning.
HYPOTESE: Ingen nødvendig hypotese.
UKENDT: Årsagen er ikke dokumenteret.
NÆSTE_TRIN: KLAR TIL NÆSTE VURDERING"""},
 {"navn":"Observation mangler før køb","forventet":"gratis","afgraensning":"""STATUS: IKKE_AFGRÆNSET
PROBLEM: Ikke afgrænset.
FAKTA: Kunden leder efter dokumentversioner og retter nogle gange bagefter.
HYPOTESE: Ingen nødvendig hypotese.
UKENDT: Kunden ved ikke hvor ofte det sker, og det er aldrig observeret.
NÆSTE_TRIN: OBSERVATION MANGLER"""},
 {"navn":"Flere forbundne processer","forventet":"moede","afgraensning":"""STATUS: FLERE_FORBUNDNE
PROBLEM: Materialemangel, planændringer, ventetid i produktionen og ophobning ved kvalitet optræder på tværs af flere funktioner.
FAKTA: Indkøb, planlægning, produktion og kvalitet rammes gentagne gange.
HYPOTESE: Ingen nødvendig hypotese.
UKENDT: Ét enkelt mikroproblem er ikke afgrænset.
NÆSTE_TRIN: KLAR TIL NÆSTE VURDERING"""},
 {"navn":"Allerede kendt svar","forventet":"gratis","afgraensning":"""STATUS: AFGRÆNSET
PROBLEM: Der bruges ekstra tid på at hente linned under næsten hver rengøring.
FAKTA: Kunden har allerede registreret det i to uger og ved, at turene til hovedhuset står for hovedparten af den ekstra tid.
HYPOTESE: Ingen nødvendig hypotese.
UKENDT: Ingen afgørende ukendt observation.
NÆSTE_TRIN: KLAR TIL NÆSTE VURDERING"""},
 {"navn":"Skjult potentiale må ikke sælges direkte","forventet":"gratis","afgraensning":"""STATUS: AFGRÆNSET
PROBLEM: Kunden vil undersøge om der er uudnyttet tid mellem aftaler.
FAKTA: Kunden har ikke målt eller observeret tiden mellem aftaler.
HYPOTESE: Der kan være uudnyttet potentiale, men det er ikke dokumenteret.
UKENDT: Om der faktisk findes et konkret forbedringsproblem.
NÆSTE_TRIN: OBSERVATION MANGLER""","skjult_potentiale":True}
]

def koer_produktport_test():
    resultater = []
    api_kald = 0
    gammel_boks = st.session_state.valgt_problem
    try:
        for case in PRODUTPORT_CASES:
            st.session_state.valgt_problem = "Har jeg skjult potentiale?" if case.get("skjult_potentiale") else "Det burde kunne gøres lettere…"
            st.session_state.produktport_raa_output = None
            try:
                retning, output = vurder_produktport(case["afgraensning"])
            except Exception as fejl:
                resultater.append({"case":case["navn"],"forventet":case["forventet"],"faktisk":"fejl","bestaaet":False,"output":st.session_state.produktport_raa_output,"fejl":type(fejl).__name__})
                # Bevar delresultater og stop; ingen ekstra kald efter en fejl.
                break
            api_kald += 1
            resultater.append({"case":case["navn"],"forventet":case["forventet"],"faktisk":retning,"bestaaet":retning == case["forventet"],"output":st.session_state.produktport_raa_output})
    finally:
        st.session_state.valgt_problem = gammel_boks
    return resultater, api_kald


def lav_produktport_testlog(resultater, api_kald):
    linjer = [
        "TESTTYPE: Niveau 5 – Produktport (5 cases)",
        "TESTVERSION / COMMIT: ikke verificeret",
        f"DATO/TID: {datetime.now(timezone.utc).isoformat()} (UTC)",
    ]
    for nr, case in enumerate(PRODUTPORT_CASES, start=1):
        resultat = resultater[nr - 1] if nr <= len(resultater) else None
        linjer.extend(["", f"CASE {nr}: {case['navn']}", f"Forventet: {case['forventet']}"])
        if resultat is None:
            linjer.extend(["Faktisk: ikke kørt", "Fejl: kørslen blev afbrudt før denne case", "Rå output: ikke tilgængeligt"])
            continue
        linjer.extend([f"Faktisk: {resultat['faktisk']}", f"Fejl: {resultat.get('fejl', 'ingen')}"])
        linjer.append("Rå output – START")
        # Ingen strip, forkortelse eller omskrivning af modeloutput.
        linjer.append(resultat["output"] if resultat["output"] is not None else "[ikke tilgængeligt]")
        linjer.append("Rå output – SLUT")
    bestaaet = sum(1 for r in resultater if r["bestaaet"])
    fejl = sum(1 for r in resultater if r.get("fejl"))
    linjer.extend([
        "", "SAMLET RESULTAT",
        f"Bestået: {bestaaet}; fejlet: {len(resultater) - bestaaet}; ikke kørt: {len(PRODUTPORT_CASES) - len(resultater)}",
        f"Rapporteret antal API-kald med returneret og fortolket svar: {api_kald}",
        "Ved fejl kan et forsøgt kald være forbrugt uden at være talt med. Ingen automatisk genkørsel.",
        f"Øvrige fejl/delresultater: {'afbrudt efter casefejl; se ovenfor' if fejl else 'ingen'}",
    ])
    return "\n".join(linjer)


def nulstil_kundeflow():
    for navn in ("aktuelt_spoergsmaal", "observation_mangler", "undersoegelse_klar",
                 "udenfor_lean", "afgraensning", "afgraenser_feedback",
                 "flow_retning", "flow_besked", "flow_fejl", "flow_raa_output"):
        st.session_state[navn] = None
    st.session_state.samtale = []
    st.session_state.flow_haendelser = []
    st.session_state.flow_kald = 0
    st.session_state.flow_fase = "spoergsmaal"
    st.session_state.flow_log_aktiv = False
    # Fjern også tidligere formularværdier ved et nyt forløb.
    for navn in list(st.session_state.keys()):
        if navn.startswith("svar_"):
            del st.session_state[navn]


def kald_flow_rolle(rolle, funktion, *argumenter):
    haendelse = {"rolle": rolle, "tid": datetime.now(timezone.utc).isoformat(),
                 "svar_nr": len(st.session_state.samtale),
                 "raa_output": None, "resultat": None, "fejl": None}
    st.session_state.flow_haendelser.append(haendelse)
    st.session_state.flow_raa_output = None
    st.session_state.flow_log_aktiv = True
    st.session_state.flow_kald += 1
    try:
        resultat = funktion(*argumenter)
        haendelse["resultat"] = resultat
        return resultat
    except Exception as fejl:
        haendelse["fejl"] = type(fejl).__name__
        raise
    finally:
        haendelse["raa_output"] = st.session_state.flow_raa_output
        st.session_state.flow_log_aktiv = False


def afslut_kundeflow(retning, besked):
    st.session_state.flow_retning = retning
    st.session_state.flow_besked = besked
    st.session_state.flow_fase = "afsluttet"
    st.session_state.aktuelt_spoergsmaal = None


def fortsaet_kundeflow():
    """Kør eksisterende roller én gang pr. fase; stop ved spørgsmål, afslutning eller fejl."""
    if st.session_state.flow_fejl or st.session_state.flow_fase == "afsluttet":
        return
    try:
        if st.session_state.flow_fase == "undersoeger":
            # Bevar den eksisterende sikkerhedsgrænse: ingen ekstra spørgsmål efter ti svar.
            if len(st.session_state.samtale) >= 10:
                st.session_state.flow_fase = "afgraenser"
            else:
                handling, tekst = kald_flow_rolle("Undersøger", vurder_naeste_skridt)
                if handling == "udenfor":
                    st.session_state.udenfor_lean = tekst
                    afslut_kundeflow("stop", tekst)
                    return
                if handling == "observer":
                    st.session_state.observation_mangler = tekst
                    afslut_kundeflow("gratis", tekst)
                    return
                if handling == "spoerg":
                    st.session_state.aktuelt_spoergsmaal = tekst
                    st.session_state.flow_fase = "spoergsmaal"
                    return
                st.session_state.undersoegelse_klar = tekst
                st.session_state.flow_fase = "afgraenser"

        if st.session_state.flow_fase == "afgraenser":
            st.session_state.afgraensning = kald_flow_rolle("Afgrænser", lav_afgraensning)
            st.session_state.flow_fase = "feedback"

        if st.session_state.flow_fase == "feedback":
            handling, tekst = kald_flow_rolle("Returgate", vurder_afgraenser_feedback)
            st.session_state.afgraenser_feedback = tekst
            if handling == "spoerg":
                if len(st.session_state.samtale) >= 10:
                    st.session_state.flow_haendelser.append({"rolle": "Sikkerhedsgrænse", "resultat": "Returspørgsmål ikke stillet efter ti svar", "raa_output": None, "fejl": None})
                    afslut_kundeflow("gratis", "Der er stadig noget, der skal afklares. Der er ikke grundlag for et køb i dette forløb.")
                else:
                    st.session_state.aktuelt_spoergsmaal = tekst
                    st.session_state.undersoegelse_klar = None
                    st.session_state.afgraensning = None
                    st.session_state.afgraenser_feedback = None
                    st.session_state.flow_fase = "spoergsmaal"
                return
            if handling == "observer":
                st.session_state.observation_mangler = tekst
                afslut_kundeflow("gratis", tekst)
                return
            st.session_state.flow_fase = "produktport"

        if st.session_state.flow_fase == "produktport":
            retning, output = kald_flow_rolle("Produktport", vurder_produktport, st.session_state.afgraensning)
            # Fortolkeren i den eksisterende port falder tilbage til STOP ved ugyldigt output.
            # Et ugyldigt svar vises som teknisk fejl frem for en faglig kundeafslutning.
            gyldig_retning = any(linje.upper().startswith("RETNING:") and linje.split(":", 1)[1].strip().upper() in {"MIKROPRODUKT", "GRATIS", "MØDE", "MODE", "STOP"} for linje in output.splitlines())
            if not gyldig_retning:
                raise ValueError("Ugyldig Produktport-retning")
            if st.session_state.valgt_problem == "Har jeg skjult potentiale?" and retning == "mikroprodukt":
                # Håndhæv den eksisterende regel også ved et afvigende modelsvar.
                st.session_state.flow_haendelser.append({"rolle": "Potentiale-regel", "resultat": "Direkte mikroprodukt afvist; GRATIS. Rå portoutput bevaret.", "raa_output": None, "fejl": None})
                afslut_kundeflow("gratis", "Et muligt potentiale er ikke i sig selv grundlag for et køb. Hvis du opdager et konkret lille problem, kan du undersøge det i et separat forløb.")
                return
            begrundelse = "\n".join(linje.split(":", 1)[1].strip() for linje in output.splitlines() if linje.upper().startswith("BEGRUNDELSE:"))
            afslut_kundeflow(retning, begrundelse)
    except Exception as fejl:
        st.session_state.flow_fejl = type(fejl).__name__
        st.session_state.flow_haendelser.append({"rolle": "Forløbsfejl", "resultat": st.session_state.flow_fase, "raa_output": None, "fejl": type(fejl).__name__})
        # Ingen gentagelse ved rerun; kunden kan starte et nyt forløb eksplicit.


def lav_kundeflow_log():
    linjer = ["TESTTYPE: Normalt ende-til-ende-forløb", "TESTVERSION / COMMIT: ikke verificeret",
              f"LOGTID: {datetime.now(timezone.utc).isoformat()} (UTC)",
              f"VALGT BOKS: {st.session_state.valgt_problem}",
              f"VIRKSOMHED: {st.session_state.virksomhed}"]
    for nr, punkt in enumerate(st.session_state.samtale, start=1):
        linjer.extend(["", f"SPØRGSMÅL {nr}: {punkt['spoergsmaal']}", f"SVAR {nr}: {punkt['svar']}"])
    for nr, haendelse in enumerate(st.session_state.flow_haendelser, start=1):
        linjer.extend(["", f"HÆNDELSE {nr}: {haendelse['rolle']}",
                      f"TID: {haendelse.get('tid', 'ikke tilgængeligt')}",
                      f"EFTER KUNDESVAR NR.: {haendelse.get('svar_nr', 'ikke tilgængeligt')}",
                      f"Fortolket resultat: {haendelse['resultat']}",
                      f"Fejl: {haendelse['fejl'] or 'ingen'}", "Rå output – START",
                      haendelse["raa_output"] if haendelse["raa_output"] is not None else "[ikke tilgængeligt / ingen AI i dette trin]",
                      "Rå output – SLUT"])
    linjer.extend(["", f"ENDELIG KUNDERETNING: {st.session_state.flow_retning or 'ikke afsluttet'}",
                  f"KUNDEBESKED: {st.session_state.flow_besked or ''}",
                  f"FASE: {st.session_state.flow_fase}", f"FORLØBSFEJL: {st.session_state.flow_fejl or 'ingen'}",
                  f"Planlagte rollekald forsøgt: {st.session_state.flow_kald}",
                  "Faktiske API-forsøg, tokens og pris er ikke målt; SDK kan genforsøge et netværkskald."])
    return "\n".join(linjer)


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
 {"navn":"Flere processer","forventet_afgraensning":"FLERE_FORBUNDNE","boks":"Jeg mangler tid…","virksomhed":"produktion","forventet":"klar","samtale":[("Hvornår?","Leverancer forsinkes."),("Hvad sker der?","Indkøb mangler materialer, plan ændres, maskinen stopper og kvalitet får bunker."),("Én arbejdsgang?","Nej, indkøb, planlægning, produktion og kvalitet rammes hver uge.")]},
 {"navn":"Kræver observation","boks":"Jeg gør ting om nogle gange…","virksomhed":"kontor","forventet":"observer","samtale":[("Hvad gør du om?","Jeg leder efter rigtig dokumentversion og retter bagefter."),("Hvor ofte?","Det ved jeg ikke. Vi har aldrig holdt øje og jeg kan ikke vurdere det.")]},
 {"navn":"Prisfastsættelse","boks":"Har jeg skjult potentiale?","virksomhed":"fotograf","forventet":"udenfor","samtale":[("Hvor er potentialet?","Jeg tror mine priser er for lave."),("Hvad vil du have hjælp til?","At finde markedsprisen og hvad jeg bør tage.")]},
 {"navn":"Forkert boks – procesproblem","boks":"Jeg har noget, jeg ikke får brugt/solgt…","virksomhed":"cykelværksted","forventet":"klar","samtale":[("Hvad får du ikke brugt?","Min tid. Cykler venter på reservedele."),("Hvad sker der?","Jeg starter og opdager bagefter at en del mangler."),("Betydning?","Cyklen optager plads og arbejdet stopper flere gange om ugen.")]}
]

ROBUSTHEDSCASES = [
 {"navn":"B&B – vinter, hverdagssprog","boks":"Jeg har noget, jeg ikke får brugt/solgt…","virksomhed":"jeg lejer tre små lejligheder ud","forventet":"udenfor","samtale":[("Hvad står ubrugt?","Altså om sommeren går det fint, men når det bliver koldt kan de bare stå tomme uge efter uge."),("Kan folk booke dem?","Ja ja, de er åbne. Der er bare nærmest ingen der spørger om vinteren."),("Hvad tror du ligger bag?","Vi gør faktisk ikke noget særligt for at få vintergæster.")]},
 {"navn":"Café – rester, rodet svar","boks":"Jeg har noget, jeg ikke får brugt/solgt…","virksomhed":"lille café","forventet":"klar","samtale":[("Hvad oplever du?","Det er lidt forskelligt, men tit når vi lukker ligger der kager tilbage, nogle tager personalet og resten ryger ud."),("Er det enkeltstående?","Nej altså ikke præcis samme antal, men der er noget tilovers næsten hver dag.") ]},
 {"navn":"Kvalitetskontrol – nødvendig men tidskrævende","boks":"Jeg mangler tid…","virksomhed":"vi laver fødevarer","forventet":"spoerg","samtale":[("Hvor forsvinder tiden?","Den der kontrol vi skal lave hver gang. Den tager en krig."),("Hvorfor gør I den?","Den skal vi. Det er fødevaresikkerhed, så den kan vi jo ikke bare springe over.") ]},
 {"navn":"Flere processer – hverdagsbeskrivelse","forventet_afgraensning":"FLERE_FORBUNDNE","boks":"Det burde kunne gøres lettere…","virksomhed":"mindre produktion","forventet":"klar","samtale":[("Hvad bøvler?","Det starter tit med at noget ikke er kommet hjem, så laver planlægning det hele om, folk står og venter, og så hober tingene sig op ved kvalitet."),("Sker det flere steder?","Ja, det er både indkøb, planlægning, folk ude ved maskinerne og kvalitet. Det er ikke bare én ting.") ]},
 {"navn":"Forkert boks – reservedele","boks":"Jeg har noget, jeg ikke får brugt/solgt…","virksomhed":"cykler og reparation","forventet":"klar","samtale":[("Hvad får du ikke brugt?","Det er nok mest tiden. Jeg går i gang med en cykel og så mangler den åndssvage lille del igen."),("Hvad betyder det?","Så står cyklen bare der og fylder, og jeg må stoppe og tage noget andet. Det sker flere gange på en uge.") ]}
]

def koer_robusthedstest():
    gemt = (st.session_state.valgt_problem, st.session_state.virksomhed, list(st.session_state.samtale), st.session_state.undersoegelse_klar, st.session_state.observation_mangler, st.session_state.afgraensning)
    resultater = []
    api_kald = 0
    try:
        for case in ROBUSTHEDSCASES:
            st.session_state.valgt_problem = case["boks"]
            st.session_state.virksomhed = case["virksomhed"]
            st.session_state.samtale = [{"spoergsmaal": q, "svar": a} for q, a in case["samtale"]]
            handling, tekst = vurder_naeste_skridt()
            api_kald += 1
            status = None
            afgraensning_output = ""
            forventet_status = None
            korrekt = handling == case["forventet"]
            if handling == "klar":
                st.session_state.undersoegelse_klar = tekst
                st.session_state.observation_mangler = None
                afgraensning_output = lav_afgraensning()
                api_kald += 1
                for linje in afgraensning_output.splitlines():
                    if linje.upper().startswith("STATUS:"):
                        status = linje.split(":", 1)[1].strip().upper()
                        break
                forventet_status = case.get("forventet_afgraensning", "AFGRÆNSET")
                korrekt = korrekt and status == forventet_status
            resultater.append({"case":case["navn"],"forventet":case["forventet"],"faktisk":handling,"status":status,"forventet_status":forventet_status,"bestaaet":korrekt,"output":tekst,"afgraensning_output":afgraensning_output})
    finally:
        st.session_state.valgt_problem, st.session_state.virksomhed, st.session_state.samtale, st.session_state.undersoegelse_klar, st.session_state.observation_mangler, st.session_state.afgraensning = gemt
    return resultater, api_kald

def koer_testbatteri():
    gemt = (st.session_state.valgt_problem, st.session_state.virksomhed, list(st.session_state.samtale), st.session_state.undersoegelse_klar, st.session_state.observation_mangler, st.session_state.afgraensning)
    resultater = []
    try:
        for case in TESTCASES:
            st.session_state.valgt_problem = case["boks"]
            st.session_state.virksomhed = case["virksomhed"]
            st.session_state.samtale = [{"spoergsmaal": q, "svar": a} for q, a in case["samtale"]]
            handling, tekst = vurder_naeste_skridt()
            triage_ok = handling == case["forventet"]
            status = None
            forventet_status = None
            afgraensning_output = ""
            afgraensning_ok = True
            if handling == "klar":
                st.session_state.undersoegelse_klar = tekst
                st.session_state.observation_mangler = None
                afgraensning_output = lav_afgraensning()
                for linje in afgraensning_output.splitlines():
                    if linje.upper().startswith("STATUS:"):
                        status = linje.split(":", 1)[1].strip().upper()
                        break
                forventet_status = case.get("forventet_afgraensning", "AFGRÆNSET")
                afgraensning_ok = status == forventet_status
            resultater.append({"case":case["navn"],"forventet":case["forventet"],"faktisk":handling,"forventet_status":forventet_status,"status":status,"bestaaet":triage_ok and afgraensning_ok,"output":tekst,"afgraensning_output":afgraensning_output})
    finally:
        st.session_state.valgt_problem, st.session_state.virksomhed, st.session_state.samtale, st.session_state.undersoegelse_klar, st.session_state.observation_mangler, st.session_state.afgraensning = gemt
    return resultater

def koer_stabilitetstest(gentagelser=3):
    # Bevidst lille test: kun de grænsecases, der tidligere har vist følsomhed.
    navne = {"Café – kassation", "Nødvendig kvalitetskontrol", "Flere processer"}
    cases = [case for case in TESTCASES if case["navn"] in navne]
    gemt = (st.session_state.valgt_problem, st.session_state.virksomhed, list(st.session_state.samtale), st.session_state.undersoegelse_klar, st.session_state.observation_mangler, st.session_state.afgraensning)
    resultater = []
    api_kald = 0
    try:
        for case in cases:
            koersler = []
            for _ in range(gentagelser):
                st.session_state.valgt_problem = case["boks"]
                st.session_state.virksomhed = case["virksomhed"]
                st.session_state.samtale = [{"spoergsmaal": q, "svar": a} for q, a in case["samtale"]]
                handling, tekst = vurder_naeste_skridt()
                api_kald += 1
                status = None
                afgraensning_output = ""
                forventet_status = None
                korrekt = handling == case["forventet"]
                if handling == "klar":
                    st.session_state.undersoegelse_klar = tekst
                    st.session_state.observation_mangler = None
                    afgraensning_output = lav_afgraensning()
                    api_kald += 1
                    for linje in afgraensning_output.splitlines():
                        if linje.upper().startswith("STATUS:"):
                            status = linje.split(":", 1)[1].strip().upper()
                            break
                    forventet_status = case.get("forventet_afgraensning", "AFGRÆNSET")
                    korrekt = korrekt and status == forventet_status
                koersler.append({
                    "handling": handling, "status": status, "korrekt": korrekt,
                    "output": tekst, "afgraensning_output": afgraensning_output,
                    "forventet_status": forventet_status
                })
            resultater.append({
                "case": case["navn"], "forventet": case["forventet"],
                "koersler": koersler,
                "stabil": len({(k["handling"], k["status"]) for k in koersler}) == 1,
                "alle_korrekte": all(k["korrekt"] for k in koersler)
            })
    finally:
        st.session_state.valgt_problem, st.session_state.virksomhed, st.session_state.samtale, st.session_state.undersoegelse_klar, st.session_state.observation_mangler, st.session_state.afgraensning = gemt
    return resultater, api_kald

# SKÆRM 1 – vælg situation
if st.session_state.valgt_problem is None:

    st.divider()
    with st.expander("🧪 Testlab – beslutningsmotor", expanded=False):
        st.caption("Testniveau 2: 12 grænsecases gennem Undersøgeren og Afgrænseren, når sagen er KLAR.")
        if st.button("Kør automatisk testbatteri", key="koer_testbatteri"):
            with st.spinner("Tester beslutningsmotoren…"):
                try:
                    resultater = koer_testbatteri()
                    bestaaet = sum(1 for r in resultater if r["bestaaet"])
                    st.write(f"**Resultat: {bestaaet}/{len(resultater)} bestået**")
                    for nr, r in enumerate(resultater, start=1):
                        ikon = "✅" if r["bestaaet"] else "❌"
                        st.write(f"{ikon} **{r['case']}** — forventet: {r['forventet']}, faktisk: {r['faktisk']}")
                        with st.expander(f"Se hele beslutningskæden – test {nr}", expanded=not r["bestaaet"]):
                            st.write("**Undersøgerens beslutning**")
                            st.text(r["output"])
                            if r["faktisk"] == "klar":
                                st.write("**Afgrænserens forventede status**")
                                st.text(r["forventet_status"] or "Ikke angivet")
                                st.write("**Afgrænserens faktiske output**")
                                st.text(r["afgraensning_output"] or "Intet output")
                            else:
                                st.caption("Sagen blev ikke sendt til Afgrænseren i denne test.")
                except Exception:
                    st.error("Testbatteriet kunne ikke gennemføres. Prøv igen om lidt.")

        st.divider()
        st.caption("Testniveau 3: stabilitet. Tre følsomme grænsecases køres 3 gange hver. Det holder API-forbruget nede.")
        if st.button("Kør stabilitetstest (3 × 3)", key="koer_stabilitetstest"):
            with st.spinner("Kører 9 gentagelser og sammenligner beslutningerne…"):
                try:
                    stabilitet, api_kald = koer_stabilitetstest(3)
                    helt_stabile = sum(1 for r in stabilitet if r["stabil"] and r["alle_korrekte"])
                    st.write(f"**Stabilitet: {helt_stabile}/{len(stabilitet)} cases stabile og korrekte**")
                    st.caption(f"API-kald i denne kørsel: {api_kald}. KLAR-svar bruger et ekstra kald til Afgrænseren.")
                    for r in stabilitet:
                        ikon = "✅" if r["stabil"] and r["alle_korrekte"] else "⚠️"
                        beslutninger = ", ".join(
                            f"{k['handling']}" + (f" → {k['status']}" if k["status"] else "")
                            for k in r["koersler"]
                        )
                        st.write(f"{ikon} **{r['case']}** — {beslutninger}")
                        with st.expander(f"Se de 3 kørsler – {r['case']}", expanded=not (r["stabil"] and r["alle_korrekte"])):
                            for nr, k in enumerate(r["koersler"], start=1):
                                st.write(f"**Kørsel {nr}: {k['handling']}**" + (f" → {k['status']}" if k["status"] else ""))
                                st.text(k["output"])
                                if k["afgraensning_output"]:
                                    st.write("Afgrænser:")
                                    st.text(k["afgraensning_output"])
                except Exception:
                    st.error("Stabilitetstesten kunne ikke gennemføres. Prøv igen om lidt.")

        st.divider()
        st.caption("Testniveau 4: robusthed. Samme typer problemer er skrevet om til mere naturligt, rodet hverdagssprog. Ingen ekstra gentagelser.")
        if st.button("Kør robusthedstest (5 nye formuleringer)", key="koer_robusthedstest"):
            with st.spinner("Tester om motoren forstår mekanismen bag andre formuleringer…"):
                try:
                    robusthed, api_kald = koer_robusthedstest()
                    bestaaet = sum(1 for r in robusthed if r["bestaaet"])
                    st.write(f"**Robusthed: {bestaaet}/{len(robusthed)} bestået**")
                    st.caption(f"API-kald i denne kørsel: {api_kald}. Testene bruger nye formuleringer, men samme beslutningsprincipper.")
                    for nr, r in enumerate(robusthed, start=1):
                        ikon = "✅" if r["bestaaet"] else "❌"
                        status = f" → {r['status']}" if r["status"] else ""
                        st.write(f"{ikon} **{r['case']}** — forventet: {r['forventet']}, faktisk: {r['faktisk']}{status}")
                        with st.expander(f"Se robusthedscase {nr}", expanded=not r["bestaaet"]):
                            st.write("**Undersøger**")
                            st.text(r["output"])
                            if r["afgraensning_output"]:
                                st.write("**Afgrænser**")
                                st.text(r["afgraensning_output"])
                except Exception:
                    st.error("Robusthedstesten kunne ikke gennemføres. Prøv igen om lidt.")

        st.divider()
        st.caption("Testniveau 5: Produktporten. Tester om et afgrænset problem skal blive mikroprodukt, gratis hjælp, møde eller stop.")
        if st.button("Kør Produktport-test (5 cases)", key="koer_produktport_test"):
            st.session_state.produktport_testlog = None
            with st.spinner("Tester om porten kan lade være med at sælge, når den ikke bør…"):
                try:
                    portresultater, api_kald = koer_produktport_test()
                    bestaaet = sum(1 for r in portresultater if r["bestaaet"])
                    st.write(f"**Produktport: {bestaaet}/{len(portresultater)} bestået**")
                    st.caption(f"API-kald i denne kørsel: {api_kald}. Ét kald pr. case.")
                    for nr, r in enumerate(portresultater, start=1):
                        ikon = "✅" if r["bestaaet"] else "❌"
                        st.write(f"{ikon} **{r['case']}** — forventet: {r['forventet']}, faktisk: {r['faktisk']}")
                        with st.expander(f"Se Produktport-case {nr}", expanded=not r["bestaaet"]):
                            st.text(r["output"] if r["output"] is not None else "Rå output er ikke tilgængeligt.")
                    st.session_state.produktport_testlog = lav_produktport_testlog(portresultater, api_kald)
                except Exception as fejl:
                    st.session_state.produktport_testlog = lav_produktport_testlog([], 0) + f"\nKørselsfejl: {type(fejl).__name__}. Resultater og antal API-kald kunne ikke fastslås."
                    st.error("Produktport-testen kunne ikke gennemføres. Bevar resultatet; genkør ikke automatisk.")

        if st.session_state.get("produktport_testlog"):
            st.write("**Produktport-testlog – kopiér hele kørslen**")
            st.code(st.session_state.produktport_testlog, language=None)

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
            nulstil_kundeflow()
            st.session_state.virksomhed = None
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


# SKÆRM 3 – én sammenhængende samtale med automatiske interne overgange
else:
    st.subheader("Lad os se lidt nærmere på det")

    for nummer, punkt in enumerate(st.session_state.samtale, start=1):
        with st.expander(f"Tidligere svar {nummer}", expanded=False):
            st.write(f"**Spørgsmål:** {punkt['spoergsmaal']}")
            st.write(f"**Dit svar:** {punkt['svar']}")

    if st.session_state.flow_fejl:
        st.error("Vi kunne ikke færdiggøre vurderingen lige nu. Dine svar er bevaret i dette forløb.")
    elif st.session_state.flow_fase == "afsluttet":
        retning = st.session_state.flow_retning
        if retning == "mikroprodukt":
            st.success("Dit afgrænsede problem ser egnet ud til et lille, enkelt værktøj.")
            st.write(st.session_state.flow_besked)
            st.write("Du kan endnu ikke købe eller få lavet værktøjet her.")
        elif retning == "gratis":
            if st.session_state.observation_mangler:
                st.info("Næste skridt er at observere det, vi mangler at vide, i dit daglige arbejde.")
                st.write(st.session_state.observation_mangler)
            else:
                st.info("Du kan komme videre uden at købe et værktøj her.")
                st.write(st.session_state.flow_besked)
            st.write("Der er ikke grundlag for et køb i dette forløb.")
        elif retning == "moede":
            st.info("Problemstillingen ser ud til at involvere flere forhold og bør ikke presses ned i et lille standardværktøj.")
            st.write(st.session_state.flow_besked)
            st.write("Du har mulighed for et gratis, uforpligtende møde med Annette om dit problem. Tidspunkt aftales direkte med Annette.")
        else:
            st.info("Mikro LEAN Manager er ikke det rette sted at hjælpe med det beskrevne problem.")
            st.write(st.session_state.flow_besked)
    else:
        st.write(st.session_state.aktuelt_spoergsmaal)
        svar = st.text_area(
            "Skriv med dine egne ord:",
            placeholder="Du behøver ikke kende årsagen – beskriv bare, hvad du oplever.",
            key=f"svar_{len(st.session_state.samtale)}"
        )
        if st.button("Gem svar og fortsæt", use_container_width=True):
            if svar.strip():
                st.session_state.samtale.append({
                    "spoergsmaal": st.session_state.aktuelt_spoergsmaal,
                    "svar": svar.strip()
                })
                st.session_state.flow_fase = "undersoeger"
                with st.spinner("Vi ser nærmere på dine svar…"):
                    fortsaet_kundeflow()
                st.rerun()
            else:
                st.warning("Skriv lidt om det, du oplever, før du fortsætter.")

    # Intern testvisning er kun synlig, når URL'en indeholder ?testlog=1.
    if st.query_params.get("testlog") == "1" and st.session_state.samtale:
        st.divider()
        with st.expander("Intern testlog – kopiér hele forløbet", expanded=False):
            st.code(lav_kundeflow_log(), language=None)

    if st.button("Start et nyt forløb", key="nyt_forloeb"):
        nulstil_kundeflow()
        st.session_state.virksomhed = None
        st.session_state.valgt_problem = None
        st.rerun()
