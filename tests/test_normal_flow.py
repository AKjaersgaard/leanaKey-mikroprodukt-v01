"""Offline integration checks. Load real functions without starting Streamlit or OpenAI."""
import ast
from datetime import datetime, timezone
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import unittest
from contextlib import nullcontext
import sys
from types import ModuleType
from unittest.mock import patch


class State(dict):
    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value


class NormalFlowTests(unittest.TestCase):
    def setUp(self):
        self.state = State(valgt_problem="Det burde kunne gøres lettere…", virksomhed="testfirma",
                           samtale=[], aktuelt_spoergsmaal="Hvad oplever du?",
                           observation_mangler=None, undersoegelse_klar=None, udenfor_lean=None,
                           afgraensning=None, afgraenser_feedback=None, flow_fase="spoergsmaal",
                           flow_retning=None, flow_besked=None, flow_fejl=None,
                           flow_haendelser=[], flow_kald=0, flow_log_aktiv=False, flow_raa_output=None)
        self.outputs = []
        self.calls = []
        self.ns = {"st": SimpleNamespace(session_state=self.state),
                   "datetime": datetime, "timezone": timezone, "deepcopy": deepcopy,
                   "client": SimpleNamespace(responses=SimpleNamespace(create=self.response))}
        self.tree = ast.parse((Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8"))
        nodes = [n for n in self.tree.body if isinstance(n, ast.FunctionDef)]
        exec(compile(ast.Module(body=nodes, type_ignores=[]), "app.py", "exec"), self.ns)

    def response(self, **kwargs):
        self.calls.append(kwargs)
        self.assertEqual(kwargs["model"], "gpt-5.6-luna")
        output = self.outputs.pop(0)
        if isinstance(output, Exception):
            raise output
        return SimpleNamespace(output_text=output)

    def answer(self, text="Det sker gentagne gange og stopper arbejdet"):
        self.state.samtale.append({"spoergsmaal": self.state.aktuelt_spoergsmaal, "svar": text})
        self.state.flow_fase = "undersoeger"
        self.ns["fortsaet_kundeflow"]()
        self.ns["opdater_flow_log"]()

    def assert_no_repeat(self):
        count = len(self.calls)
        self.ns["fortsaet_kundeflow"]()
        self.assertEqual(len(self.calls), count)

    def test_six_entry_questions(self):
        for box in ("Jeg mangler tid…", "Jeg mangler noget for at komme videre…",
                    "Jeg gør ting om nogle gange…", "Det burde kunne gøres lettere…",
                    "Jeg har noget, jeg ikke får brugt/solgt…", "Har jeg skjult potentiale?"):
            self.assertIn("testfirma", self.ns["foerste_spoergsmaal"](box, "testfirma"))
        self.assertEqual(self.calls, [])

    def test_four_port_endings_and_full_raw_log(self):
        for raw_direction, expected in (("MIKROPRODUKT", "mikroprodukt"), ("GRATIS", "gratis"),
                                        ("MØDE", "moede"), ("STOP", "stop")):
            self.setUp()
            raw = f"\nRETNING: {raw_direction}\nBEGRUNDELSE: Faglig begrundelse.  \n\n"
            self.outputs = ["SPØRG: Hvornår?", "KLAR: Dokumenteret problem.",
                            "STATUS: AFGRÆNSET\nNÆSTE_TRIN: KLAR TIL NÆSTE VURDERING",
                            "VIDERE: Intet afgørende mangler.", raw]
            self.answer()
            self.assertEqual(self.state.flow_fase, "spoergsmaal")
            self.assertEqual(self.state.aktuelt_spoergsmaal, "Hvornår?")
            self.answer()
            self.assertEqual(self.state.flow_retning, expected)
            self.assertEqual(len(self.calls), 5)
            log = self.ns["lav_kundeflow_log"]()
            self.assertIn(raw, log)
            self.assertIn("ikke verificeret", log)
            self.assertIn("RETURGATE", log)
            self.assertIn("EFTER KUNDESVAR NR.: 2", log)
            self.assert_no_repeat()

    def test_return_question_uses_updated_conversation(self):
        self.outputs = ["KLAR: Grundlag.", "STATUS: AFGRÆNSET", "SPØRG: Hvad ved du allerede?",
                        "KLAR: Nyt grundlag.", "STATUS: AFGRÆNSET", "VIDERE: Nok viden.",
                        "RETNING: GRATIS\nBEGRUNDELSE: Viden er allerede kendt."]
        self.answer()
        self.assertEqual(self.state.aktuelt_spoergsmaal, "Hvad ved du allerede?")
        self.assertIsNone(self.state.afgraensning)
        self.answer("Jeg har allerede registreret arbejdet.")
        self.assertEqual(self.state.flow_retning, "gratis")
        self.assertIn("Jeg har allerede registreret arbejdet.", self.calls[3]["input"])
        self.assertEqual([e["rolle"] for e in self.state.flow_haendelser],
                         ["Undersøger", "Afgrænser", "Returgate", "Undersøger", "Afgrænser", "Returgate", "Produktport"])

    def test_early_observation_and_outside(self):
        for output, expected in (("OBSERVÉR: Hvor ofte det sker.", "gratis"),
                                 ("UDENFOR: Primært markedsføring.", "stop")):
            self.setUp()
            self.outputs = [output]
            self.answer()
            self.assertEqual(self.state.flow_retning, expected)
            self.assertEqual(len(self.calls), 1)
            self.assert_no_repeat()

    def test_feedback_observation_stops_without_port(self):
        self.outputs = ["KLAR: Grundlag.", "STATUS: IKKE_AFGRÆNSET", "OBSERVÉR: Antal afbrydelser."]
        self.answer()
        self.assertEqual(self.state.flow_retning, "gratis")
        self.assertEqual(self.state.observation_mangler, "Antal afbrydelser.")
        self.assertEqual(len(self.calls), 3)

    def test_box_six_blocks_deviant_microproduct_without_more_calls(self):
        self.state.valgt_problem = "Har jeg skjult potentiale?"
        self.outputs = ["KLAR: Grundlag.", "STATUS: AFGRÆNSET", "VIDERE: Nok.",
                        "RETNING: MIKROPRODUKT\nBEGRUNDELSE: Afvigende svar."]
        self.answer()
        self.assertEqual(self.state.flow_retning, "gratis")
        self.assertEqual(len(self.calls), 4)
        self.assertIn("RETNING: MIKROPRODUKT", self.ns["lav_kundeflow_log"]())
        self.assertIn("POTENTIALE-REGEL", self.ns["lav_kundeflow_log"]())

    def test_role_errors_preserve_partial_results_and_do_not_retry(self):
        success = ["KLAR: Grundlag.", "STATUS: AFGRÆNSET", "VIDERE: Nok."]
        for stage in range(4):
            self.setUp()
            self.outputs = success[:stage] + [RuntimeError("do not expose secret detail")]
            self.answer()
            self.assertEqual(self.state.flow_fejl, "RuntimeError")
            self.assertEqual(len(self.calls), stage + 1)
            log = self.ns["lav_kundeflow_log"]()
            self.assertNotIn("secret detail", log)
            self.assertIn("RuntimeError", log)
            self.assertEqual(len(self.state.samtale), 1)
            self.assert_no_repeat()

    def test_invalid_port_output_is_error_not_factual_stop(self):
        self.outputs = ["KLAR: Grundlag.", "STATUS: AFGRÆNSET", "VIDERE: Nok.", "Uventet tekst"]
        self.answer()
        self.assertEqual(self.state.flow_fejl, "ValueError")
        self.assertIsNone(self.state.flow_retning)
        self.assertIn("Uventet tekst", self.ns["lav_kundeflow_log"]())
        self.assert_no_repeat()

    def test_ten_answer_limit_prevents_feedback_question_loop(self):
        self.state.samtale = [{"spoergsmaal": "Q", "svar": "A"}] * 9
        self.outputs = ["STATUS: IKKE_AFGRÆNSET", "SPØRG: Mere?"]
        self.answer()
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(self.state.flow_retning, "gratis")
        self.assertIn("SIKKERHEDSGRÆNSE", self.ns["lav_kundeflow_log"]())

    def test_raw_output_is_saved_immediately_before_role_returns(self):
        raw = "\n  FULDT RÅ OUTPUT  \n\n"
        def role():
            self.ns["gem_flow_output"](raw)
            event = self.state.flow_haendelser[-1]
            self.assertEqual(event["raa_output"], raw)
            self.assertIn("modtaget_tid", event)
            self.assertIsNone(event["resultat"])
            raise ValueError("fortolkning fejlede efter modtagelse")
        with self.assertRaises(ValueError):
            self.ns["kald_flow_rolle"]("Undersøger", role)
        self.assertEqual(self.state.flow_haendelser[-1]["raa_output"], raw)
        self.assertIsNone(self.state.flow_aktiv_haendelse)
        self.assertIn(raw, self.ns["lav_kundeflow_log"]())

    def test_call_snapshots_and_actual_next_actions_are_preserved(self):
        self.outputs = ["SPØRG: Hvornår?", "KLAR: Grundlag.", "STATUS: AFGRÆNSET",
                        "VIDERE: Nok.", "RETNING: GRATIS\nBEGRUNDELSE: Kendt viden."]
        self.answer("første faktiske svar")
        first = self.state.flow_haendelser[0]
        self.assertEqual(first["naeste_handling"], "Stil kundespørgsmål: Hvornår?")
        self.answer("andet faktiske svar")
        self.assertEqual(len(first["grundlag"]["samtale"]), 1)
        self.assertEqual(first["grundlag"]["samtale"][0]["svar"], "første faktiske svar")
        events = self.state.flow_haendelser
        self.assertEqual([e["kaldnummer"] for e in events], [1, 2, 3, 4, 5])
        self.assertEqual(events[1]["naeste_handling"], "Aktivér AFGRÆNSER")
        self.assertEqual(events[2]["naeste_handling"], "Aktivér RETURGATE")
        self.assertEqual(events[3]["naeste_handling"], "Aktivér PRODUKTPORT")
        self.assertEqual(events[4]["naeste_handling"], "Afslut: gratis")
        log = self.ns["lav_kundeflow_log"]()
        self.assertIn("ANTAL KUNDESVAR: 2", log)
        self.assertIn("FORTOLKET AFGRÆNSERSTATUS: STATUS: AFGRÆNSET", log)
        self.assertIn("SAMTALEGRUNDLAG VED KALD", log)

    def test_new_flow_clears_old_data_and_widgets(self):
        self.state.svar_0 = "gammelt svar"
        self.state.flow_retning = "gratis"
        self.state.flow_fejl = "RuntimeError"
        self.state.flow_haendelser = [{"gammel": True}]
        self.ns["nulstil_kundeflow"]()
        self.assertNotIn("svar_0", self.state)
        self.assertIsNone(self.state.flow_retning)
        self.assertIsNone(self.state.flow_fejl)
        self.assertEqual(self.state.flow_haendelser, [])
        self.assertEqual(self.state.flow_fase, "spoergsmaal")

    def test_actual_screen_flow_and_hidden_debug_log(self):
        """Run the full app with UI stubs; no Streamlit/OpenAI package or network needed."""
        source = (Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8")
        fake_st = ModuleType("streamlit")
        fake_st.session_state = self.state
        fake_st.secrets = {"OPENAI_API_KEY": "offline-placeholder"}
        fake_st.query_params = {}
        displays, buttons = [], []
        selected_button = [None]
        answer_text = ["Gentaget tab i arbejdet."]
        class Rerun(Exception):
            pass
        def button(label, **kwargs):
            buttons.append(label)
            return label == selected_button[0]
        def display(*args, **kwargs):
            displays.extend(str(x) for x in args)
        for name in ("title", "subheader", "write", "info", "success", "error", "warning", "text", "code", "caption"):
            setattr(fake_st, name, display)
        fake_st.set_page_config = lambda **kwargs: None
        fake_st.divider = lambda: None
        fake_st.expander = lambda *args, **kwargs: nullcontext()
        fake_st.spinner = lambda *args, **kwargs: nullcontext()
        fake_st.text_area = lambda *args, **kwargs: answer_text[0]
        fake_st.text_input = lambda *args, **kwargs: "testfirma"
        fake_st.button = button
        def rerun():
            raise Rerun()
        fake_st.rerun = rerun
        fake_openai = ModuleType("openai")
        fake_openai.OpenAI = lambda **kwargs: self.ns["client"]
        def run():
            displays.clear()
            buttons.clear()
            with patch.dict(sys.modules, {"streamlit": fake_st, "openai": fake_openai}):
                try:
                    exec(compile(source, "app.py", "exec"), {})
                except Rerun:
                    pass
        # An actual customer submission automatically runs all four existing roles.
        self.outputs = ["KLAR: Grundlag.", "STATUS: AFGRÆNSET", "VIDERE: Nok.",
                        "RETNING: GRATIS\nBEGRUNDELSE: Kendt viden giver intet nyt køb."]
        selected_button[0] = "Gem svar og fortsæt"
        run()
        self.assertEqual(self.state.flow_retning, "gratis")
        self.assertEqual(len(self.calls), 4)
        selected_button[0] = None
        run()
        self.assertTrue(any("uden at købe" in x for x in displays))
        self.assertNotIn("Gem svar og fortsæt", buttons)
        self.assertFalse(any("TESTTYPE:" in x for x in displays))
        self.assertFalse(any(x in buttons for x in ("Send til Afgrænseren", "Kontrollér om der mangler noget", "Kør Produktport")))
        # Debug URL exposes only the copyable log; rerenders make no AI calls.
        fake_st.query_params["testlog"] = "1"
        run()
        self.assertTrue(any("TESTTYPE: Normalt ende-til-ende" in x for x in displays))
        self.assertEqual(len(self.calls), 4)
        selected_button[0] = "Start et nyt forløb"
        run()
        self.assertIsNone(self.state.valgt_problem)
        self.assertIsNone(self.state.virksomhed)
        self.assertEqual(self.state.samtale, [])
        self.assertEqual(self.state.flow_haendelser, [])
        # Front screen still contains existing Testlab and all six entry buttons.
        selected_button[0] = None
        run()
        self.assertIn("Kør Produktport-test (5 cases)", buttons)
        self.assertIn("Har jeg skjult potentiale?", buttons)
        selected_button[0] = "Jeg mangler tid…"
        run()
        self.assertEqual(self.state.valgt_problem, "Jeg mangler tid…")
        selected_button[0] = "Fortsæt"
        run()
        self.assertEqual(self.state.virksomhed, "testfirma")
        self.assertIn("testfirma", self.state.aktuelt_spoergsmaal)
        self.assertEqual(len(self.calls), 4)


if __name__ == "__main__":
    unittest.main()
