"""
Test della pipeline di generazione (Passo 3a, 2026-10-05), nello stile di retrieval/test_retrieval.py: script, non
pytest. NESSUNA chiamata a un LLM reale: MockClient e un server HTTP finto su 127.0.0.1.

Uso:
    python generation/test_generation.py
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import shutil
import socket
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "experiments"))
import plantuml_postprocess as ppu  # noqa: E402
import postprocess as pp  # noqa: E402
import run_experiment as rx  # noqa: E402
import analyze_pilot as ap  # noqa: E402
import select_pilot  # noqa: E402
import smoke_lmstudio as sm  # noqa: E402
import token_estimate  # noqa: E402
from llm_client import CachedClient, GenerationParams, LMStudioClient, MockClient, cache_key  # noqa: E402
from prompt_builder import V4_TEMPLATE, PromptBuilder, PromptSpec, cl  # noqa: E402

MINI = {"version": "4.2.0", "id": "t", "title": "T", "type": "ClassDiagram", "assessments": {}, "edges": [
    {"id": "e1", "source": "n1", "target": "n2", "type": "ClassBidirectional", "sourceHandle": "right",
     "targetHandle": "left", "data": {"points": [{"x": 260, "y": 90}, {"x": 400, "y": 90}], "label": "",
                                      "sourceMultiplicity": "1", "targetMultiplicity": "1..n", "sourceRole": "",
                                      "targetRole": ""}}], "nodes": [
    {"id": "n1", "type": "class", "position": {"x": 40, "y": 40}, "width": 220, "height": 100,
     "measured": {"width": 220, "height": 100},
     "data": {"name": "Alpha", "attributes": [{"id": "a1", "name": "+ code : string"}],
              "methods": [{"id": "m1", "name": "describe(): string"}]}},
    {"id": "n2", "type": "class", "position": {"x": 400, "y": 40}, "width": 220, "height": 100,
     "measured": {"width": 220, "height": 100}, "data": {"name": "Beta", "attributes": [], "methods": []}}]}
MINI_TXT = json.dumps(MINI)


def snapshot_corpus() -> dict[str, str]:
    out = {}
    for p in sorted((ROOT / "corpus").rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            out[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


# --- prompt ---------------------------------------------------------------------------------------------------------


def check_prompts(builder: PromptBuilder, queries: list[dict]) -> None:
    v4_lines = V4_TEMPLATE.read_text(encoding="utf-8").split("\n")
    assert builder.instructions == "\n".join(v4_lines[:69]) + "\n", "istruzioni diverse dal template v4"
    spec = PromptSpec("bm25")
    assert (spec.serialization, spec.layout, spec.drop_interactive) == ("compact", "user_only", True)
    n = 0
    for q in queries:
        built = {}
        for cond in ("zero_shot", "static", "random", "bm25", "oracle"):
            for k in (1, 3):
                s = PromptSpec(cond, k=k)
                a, b = builder.build(q, s), builder.build(q, s)
                assert a.text == b.text and a.messages == b.messages and a.example_ids == b.example_ids, "non determ."
                assert not any(e in builder.test_ids or cl.DEBARI_ID_RE.match(e) for e in a.example_ids)
                assert a.messages == [{"role": "user", "content": a.text}]
                assert a.text == a.instructions + "\n" + (a.examples_block + "\n" if a.examples_block else "") + a.task
                assert '"interactive"' not in a.examples_block
                built[(cond, k)] = a
                n += 1
        ref = built[("zero_shot", 1)]
        assert ref.examples_block == "" and ref.example_ids == []
        for a in built.values():  # le condizioni differiscono SOLO nel blocco esempi
            assert a.instructions == ref.instructions and a.task == ref.task
        assert len(built[("bm25", 3)].example_ids) == 3 and len(built[("static", 1)].example_ids) == 2
    rejected = False
    try:
        PromptBuilder(builder.candidates + [dict(queries[1])], queries)  # esercizio del test set tra i candidati
    except (AssertionError, SystemExit, ValueError):
        rejected = True
    assert rejected, "candidato del test set non rifiutato"
    print(f"  OK  {n} prompt: deterministici, istruzioni v4 identiche, solo il blocco esempi cambia, nessun id del "
          "test set tra gli esempi, default compact / user_only / drop_interactive")


# --- client e cache -------------------------------------------------------------------------------------------------


def check_cache(tmp: Path) -> None:
    mock = MockClient({"default": MINI_TXT})
    c = CachedClient(mock, tmp / "cache")
    m1, m2 = [{"role": "user", "content": "a"}], [{"role": "user", "content": "b"}]
    p = GenerationParams(seed=1)
    r1, r2 = c.generate(m1, p, 0), c.generate(m1, p, 0)
    assert mock.calls == 1 and not r1.cached and r2.cached and r2.text == r1.text
    c.generate(m1, p, 1)
    c.generate(m2, p, 0)
    c.generate(m1, GenerationParams(seed=2), 0)
    assert mock.calls == 4, mock.calls
    assert cache_key(m1, "x", p, 0) != cache_key(m2, "x", p, 0) != cache_key(m1, "y", p, 0)
    sys_user = [{"role": "system", "content": "a"}, {"role": "user", "content": ""}]
    assert cache_key(sys_user, "x", p, 0) != cache_key([{"role": "user", "content": "a"}], "x", p, 0)
    print("  OK  cache: stessa chiamata servita dal disco; messaggi, modello, parametri e ripetizione nella chiave")


REASONING_TXT = 'The user wants classes. Draft: {"version": "4.2.0", "nodes": []}'


class FakeLMStudio(BaseHTTPRequestHandler):
    """Server finto: script = lista di azioni per le richieste successive ("ok", "500", "400", "sleep", "reasoning"
    = ragionamento in reasoning_content con reasoning_tokens in usage, "reasoning_nousage" = senza reasoning_tokens,
    "reasoning_only" = contenuto vuoto, solo ragionamento, troncato; "echo_seed" = testo che dipende dal seed)."""
    script: list[str] = []
    requests: list[dict] = []
    models_payload: dict | None = None  # risposta di GET /api/v1/models; None -> 404 (endpoint non disponibile)

    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path != "/api/v1/models" or FakeLMStudio.models_payload is None:
            self.send_response(404)
            self.end_headers()
            return
        data = json.dumps(FakeLMStudio.models_payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])).decode("utf-8"))
        FakeLMStudio.requests.append({"path": self.path, "body": body, "headers": dict(self.headers)})
        action = FakeLMStudio.script.pop(0) if FakeLMStudio.script else "ok"
        if action == "sleep":
            time.sleep(1.0)
        if action in ("500", "400"):
            self.send_response(int(action))
            self.end_headers()
            self.wfile.write(b'{"error": "fake"}')
            return
        message, finish = {"role": "assistant", "content": MINI_TXT}, "stop"
        usage = {"prompt_tokens": 11, "completion_tokens": 22, "total_tokens": 33}
        if action == "echo_seed":
            message["content"] = f"Cat number {body.get('seed')}"
        if action.startswith("reasoning"):
            message["reasoning_content"] = REASONING_TXT
            if action == "reasoning":
                usage["completion_tokens_details"] = {"reasoning_tokens": 5}
            if action == "reasoning_only":
                message["content"], finish = "", "length"
        out = {"model": body["model"], "choices": [{"index": 0, "finish_reason": finish, "message": message}],
               "usage": usage}
        data = json.dumps(out).encode("utf-8")
        try:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass


def check_lmstudio_client() -> str:
    srv = ThreadingHTTPServer(("127.0.0.1", 0), FakeLMStudio)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/v1"
    msgs = [{"role": "user", "content": "ciao"}]
    try:
        cli = LMStudioClient("fake-model", base_url=base, timeout_s=5, retries=2, backoff_s=0.01)
        P = GenerationParams(top_k=40, seed=1)
        FakeLMStudio.requests.clear()
        r = cli.generate(msgs, GenerationParams(temperature=0.2, top_p=0.9, top_k=20, max_tokens=100, seed=7))
        req = FakeLMStudio.requests[-1]
        assert req["path"] == "/v1/chat/completions"
        assert req["body"] == {"model": "fake-model", "messages": msgs, "temperature": 0.2, "top_p": 0.9, "top_k": 20,
                               "max_tokens": 100, "seed": 7, "stream": False}, req["body"]
        assert not any(h.lower() == "authorization" for h in req["headers"]), "chiave API inviata"
        assert (r.text, r.finish_reason, r.prompt_tokens, r.completion_tokens, r.model) == \
            (MINI_TXT, "stop", 11, 22, "fake-model")
        assert r.request_params == {"temperature": 0.2, "top_p": 0.9, "top_k": 20, "max_tokens": 100, "seed": 7}
        assert r.params_not_sent == [] and r.reasoning_field is None and r.reasoning_tokens is None
        n = len(FakeLMStudio.requests)
        for missing in (GenerationParams(top_k=40, seed=None), GenerationParams(seed=1)):  # mai al default del modello
            try:
                cli.generate(msgs, missing)
                raise AssertionError("parametro None non rifiutato")
            except ValueError as e:
                assert "esplicito" in str(e)
        assert len(FakeLMStudio.requests) == n, "richiesta inviata con un parametro mancante"
        partial = LMStudioClient("fake-model", base_url=base, timeout_s=5, retries=0, unsupported_params=["top_k"])
        r = partial.generate(msgs, GenerationParams(seed=1))  # top_k dichiarato non supportato: non inviato
        assert "top_k" not in FakeLMStudio.requests[-1]["body"] and r.params_not_sent == ["top_k"]
        try:
            LMStudioClient("fake-model", unsupported_params=["min_p"])
            raise AssertionError("parametro sconosciuto accettato")
        except ValueError:
            pass
        cli.generate(msgs, P)
        assert "response_format" not in FakeLMStudio.requests[-1]["body"]

        FakeLMStudio.script = ["reasoning"]  # ragionamento in un campo separato, token dal server
        r = cli.generate(msgs, P)
        assert (r.text, r.reasoning_text, r.reasoning_field) == (MINI_TXT, REASONING_TXT, "reasoning_content")
        assert (r.reasoning_tokens, r.reasoning_tokens_source) == (5, "server")
        FakeLMStudio.script = ["reasoning_nousage"]  # senza reasoning_tokens: stima
        r = cli.generate(msgs, P)
        assert (r.reasoning_tokens, r.reasoning_tokens_source) == (token_estimate.count_tokens(REASONING_TXT),
                                                                   "stima_cl100k")
        FakeLMStudio.script = ["reasoning_only"]  # JSON valido SOLO nel ragionamento: mai usato per l'estrazione
        r = cli.generate(msgs, P)
        v = pp.validate_response(r.text, r.finish_reason)
        assert r.text == "" and r.reasoning_text == REASONING_TXT and (v.level, v.failure) == (-1, "truncated")
        cli.generate(msgs, GenerationParams(top_k=40, seed=1, structured_output=True))
        rf = FakeLMStudio.requests[-1]["body"]["response_format"]
        assert rf["type"] == "json_schema" and rf["json_schema"]["strict"] is True
        assert rf["json_schema"]["schema"]["properties"]["version"]["pattern"] == "^4\\.\\d+\\.\\d+$"

        FakeLMStudio.script = ["500", "500"]  # retry: due errori 5xx, poi risposta
        r = cli.generate(msgs, P)
        assert cli.attempts == 3 and r.text == MINI_TXT
        FakeLMStudio.script = ["500", "500", "500"]  # retry esauriti
        try:
            cli.generate(msgs, P)
            raise AssertionError("errore 5xx persistente non segnalato")
        except RuntimeError as e:
            assert "3 tentativi" in str(e) and cli.attempts == 3
        FakeLMStudio.script = ["400"]  # errore del client: nessun retry
        try:
            cli.generate(msgs, P)
            raise AssertionError("400 non segnalato")
        except RuntimeError as e:
            assert "HTTP 400" in str(e) and cli.attempts == 1
        slow = LMStudioClient("fake-model", base_url=base, timeout_s=0.2, retries=1, backoff_s=0.01)
        FakeLMStudio.script = ["sleep", "sleep"]  # timeout su entrambi i tentativi
        try:
            slow.generate(msgs, P)
            raise AssertionError("timeout non segnalato")
        except RuntimeError as e:
            assert slow.attempts == 2, slow.attempts
        FakeLMStudio.script = ["sleep"]  # timeout, poi risposta al secondo tentativo
        r = slow.generate(msgs, P)
        assert slow.attempts == 2 and r.text == MINI_TXT
    finally:
        FakeLMStudio.script = []
        srv.shutdown()
        srv.server_close()
    print("  OK  LMStudioClient su server finto: richiesta ben formata (senza chiave API; temperature, top_p, top_k, "
          "max_tokens, seed sempre espliciti; non supportati registrati; response_format solo se attivato), "
          "ragionamento in campo separato salvato e mai estratto, retry su 5xx, nessun retry su 4xx, timeout")
    return base


# --- post-processing ------------------------------------------------------------------------------------------------


def check_extraction() -> None:
    v = pp.validate_response(MINI_TXT, "stop")
    assert v.level == 4 and v.extraction == "raw" and not v.format_issues and not v.layout_issues
    assert len(v.style_raw) == 2, v.style_raw  # metodo senza "+ " e "1..n": ammessi dal v4, segnalati da style_check
    assert v.l4_rewrites == {"method_v4_form": 1, "multiplicity_n": 1}
    row = v.row()
    assert row["l4_rewrites_total"] == 2 and row["style_raw_count"] == 2 and len(json.loads(row["style_raw"])) == 2
    cases = {
        "fence": ("Here it is:\n```json\n" + MINI_TXT + "\n```\nHope it helps.", "stop", 4, "fence"),
        "testo extra": ("Sure! " + MINI_TXT + " Done.", "stop", 4, "braces"),
        "think": ("<think>I need classes {Alpha} and {\"x\": 1}</think>\n" + MINI_TXT, "stop", 4, "raw"),
        "think senza apertura": ("reasoning {draft}\n</think>\n\n" + MINI_TXT, "stop", 4, "raw"),
        "thinking maiuscolo": ("<THINKING>{\"a\": 1}</THINKING>```\n" + MINI_TXT + "\n```", "stop", 4, "fence"),
        "gemma4": ("<|channel>thought\nClasses {Alpha}, draft {\"x\": 1}<channel|>" + MINI_TXT, "stop", 4, "raw"),
        "gemma4 senza apertura": ("draft {\"x\": 1}\n<channel|>\n" + MINI_TXT, "stop", 4, "raw"),
        "gemma4 + fence": ("<|channel>thought {a}<channel|>Here:\n```json\n" + MINI_TXT + "\n```", "stop", 4,
                           "fence"),
    }
    for name, (text, fr, level, how) in cases.items():
        v = pp.validate_response(text, fr)
        assert v.level == level and v.extraction == how, (name, v.level, v.extraction, v.errors)
    assert pp.validate_response(cases["think"][0]).reasoning_removed
    assert set(pp.validate_response(cases["fence"][0]).format_issues) == {"extra_text"}

    trunc = MINI_TXT[:len(MINI_TXT) // 2]
    v = pp.validate_response(trunc, "length")
    assert (v.level, v.failure, v.truncated) == (-1, "truncated", True)
    v = pp.validate_response(trunc, "stop")
    assert (v.level, v.failure, v.truncated) == (-1, "incomplete_json", False)
    v = pp.validate_response("<think>let me think about {the classes", "length")
    assert (v.failure, v.reasoning_removed) == ("truncated", True)
    v = pp.validate_response("<|channel>thought\nlet me draft " + MINI_TXT, "length")  # Gemma 4 troncato nel pensiero
    assert (v.level, v.failure, v.reasoning_removed) == (-1, "truncated", True)
    v = pp.validate_response("<|channel>thought\nlet me draft " + MINI_TXT, "stop")  # pensiero mai chiuso
    assert (v.level, v.failure, v.reasoning_removed) == (-1, "no_json", True)
    assert pp.reasoning_markers(cases["gemma4"][0]) == ["gemma4_channel_thought"]
    assert pp.reasoning_markers(cases["think senza apertura"][0]) == ["think"]
    assert pp.reasoning_markers(MINI_TXT) == []
    v = pp.validate_response('{"version": "4.2.0", "nodes": [1, 2,], }', "stop")
    assert (v.level, v.failure) == (0, "invalid_json")
    v = pp.validate_response("I cannot draw this diagram.", "stop")
    assert (v.level, v.failure) == (-1, "no_json")
    v = pp.validate_response('```json\n{"a": [1, 2\n```', "length")
    assert (v.level, v.failure) == (0, "truncated")
    print("  OK  estrazione: risposta pulita, fence, testo extra, blocchi di ragionamento <think> e Gemma 4 "
          "<|channel>thought (anche senza apertura o troncati), troncamento (finish_reason=length) distinto da JSON incompleto o non valido")


def check_levels() -> None:
    def mutate(f):
        d = json.loads(MINI_TXT)
        f(d)
        return pp.validate_response(json.dumps(d), "stop")

    v = mutate(lambda d: d.update(interactive={"elements": {}, "relationships": {}}))
    assert v.level == 4 and set(v.format_issues) == {"interactive_present"} and not v.layout_issues  # non e' errore
    v = mutate(lambda d: d.update(extra=1))
    assert (v.level, v.failure) == (1, "schema")
    v = mutate(lambda d: d["nodes"][0]["data"]["attributes"][0].update(id="n2"))  # id globale duplicato
    assert (v.level, v.failure) == (2, "integrity") and "id duplicati" in v.errors["L3"][0]
    v = mutate(lambda d: d["edges"][0].update(target="nX"))
    assert (v.level, v.failure) == (2, "integrity")
    v = mutate(lambda d: d["nodes"][0]["data"].update(attributes=[{"name": "+ x : int"}]))  # membro senza id
    assert (v.level, v.failure) == (2, "integrity") and "malformata" in v.errors["L3"][0]
    v = mutate(lambda d: [n.update(id=f"id-{i}") for i, n in enumerate(d["nodes"])] and
               d["edges"][0].update(source="id-0", target="id-1"))  # id non UUID: ammessi
    assert v.level == 4
    v = mutate(lambda d: d["nodes"][0]["data"]["attributes"][0].update(name="+ code : String"))
    assert (v.level, v.failure) == (3, "style")
    v = mutate(lambda d: d["edges"][0]["data"].update(targetMultiplicity="N"))
    assert (v.level, v.failure) == (3, "style")
    v = mutate(lambda d: d["nodes"][1].update(position={"x": 100, "y": 100}))
    assert v.level == 4 and set(v.layout_issues) == {"overlapping_nodes"} and not v.format_issues
    v = mutate(lambda d: d["nodes"][1].update(position={"x": 1500, "y": 40}))
    assert v.level == 4 and set(v.layout_issues) == {"out_of_canvas"}
    # elenco CHIUSO delle riscritture L4: solo "1..n", "0..n", "n" e i metodi nella forma v4
    for mult, rewritten in (("0..n", True), ("n", True), ("N", False), ("1..N", False), ("2..n", False),
                            ("1..*", False)):
        v = mutate(lambda d: d["edges"][0]["data"].update(targetMultiplicity=mult))
        assert (v.l4_rewrites.get("multiplicity_n") == 1) == rewritten, (mult, v.l4_rewrites)
        assert v.L4_style == (rewritten or mult == "1..*"), (mult, v.errors)
    v = mutate(lambda d: d["nodes"][0]["data"]["methods"][0].update(name="+ describe(): string"))
    assert "method_v4_form" not in v.l4_rewrites and v.level == 4
    v = mutate(lambda d: d["nodes"][0]["data"]["methods"][0].update(name="describe"))  # senza parentesi: non ammesso
    assert "method_v4_form" not in v.l4_rewrites and v.failure == "style"
    norm, _ = pp.v4_normalized_copy(json.loads(MINI_TXT))
    assert norm["nodes"][0]["data"]["methods"][0]["name"] == "+ describe() : string"
    assert set(pp.L4_REWRITES) == {"method_v4_form", "multiplicity_n"}
    print("  OK  livelli L0-L4 separati; id unici senza formato UUID; elenco chiuso delle riscritture L4 con "
          "conteggio; diagnostici di formato e di layout separati, fuori dai livelli")


# --- runner ---------------------------------------------------------------------------------------------------------


def check_tokenizer_offline(tmp: Path) -> None:
    """Stima dei token con la rete DISATTIVATA (connessioni socket rifiutate) e la cache di tiktoken vuota: il
    vocabolario si carica da generation/tokenizer/ senza download. Sha256 alterato -> errore."""
    def no_network(*a, **k):
        raise OSError("rete disattivata dal test")

    saved = (socket.socket.connect, socket.create_connection, os.environ.get("TIKTOKEN_CACHE_DIR"))
    empty_cache = tmp / "tiktoken_cache"
    empty_cache.mkdir()
    socket.socket.connect, socket.create_connection = no_network, no_network
    os.environ["TIKTOKEN_CACHE_DIR"] = str(empty_cache)
    try:
        try:
            socket.create_connection(("openaipublic.blob.core.windows.net", 443))
            raise AssertionError("rete non disattivata")
        except OSError:
            pass
        token_estimate.encoding.cache_clear()
        enc = token_estimate.encoding()
        assert enc.encode("hello world") == [15339, 1917]  # id cl100k_base noti
        assert token_estimate.count_tokens("hello world") == 2
        instructions = (HERE / "templates" / "v4_instructions.txt").read_text(encoding="utf-8")
        assert rx.token_counter()(instructions) == 1708, "conteggio delle istruzioni v4 diverso da quello riportato"
        assert token_estimate.count_tokens("<|endoftext|>") > 1  # testo normale, nessun errore
        assert not any(empty_cache.iterdir()), "tiktoken ha scritto nella cache (download?)"
    finally:
        socket.socket.connect, socket.create_connection = saved[0], saved[1]
        if saved[2] is None:
            os.environ.pop("TIKTOKEN_CACHE_DIR", None)
        else:
            os.environ["TIKTOKEN_CACHE_DIR"] = saved[2]
    bad = tmp / "cl100k_crlf.tiktoken"
    bad.write_bytes(token_estimate.VOCAB_PATH.read_bytes().replace(b"\n", b"\r\n"))  # come dopo un checkout CRLF
    try:
        token_estimate.load_ranks(bad)
        raise AssertionError("vocabolario alterato non rifiutato")
    except ValueError as e:
        assert "sha256" in str(e)
    print("  OK  stima dei token senza rete e con cache tiktoken vuota (vocabolario versionato, sha256 verificato; "
          "istruzioni v4 = 1708 token come riportato); vocabolario alterato rifiutato")


def check_smoke(tmp: Path) -> None:
    """experiments/smoke_lmstudio.py sul server finto: risposte vuote o troncate -> "non valutabile" (mai si'/no),
    ragionamento -> avviso; seed rispettato -> "si"."""
    from llm_client import GenerationResult

    def fake(text, finish="stop"):
        return GenerationResult(text=text, finish_reason=finish, model="m", params={}, repetition=0, latency_s=0)

    assert sm.seed_verdict([fake("a"), fake("a"), fake("b")]) == "si"
    assert sm.seed_verdict([fake("a"), fake("b"), fake("c")]) == "no"
    assert sm.seed_verdict([fake("a"), fake("a"), fake("a")]).startswith("non determinabile")
    for bad in ([fake(""), fake(""), fake("")], [fake("a"), fake("a"), fake("b", "length")],
                [fake("<|channel>thought ..."), fake("<|channel>thought ..."), fake("b")]):
        assert sm.seed_verdict(bad) == sm.NOT_EVALUABLE

    srv = ThreadingHTTPServer(("127.0.0.1", 0), FakeLMStudio)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    argv = sys.argv
    try:
        sys.argv = ["smoke", "--model", "fake", "--base-url", f"http://127.0.0.1:{srv.server_address[1]}/v1"]
        outputs = {}
        for scenario, action in (("ragionamento", "reasoning_only"), ("seed", "echo_seed")):
            FakeLMStudio.script = [action] * 7  # 1 chiamata {"ok": true} + 2 x 3 chiamate del seed
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                sm.main()
            outputs[scenario] = buf.getvalue()
    finally:
        sys.argv = argv
        FakeLMStudio.script = []
        srv.shutdown()
        srv.server_close()
    out = outputs["ragionamento"]  # come nel primo smoke test con Gemma 4: contenuto vuoto, ragionamento, length
    verdicts = [line for line in out.splitlines() if line.startswith("seed rispettato:")]
    assert len(verdicts) == 2 and all(line.split("   [")[0] == f"seed rispettato: {sm.NOT_EVALUABLE}"
                                      for line in verdicts), verdicts
    assert sm.REASONING_WARNING in out and "finish_reason=length" in out and "token di completamento=22" in out
    assert "'max_tokens': 512" in out and "campo di ragionamento separato: reasoning_content" in out
    out = outputs["seed"]
    assert "seed rispettato: si" in out and sm.REASONING_WARNING not in out and "finish_reason=stop" in out

    # --save: file .txt + .json, numerazione progressiva per data e modello, mai sovrascrivere
    srv = ThreadingHTTPServer(("127.0.0.1", 0), FakeLMStudio)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/v1"
    save_dir = tmp / "smoke_tests"
    save_dir.mkdir()
    date = time.strftime("%Y-%m-%d")
    prefix = f"{date}_lab-fake-model_smoke"  # "lab/fake model" -> "lab-fake-model"
    existing = save_dir / f"{prefix}1.txt"
    existing.write_text("prova esistente", encoding="utf-8")
    (save_dir / f"{prefix}4.json").write_text("{}", encoding="utf-8")  # solo il .json: il numero 4 e' occupato
    (save_dir / f"{date}_altro-modello_smoke9.txt").write_text("x", encoding="utf-8")  # altro modello: non conta
    args = ["--model", "lab/fake model", "--base-url", base, "--save", "--save-dir", str(save_dir)]
    try:
        for action in ("reasoning_only", "echo_seed"):
            FakeLMStudio.script = [action] * 7
            with contextlib.redirect_stdout(io.StringIO()):
                assert sm.main(args) == 0
    finally:
        FakeLMStudio.script = []
        srv.shutdown()
        srv.server_close()
    assert existing.read_text(encoding="utf-8") == "prova esistente"
    names = sorted(x.name for x in save_dir.iterdir() if x.name.startswith(prefix))
    assert names == [f"{prefix}1.txt", f"{prefix}4.json", f"{prefix}5.json", f"{prefix}5.txt", f"{prefix}6.json",
                     f"{prefix}6.txt"], names
    txt = (save_dir / f"{prefix}5.txt").read_text(encoding="utf-8")
    assert f"base_url:          {base}" in txt and "id del modello:    lab/fake model" in txt
    assert f"versione script:   {sm.SCRIPT_VERSION} (sha256 {sm.script_sha256()})" in txt
    assert sm.REASONING_WARNING in txt and f"seed rispettato: {sm.NOT_EVALUABLE}" in txt  # output completo
    j5 = json.loads((save_dir / f"{prefix}5.json").read_text(encoding="utf-8"))
    assert j5["ok_check"]["expected_answer"] is False and j5["reasoning_present"] is True and j5["error"] is None
    assert [c["verdict"] for c in j5["seed_checks"]] == [sm.NOT_EVALUABLE] * 2
    assert [c["temperature"] for c in j5["seed_checks"]] == [0.8, 0.0]
    call = j5["seed_checks"][0]["calls"][0]
    assert (call["seed"], call["finish_reason"], call["completion_tokens"]) == (sm.SEED, "length", 22)
    assert call["reasoning"]["field"] == "reasoning_content" and call["reasoning"]["tokens_source"] == "stima_cl100k"
    assert call["reasoning"]["tokens"] == token_estimate.count_tokens(REASONING_TXT)
    assert call["request_params"]["max_tokens"] == sm.SEED_MAX_TOKENS
    j6 = json.loads((save_dir / f"{prefix}6.json").read_text(encoding="utf-8"))
    assert [c["verdict"] for c in j6["seed_checks"]][0] == "si" and j6["reasoning_present"] is False
    assert j6["seed_checks"][0]["calls"][2]["answer"] == f"Cat number {sm.OTHER_SEED}"

    # server irraggiungibile: la prova si salva comunque, con l'errore
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        rc = sm.main(["--model", "lab/fake model", "--base-url", base, "--save", "--save-dir", str(save_dir)])
    j7 = json.loads((save_dir / f"{prefix}7.json").read_text(encoding="utf-8"))
    assert rc == 1 and j7["error"] and j7["ok_check"] is None and (save_dir / f"{prefix}7.txt").exists()
    print("  OK  smoke test sul server finto: risposte vuote o troncate -> non valutabile (mai si'/no), avviso se "
          "c'e' ragionamento, finish_reason / token / max_tokens stampati, seed rispettato -> si; --save: .txt con "
          "intestazione e output completo + .json strutturato, numerazione progressiva, nessuna sovrascrittura, "
          "prova salvata anche in caso di errore")


def check_corpus_loo(builder: PromptBuilder) -> None:
    """Query dal corpus (pilota): selezione leave-one-out. Per OGNI query del corpus e ogni condizione nessun esempio
    ha lo stesso id della query e nessun id del test set compare; bm25 identico al LOO del Passo 2."""
    import csv
    loo_csv = ROOT / "data" / "results" / "retrieval" / "loo_2026-10-04_stop1" / "loo_top3.csv"
    ref: dict[str, list[dict]] = {}
    for row in csv.DictReader(loo_csv.open(encoding="utf-8")):
        ref.setdefault(row["query"], []).append(row)
    n = 0
    for c in builder.candidates:
        for cond, k in (("zero_shot", 0), ("random", 3), ("bm25", 1), ("bm25", 2), ("bm25", 3), ("oracle", 3)):
            bp = builder.build(c, PromptSpec(cond, k=k))
            assert c["id"] not in bp.example_ids, (c["id"], cond)
            assert not any(e in builder.test_ids or cl.DEBARI_ID_RE.match(e) for e in bp.example_ids)
            n += 1
        hits = builder.bm25_for(c).retrieve(c["description"], 3)  # stesso protocollo di analyze_retrieval.loo
        rows = sorted(ref[c["id"]], key=lambda r: int(r["rank"]))
        assert [h.id for h in hits] == [r["neighbor"] for r in rows], c["id"]
        assert all(abs(h.score_norm - float(r["score_norm"])) < 6e-5 for h, r in zip(hits, rows)), c["id"]
        assert builder.bm25_for(c) is not builder.bm25 and c["id"] not in builder.bm25_for(c).ids
    for q in [dict(x) for x in cl.load_queries()]:  # il test set usa l'indice congelato sui 59 candidati
        assert builder.bm25_for(q) is builder.bm25
    try:
        builder.build(builder.by_id["AirTravel"], PromptSpec("static"))
        raise AssertionError("static con la query AirTravel non rifiutata")
    except ValueError:
        pass
    assert builder.build(builder.by_id["Louvre"], PromptSpec("static")).example_ids == [
        "STATIC_example_1_bank_loans", "AirTravel"]
    print(f"  OK  query dal corpus: {n} prompt senza la query tra i propri esempi e senza id del test set; bm25 LOO "
          "identico a loo_top3.csv del Passo 2 per le 59 query (indice rifittato senza la query); static con "
          "AirTravel rifiutata")


def check_pilot(builder: PromptBuilder, tmp: Path) -> None:
    """Selezione deterministica dei 6 esercizi, config del pilota valida, temperature multiple, stop_on_reasoning."""
    import yaml
    chosen = select_pilot.select(builder)
    assert chosen == select_pilot.select(builder)  # deterministica
    cfg = yaml.safe_load((ROOT / "experiments" / "configs" / "pilot_temperature.yaml").read_text(encoding="utf-8"))
    assert cfg["query_ids"] == [r["id"] for r in chosen]
    assert [(r["band"], r["role"]) for r in chosen] == [(b, role) for b in select_pilot.BANDS
                                                         for role in ("piccolo", "grande")]
    assert "EatAtHome" not in cfg["query_ids"] and not set(cfg["query_ids"]) & builder.test_ids
    assert cfg["split"] == "corpus" and cfg["conditions"] == ["bm25"] and cfg["k"] == [2]
    assert cfg["generation"]["temperature"] == [0.0, 0.3] and cfg["repetitions"] == 3
    assert (cfg["generation"]["top_k"], cfg["generation"]["top_p"], cfg["generation"]["max_tokens"]) == (64, 0.95, 12288)
    assert cfg["model_metadata"]["enable_thinking"] is False and cfg["model_metadata"]["context_length"] == 32768
    assert cfg["stop_on_reasoning"] is True
    # config STORICA del primo pilota (run conclusa, non modificata): prima dei metadati di caricamento del 2026-10-07
    assert rx.missing_metadata(cfg["model_metadata"]) == ["kv_cache_quant", "flash_attention"]
    assert isinstance(rx.make_client({**cfg, "model_metadata": {**cfg["model_metadata"], "kv_cache_quant": "F16",
                                                                "flash_attention": False}}), LMStudioClient)
    planned = rx.plan(cfg, builder.candidates)
    assert len(planned) == 36
    ids = [rx.call_id(q["id"], spec, r, t) for q, spec, r, t in planned]
    assert len(set(ids)) == 36 and "Louvre__bm25__k2__t0__r0" in ids and "Louvre__bm25__k2__t0.3__r2" in ids
    params = {rx.params_for(cfg, r, t) for _, _, r, t in planned}
    assert {(p.temperature, p.seed) for p in params} == {(t, 42 + r) for t in (0.0, 0.3) for r in range(3)}
    assert {(p.top_k, p.top_p, p.max_tokens) for p in params} == {(64, 0.95, 12288)}  # identici tra temperature
    limit = select_pilot.testset_max_gt_tokens()
    assert limit == 3509 and all(r["gt_tokens"] <= limit for r in chosen)  # nessun esercizio fuori scala
    assert not {"HotelBookingManagementSystem", "SmartHomeAutomationSystem"} & set(cfg["query_ids"])
    tmpl = yaml.safe_load((ROOT / "experiments" / "configs" / "gemma4_12b_qat_template.yaml").read_text(encoding="utf-8"))
    assert tmpl["generation"]["max_tokens"] == cfg["generation"]["max_tokens"]  # stesso tetto nel Passo 3b
    assert rx.is_placeholder([0.0, "TODO"]) and rx.is_placeholder([]) and not rx.is_placeholder([0.0, 0.3])

    # run con MockClient sullo split corpus: temperature multiple e arresto quando compare ragionamento
    rdir = tmp / "pilot_mock_responses"
    rdir.mkdir()
    (rdir / "Louvre.txt").write_text(MINI_TXT, encoding="utf-8")
    (rdir / "StudentAppointment.txt").write_text("<|channel>thought\nok<channel|>" + MINI_TXT, encoding="utf-8")
    mock = {"run_id": "pilot_mock", "split": "corpus", "query_ids": ["Louvre", "StudentAppointment"],
            "conditions": ["bm25"], "k": [2], "repetitions": 2, "seed": 0, "stop_on_reasoning": True,
            "client": {"kind": "mock", "responses_dir": str(rdir)},
            "generation": {"temperature": [0.0, 0.3], "top_p": 0.95, "top_k": 64, "max_tokens": 8192, "seed": 42}}
    cfg_path = tmp / "pilot_mock.yaml"
    cfg_path.write_text(yaml.safe_dump(mock), encoding="utf-8")
    res = tmp / "pilot_results"
    try:
        rx.main([str(cfg_path), "--results-dir", str(res)])
        raise AssertionError("ragionamento non fermato")
    except SystemExit as e:
        assert "FERMATA" in str(e) and "StudentAppointment__bm25__k2__t0__r0" in str(e)
    man = [json.loads(x) for x in (res / "pilot_mock" / "manifest.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [m["call_id"] for m in man] == ["Louvre__bm25__k2__t0__r0", "Louvre__bm25__k2__t0__r1",
                                           "Louvre__bm25__k2__t0.3__r0", "Louvre__bm25__k2__t0.3__r1",
                                           "StudentAppointment__bm25__k2__t0__r0"]
    assert [m["temperature"] for m in man] == [0.0, 0.0, 0.3, 0.3, 0.0] and {m["split"] for m in man} == {"corpus"}
    assert all(m["query_id"] not in m["example_ids"] for m in man)
    assert man[-1]["reasoning_markers_in_content"] == ["gemma4_channel_thought"] and man[-1]["level"] == 4
    print("  OK  pilota: selezione deterministica = query_ids del config (2 per fascia, piccolo e grande, senza "
          "EatAtHome ne' esercizi oltre i 3509 token del test set), config valida (36 generazioni, top_k / top_p / max_tokens identici tra temperature), id con "
          "__t<temperatura>, split corpus nel runner, stop_on_reasoning")


def models_payload(model: str, context: int | None, parallel: int = 1, flash_attention: bool | None = None) -> dict:
    """Risposta di GET /api/v1/models come nella documentazione di LM Studio; context None = modello non caricato."""
    conf = {"context_length": context, "parallel": parallel}
    if flash_attention is not None:
        conf["flash_attention"] = flash_attention
    inst = [] if context is None else [{"id": model, "config": conf}]
    return {"models": [{"type": "llm", "key": "altro/modello", "loaded_instances": [], "max_context_length": 4096},
                       {"type": "llm", "key": model, "loaded_instances": inst, "max_context_length": 131072}]}


def check_server_context() -> None:
    """Controllo del contesto del modello CARICATO prima della prima chiamata (GET /api/v1/models)."""
    srv = ThreadingHTTPServer(("127.0.0.1", 0), FakeLMStudio)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/v1"
    cli = LMStudioClient("google/gemma-4-12b-qat", base_url=base)
    cfg = {"model_metadata": {"context_length": 32768}}
    try:
        assert cli.api_root() == f"http://127.0.0.1:{srv.server_address[1]}"
        FakeLMStudio.models_payload = models_payload(cli.model, 32768)
        probe = cli.loaded_context()
        assert probe["available"], f"GET /api/v1/models sul server finto fallito: {probe['error']}"
        info = rx.check_server_context(cli, cfg)
        assert info["verified"] and info["context_lengths"] == [32768] and info["max_context_length"] == 131072
        for ctx, msg in ((8192, "diverso da quello del config"), (None, "non risulta caricato")):
            FakeLMStudio.models_payload = models_payload(cli.model, ctx)  # come nel primo tentativo del pilota
            try:
                rx.check_server_context(cli, cfg)
                raise AssertionError(f"contesto {ctx} non rifiutato")
            except SystemExit as e:
                assert msg in str(e), e
        FakeLMStudio.models_payload = None  # endpoint non disponibile: avviso + conferma
        with contextlib.redirect_stdout(io.StringIO()) as out:
            info = rx.check_server_context(cli, cfg, ask=lambda _: "si")
        assert info["verified"] is False and info["accepted_by"] == "conferma interattiva"
        assert "CONTESTO DEL MODELLO CARICATO NON VERIFICABILE" in out.getvalue()
        for answer in (lambda _: "no", lambda _: (_ for _ in ()).throw(EOFError())):
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    rx.check_server_context(cli, cfg, ask=answer)
                raise AssertionError("conferma mancante non rifiutata")
            except SystemExit:
                pass
        with contextlib.redirect_stdout(io.StringIO()):
            info = rx.check_server_context(cli, cfg, accept_unverified=True)
        assert info["accepted_by"] == "--accept-unverified-context"
        fa_cfg = {"model_metadata": {"context_length": 32768, "flash_attention": True}}
        FakeLMStudio.models_payload = models_payload(cli.model, 32768, flash_attention=True)
        assert rx.check_server_context(cli, fa_cfg)["verified"]
        FakeLMStudio.models_payload = models_payload(cli.model, 32768, flash_attention=False)
        try:
            rx.check_server_context(cli, fa_cfg)
            raise AssertionError("Flash Attention diversa non rifiutata")
        except SystemExit as e:
            assert "Flash Attention" in str(e)
    finally:
        FakeLMStudio.models_payload = None
        srv.shutdown()
        srv.server_close()
    print("  OK  contesto del modello caricato (GET /api/v1/models): coincide -> parte e lo registra; diverso o modello "
          "non caricato -> non parte; endpoint assente -> avviso e conferma (no / EOF -> non parte)")


def check_analyze_pilot() -> None:
    """Funzioni di experiments/analyze_pilot.py su dati sintetici: regola di decisione della voce 75 e confronto
    esplorativo delle relazioni."""
    from types import SimpleNamespace

    def call(t, level, failure="", names=("a",), gt_names=("a",)):
        v = SimpleNamespace(level=level, failure=failure, L1_json=level >= 1)
        gt = {"nodes": [{"data": {"name": n}} for n in gt_names]}
        return {"t": t, "v": v, "names": set(names) if level >= 1 else None, "gt": gt}

    ok = [call(0.0, 4)] * 18 + [call(0.3, 4)] * 18
    assert ap.decision(ok, False)["outcome"].startswith("opzione (a)")
    worse_v = [call(0.0, 2)] * 18 + [call(0.3, 4)] * 18  # V(0) < V(0.3)
    assert ap.decision(worse_v, False)["outcome"].startswith("opzione (b)")
    worse_j = [call(0.0, 4, names=("a", "b"))] * 18 + [call(0.3, 4)] * 18  # J(0) = 0.5 < 1 - 0.05
    assert ap.decision(worse_j, False)["outcome"].startswith("opzione (b)")
    within = [call(0.0, 4, names=("a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o",
                                 "p", "q", "r", "s", "t"), gt_names=("a", "b", "c", "d", "e", "f", "g", "h", "i",
                                                                     "j", "k", "l", "m", "n", "o", "p", "q", "r",
                                                                     "s"))] * 18 + [call(0.3, 4, names=(
        "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s"), gt_names=(
        "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s"))] * 18
    assert ap.decision(within, False)["outcome"].startswith("opzione (a)")  # J(0) = 0.95 = J(0.3) - 0.05
    trunc = [call(0.0, -1, "truncated")] * 2 + [call(0.0, 4)] * 16 + [call(0.3, 4)] * 18
    d = ap.decision(trunc, False)
    assert d["outcome"].startswith("STOP") and "2 risposte troncate" in d["reasons"][0]
    one = [call(0.0, -1, "truncated")] + [call(0.0, 4)] * 17 + [call(0.3, 4)] * 18  # 1 su 18: ammesso
    assert not ap.decision(one, False)["reasons"]
    assert ap.decision(ok, True)["outcome"].startswith("STOP")  # run fermata per ragionamento
    assert ap.decision([call(0.0, 0)] * 18 + [call(0.3, 4)] * 18, False)["outcome"].startswith("STOP")  # J indefinito

    assert [ap.norm_mult(m) for m in ("1..n", "0..*", "n", " 1 ", "", None, "0..1")] == [
        "1..*", "*", "*", "1", "", "", "0..1"]

    def diagram(edges):
        nodes = [{"id": i, "data": {"name": n}} for i, n in (("b", "Building"), ("a", "Apartment"), ("o", "Owner"))]
        return {"nodes": nodes, "edges": [{"id": f"e{k}", "source": s, "target": t, "type": ty,
                                           "data": {"sourceMultiplicity": sm, "targetMultiplicity": tm}}
                                          for k, (s, t, ty, sm, tm) in enumerate(edges)]}

    gt = diagram([("a", "b", "ClassComposition", "1..*", "1"), ("o", "a", "ClassBidirectional", "1", "0..*")])
    resp = diagram([("b", "a", "ClassComposition", "1", "1..n"),  # composizione invertita (la parte e' la sorgente)
                    ("o", "a", "ClassAggregation", "*", "*"),  # aggregazione al posto dell'associazione
                    ("o", "b", "ClassBidirectional", "1", "1")])  # coppia assente nel GT
    c = ap.compare_relations(resp, gt)
    assert (c["resp_edges"], c["gt_edges"], c["same_pair"], c["same_type"]) == (3, 2, 2, 1)
    assert (c["part_whole_same_type"], c["part_whole_same_direction"]) == (1, 0)
    assert c["type ClassBidirectional -> ClassAggregation"] == 1
    assert (c["mult_compared"], c["same_mult"]) == (2, 1)  # composizione: stesse molteplicita' per estremo
    c = ap.compare_relations(gt, gt)
    assert (c["same_pair"], c["same_type"], c["same_direction"], c["same_mult"]) == (2, 2, 1, 2)
    print("  OK  analisi del pilota: regola della voce 75 (a / b / STOP per troncamenti, ragionamento, J non "
          "definito; soglia 0.05 inclusa) e confronto esplorativo delle relazioni (coppia, tipo, verso, "
          "molteplicita')")


PU_OK = """@startuml
class Building {
  + floors : int
}
class Apartment {
  + number : int
}
class Person {}
Building "1" *-- "1..*" Apartment
Apartment "1..*" -- "1..* owner" Person : isOwnedBy
Person "coach" -- "0..*" Person
@enduml"""


def check_plantuml(builder: PromptBuilder) -> None:
    """Strada 1 del secondo pilota: post-processing PlantUML -> Apollon, regola automatica delle etichette, prompt."""
    v = ppu.validate_plantuml_response(PU_OK, "stop", "t")
    assert (v.P0_block, v.P1b_parsed, v.P1_clean, v.level) == (True, True, True, 4), (v.failure, v.errors)
    names = {n["id"]: n["data"]["name"] for n in v.diagram["nodes"]}
    edges = {(e["type"], names[e["source"]], names[e["target"]]): e["data"] for e in v.diagram["edges"]}
    assert edges[("ClassComposition", "Apartment", "Building")]["targetMultiplicity"] == "1"  # Tutto = destinazione
    own = edges[("ClassBidirectional", "Apartment", "Person")]
    assert (own["label"], own["targetMultiplicity"], own["targetRole"]) == ("isOwnedBy", "1..*", "owner")
    selfrel = edges[("ClassBidirectional", "Person", "Person")]
    assert (selfrel["sourceMultiplicity"], selfrel["sourceRole"]) == ("", "coach")  # ruolo senza molteplicita'
    wrapped = "<|channel>thought\nok<channel|>Here:\n```plantuml\n" + PU_OK + "\n```"
    v = ppu.validate_plantuml_response(wrapped, "stop", "t")
    assert v.level == 4 and v.reasoning_removed and "extra_text" in v.format_issues
    dirty = PU_OK.replace("class Person {}", "class Person {}\nskinparam monochrome true\npackage X")
    v = ppu.validate_plantuml_response(dirty, "stop", "t")
    assert (v.P1b_parsed, v.P1_clean, len(v.discarded_lines), v.level) == (True, False, 2, 4)
    v = ppu.validate_plantuml_response(PU_OK.split("@enduml")[0][:120], "length", "t")
    assert (v.P0_block, v.failure) == (False, "truncated")
    assert ppu.validate_plantuml_response("no diagram", "stop", "t").failure == "no_block"
    v = ppu.validate_plantuml_response("@startuml\n<> D\nA -- D\n@enduml", "stop", "t")
    assert (v.P0_block, v.P1b_parsed, v.failure) == (True, False, "unsupported")
    assert ppu.validate_plantuml_response("@startuml\n@enduml", "stop", "t").failure == "no_classes"
    rels = [{"kind": "binary", "source_mult": "0..1*", "source_role": "", "target_mult": "boss", "target_role": "x"}]
    assert ppu.apply_auto_label_rule(rels) == 1 and rels[0]["target_role"] == "boss x" and rels[0]["source_mult"] == "0..1*"
    q = builder.by_id["ApartmentBuilding"]
    a = builder.build(q, PromptSpec("bm25", k=2, output_format="plantuml"))
    z = builder.build(q, PromptSpec("zero_shot", output_format="plantuml"))
    assert a.instructions == z.instructions == (HERE / "templates" / "v4_plantuml_instructions.txt").read_text(
        encoding="utf-8") and a.task == z.task
    assert a.examples_block.count("@startuml") == 2 and '"nodes"' not in a.examples_block
    assert a.text == builder.build(q, PromptSpec("bm25", k=2, output_format="plantuml")).text
    assert a.example_ids == builder.build(q, PromptSpec("bm25", k=2)).example_ids  # stessi esempi del formato JSON
    try:
        PromptSpec("bm25", output_format="xml")
        raise AssertionError("formato sconosciuto accettato")
    except ValueError:
        pass
    import plantuml_sanity_check
    summ = plantuml_sanity_check.run()
    assert all(summ[x]["levels"] == {4: 79} for x in "AB") and summ["B"]["n_diff"] == 0
    assert summ["A"]["kinds"] == {"ruolo del Passo 1 rimasto come nome di associazione (testo dopo i due punti)": 106}
    print("  OK  strada 1 (PlantUML): P0 / P1 / P1b / L2-L4, righe scartate contate, troncamento, diamante "
          "n-ario, regola automatica delle etichette, prompt PlantUML con esempi canonici e stessi esempi del formato "
          "JSON; 79 diagrammi a L4 (canonico identico al Passo 1, diagram_plantuml grezzo: 106 ruoli come etichette)")


def check_pilot2(tmp: Path) -> None:
    """Configurazioni del secondo pilota, schema per la generazione vincolata, calibrazione (server finto)."""
    import yaml
    import calibrate_tokens as ct
    import make_generation_schema as mgs
    cfg = yaml.safe_load((ROOT / "experiments" / "configs" / "pilot2_formats.yaml").read_text(encoding="utf-8"))
    assert sorted(cfg["configurations"]) == ["J-G", "J-Q", "P-G", "P-Q"]
    first = yaml.safe_load((ROOT / "experiments" / "configs" / "pilot_temperature.yaml").read_text(encoding="utf-8"))
    assert cfg["query_ids"] == first["query_ids"]  # stessi 6 esercizi del primo pilota
    total = 0
    for name in cfg["configurations"]:
        r = rx.resolve_configuration(cfg, name)
        assert r["run_id"] == f"pilot2_formats__{name}" and r["configuration"] == name
        fmt = "plantuml" if name.startswith("P") else "apollon"
        assert r["prompt"]["output_format"] == fmt and r["generation"]["structured_output"] == (fmt == "apollon")
        assert ("response_schema" in r["client"]) == (fmt == "apollon")
        assert (r["model_metadata"]["context_length"], r["generation"]["max_tokens"]) == (32768, 12288)
        assert r["model_metadata"]["enable_thinking"] is False
        assert (r["generation"]["temperature"], r["generation"]["top_p"], r["generation"]["top_k"]) == (0.3, 0.95, 64)
        planned = rx.plan(r, cl.load_candidates())
        assert all(spec.output_format == fmt for _, spec, _, _ in planned)
        total += len(planned)
    assert total == 48
    q = rx.resolve_configuration(cfg, "J-Q")["model_metadata"]
    assert (q["quantization"], q["kv_cache_quant"], q["flash_attention"]) == ("Q4_K_M", "Q4", True)
    for name in ("P-G", "P-Q"):  # regola delle etichette non ancora approvata
        try:
            rx.check_label_rule(rx.resolve_configuration(cfg, name))
            raise AssertionError("regola delle etichette non approvata accettata")
        except SystemExit as e:
            assert "non approvata" in str(e)
    for name, missing in (("J-Q", "client.model"), ("J-G", "kv_cache_quant")):  # TODO ancora aperti
        try:
            rx.make_client(rx.resolve_configuration(cfg, name))
            raise AssertionError(f"{name} con metadati TODO accettato")
        except SystemExit as e:
            assert missing in str(e)
    for bad in (None, "X"):
        try:
            rx.resolve_configuration(cfg, bad)
            raise AssertionError("configurazione mancante o sconosciuta accettata")
        except SystemExit:
            pass
    jg = rx.resolve_configuration(cfg, "J-G")
    jg["model_metadata"].update(kv_cache_quant="F16", flash_attention=False)  # valori fittizi solo per il test
    client = rx.make_client(jg)
    body = client.request_body([{"role": "user", "content": "x"}],
                               GenerationParams(top_k=64, seed=1, structured_output=True))
    gen_schema = body["response_format"]["json_schema"]["schema"]
    assert gen_schema == json.loads(mgs.TARGET.read_text(encoding="utf-8"))
    built, info = mgs.build_schema()
    assert built == gen_schema, "schema di generazione non aggiornato: rilancia generation/make_generation_schema.py"
    assert '"$ref"' not in json.dumps(gen_schema) and "definitions" not in gen_schema
    assert gen_schema["properties"]["edges"]["maxItems"] == 3 * info["max_edges_selectable"] == 39
    import jsonschema
    gv = jsonschema.Draft7Validator(gen_schema)
    gts = [c["diagram_apollon_json"] for c in cl.load_candidates()] + [q["diagram_apollon_json"] for q in cl.load_queries()]
    assert all(not list(gv.iter_errors(d)) for d in gts)  # nessun ground truth escluso dal vincolo
    too_many = json.loads(MINI_TXT)
    too_many["edges"] = too_many["edges"] * 40
    assert list(gv.iter_errors(too_many)) and not list(jsonschema.Draft7Validator(json.loads(
        (ROOT / "evaluation" / "uml-model-4.schema.json").read_text(encoding="utf-8"))).iter_errors(too_many))

    # calibrazione sul server finto (prompt_tokens = 11 per ogni chiamata)
    srv = ThreadingHTTPServer(("127.0.0.1", 0), FakeLMStudio)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        jq = rx.resolve_configuration(cfg, "J-Q")
        jq["client"].update(model="fake-qwen", base_url=f"http://127.0.0.1:{srv.server_address[1]}/v1")
        FakeLMStudio.models_payload = models_payload("fake-qwen", 32768, flash_attention=True)
        FakeLMStudio.requests.clear()
        out = ct.calibrate(jq, rx.make_client({**jq, "model_metadata": {**jq["model_metadata"], "model_id": "q"}}))
    finally:
        FakeLMStudio.models_payload = None
        srv.shutdown()
        srv.server_close()
    assert len(out["rows"]) == 12 and all(r["real"] == 11 for r in out["rows"])
    assert all(rq["body"]["max_tokens"] == 1 for rq in FakeLMStudio.requests)  # chiamate brevissime
    assert out["summary"]["apollon"]["fits"] and out["summary"]["plantuml"]["fits"]
    assert out["server_context"]["verified"]
    d = tmp / "calib"
    d.mkdir()
    p1 = ct.next_path(d, "2026-10-07", "fake/qwen")
    p1.write_text("{}", encoding="utf-8")
    assert ct.next_path(d, "2026-10-07", "fake/qwen").name == "2026-10-07_fake-qwen_calibration2.json"
    print("  OK  secondo pilota: 4 configurazioni (48 generazioni, stessi 6 esercizi, parametri identici), run_id "
          "per configurazione, response_format solo per J-*, PlantUML bloccato finche' la regola non e' approvata, "
          "Qwen 14B (Q4_K_M, KV Q4, Flash Attention) e Gemma bloccati dai TODO; schema di generazione con $ref "
          "espansi e maxItems 39 (79 ground truth validi); calibrazione dei token con max_tokens = 1 sul server finto")


def check_runner(tmp: Path, base_url: str) -> None:
    cfg_path = tmp / "cfg.yaml"
    cfg = {"run_id": "t1", "split": "testset", "query_ids": ["DB06_Flights"], "conditions": ["zero_shot", "bm25"],
           "k": [1], "repetitions": 2, "seed": 0, "client": {"kind": "mock", "finish_reasons": {}},
           "generation": {"temperature": 0.0, "top_p": 1.0, "top_k": 40, "max_tokens": 100, "seed": 5}}
    import yaml
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    res = tmp / "results"
    assert rx.main([str(cfg_path), "--results-dir", str(res)]) == 0  # MockClient senza risposte: testo vuoto
    out = res / "t1"
    man = [json.loads(x) for x in (out / "manifest.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(man) == 4 and {m["failure"] for m in man} == {"no_json"}
    assert [m["params"]["seed"] for m in man] == [5, 6, 5, 6]
    assert all(m["prompt_chars"] > 0 and m["prompt_tokens_est"] > 0 for m in man)
    try:
        rx.main([str(cfg_path), "--results-dir", str(res)])
        raise AssertionError("sovrascrittura non rifiutata")
    except SystemExit as e:
        assert "non si sovrascrive" in str(e)
    lines = (out / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
    (out / "manifest.jsonl").write_text("\n".join(lines[:2]) + "\n", encoding="utf-8")  # run interrotta
    assert rx.main([str(cfg_path), "--results-dir", str(res), "--resume"]) == 0
    man = [json.loads(x) for x in (out / "manifest.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(man) == 4 and [m["cached"] for m in man] == [False, False, True, True]

    real = dict(cfg, run_id="t2", client={"kind": "lmstudio", "model": "fake-model", "base_url": base_url,
                                          "retries": 0, "timeout_s": 5})
    cfg_path.write_text(yaml.safe_dump(real), encoding="utf-8")
    try:
        rx.main([str(cfg_path), "--results-dir", str(res)])
        raise AssertionError("client reale senza metadati non rifiutato")
    except SystemExit as e:
        assert "metadati obbligatori" in str(e) and not (res / "t2").exists()
    meta = {"model_id": "m", "quantization": "QAT (q4_0)", "context_length": 32768, "lmstudio_version": "0.0.0",
            "enable_thinking": False, "kv_cache_quant": "Q4", "flash_attention": True,
            "hardware": {"cpu": "c", "gpu": "g", "ram_gb": 1, "vram_gb": 1}}
    assert rx.missing_metadata(dict(meta, flash_attention="si")) == [
        "flash_attention (true/false, come impostato in LM Studio)"]
    assert rx.missing_metadata(dict(meta, kv_cache_quant="TODO")) == ["kv_cache_quant"]
    assert rx.missing_metadata(meta) == []  # enable_thinking = false e' un valore valido
    assert rx.missing_metadata(dict(meta, enable_thinking="TODO")) == ["enable_thinking"]
    assert rx.missing_metadata(dict(meta, enable_thinking="yes")) == [
        "enable_thinking (true/false, come impostato in LM Studio)"]
    no_topk = dict(real, run_id="t2", model_metadata=meta, generation=dict(cfg["generation"], top_k=None))
    cfg_path.write_text(yaml.safe_dump(no_topk), encoding="utf-8")
    try:
        rx.main([str(cfg_path), "--results-dir", str(res)])
        raise AssertionError("top_k mancante non rifiutato")
    except SystemExit as e:
        assert "generation.top_k" in str(e) and not (res / "t2").exists()
    prior = dict(real, run_id="t3", model_metadata=meta)
    (res / "t3").mkdir()
    (res / "t3" / "config.json").write_text(json.dumps({"config": prior}), encoding="utf-8")
    assert rx.inconsistent_runs(dict(prior, run_id="t4"), res) == []  # stessi valori: ammessa
    other_model = dict(prior, run_id="t4", model_metadata=dict(meta, model_id="altro"),
                       generation=dict(prior["generation"], max_tokens=999))
    assert rx.inconsistent_runs(other_model, res) == []  # altro modello: nessun vincolo
    for changed in (dict(prior, run_id="t4", generation=dict(prior["generation"], max_tokens=999)),
                    dict(prior, run_id="t4", model_metadata=dict(meta, context_length=16384))):
        assert rx.inconsistent_runs(changed, res) == ["t3: context_length=32768, max_tokens=100"]
        cfg_path.write_text(yaml.safe_dump(changed), encoding="utf-8")
        try:
            rx.main([str(cfg_path), "--results-dir", str(res)])
            raise AssertionError("contesto / max_tokens diversi per lo stesso modello non rifiutati")
        except SystemExit as e:
            assert "identici" in str(e) and not (res / "t4").exists()

    srv = ThreadingHTTPServer(("127.0.0.1", 0), FakeLMStudio)  # run con client lmstudio sul server finto
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        e2e = dict(prior, run_id="t5", conditions=["zero_shot"], repetitions=1,
                   model_metadata=dict(meta, model_id="m5", enable_thinking=True),
                   client=dict(prior["client"], base_url=f"http://127.0.0.1:{srv.server_address[1]}/v1"))
        cfg_path.write_text(yaml.safe_dump(e2e), encoding="utf-8")
        FakeLMStudio.script = ["reasoning"]
        FakeLMStudio.models_payload = models_payload("fake-model", 16384)  # contesto diverso dal config: non parte
        try:
            rx.main([str(cfg_path), "--results-dir", str(res)])
            raise AssertionError("contesto diverso non rifiutato")
        except SystemExit as e:
            assert "diverso da quello del config" in str(e) and not (res / "t5").exists()
        FakeLMStudio.models_payload = models_payload("fake-model", 32768)
        assert rx.main([str(cfg_path), "--results-dir", str(res)]) == 0
        lines = (res / "t5" / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
        (res / "t5" / "manifest.jsonl").write_text("", encoding="utf-8")  # ripresa: esito in server_checks.jsonl
        FakeLMStudio.script = ["reasoning"]
        assert rx.main([str(cfg_path), "--results-dir", str(res), "--resume"]) == 0
        (res / "t5" / "manifest.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
        checks = [json.loads(x) for x in (res / "t5" / "server_checks.jsonl").read_text(encoding="utf-8").splitlines()]
        assert len(checks) == 1 and checks[0]["verified"] and checks[0]["context_lengths"] == [32768]
    finally:
        FakeLMStudio.script = []
        FakeLMStudio.models_payload = None
        srv.shutdown()
        srv.server_close()
    m = json.loads((res / "t5" / "manifest.jsonl").read_text(encoding="utf-8"))
    assert m["request_params"] == {"temperature": 0.0, "top_p": 1.0, "top_k": 40, "max_tokens": 100, "seed": 5}
    assert (m["reasoning_field"], m["reasoning_tokens"], m["reasoning_tokens_source"]) == ("reasoning_content", 5,
                                                                                           "server")
    assert m["reasoning_chars"] == len(REASONING_TXT) and m["reasoning_markers_in_content"] == []
    assert m["level"] == 4 and m["params_not_sent"] == [] and not m["content_empty"]
    raw = json.loads((res / "t5" / "raw" / "DB06_Flights__zero_shot__k0__r0.json").read_text(encoding="utf-8"))
    assert raw["reasoning_text"] == REASONING_TXT
    assert raw["raw"]["choices"][0]["message"]["reasoning_content"] == REASONING_TXT
    saved = json.loads((res / "t5" / "config.json").read_text(encoding="utf-8"))["config"]["model_metadata"]
    assert saved["enable_thinking"] is True and saved["quantization"] == "QAT (q4_0)"
    sc = json.loads((res / "t5" / "config.json").read_text(encoding="utf-8"))["provenance"]["server_context"]
    assert sc["verified"] and sc["context_lengths"] == [32768] and sc["expected_context_length"] == 32768
    print("  OK  runner: output e manifest (caratteri, token stimati, seed per ripetizione), rifiuto della "
          "sovrascrittura, ripresa dalla cache, client reale rifiutato senza metadati (anche enable_thinking) o "
          "senza top_k o con contesto / max_tokens diversi da un'altra run dello stesso modello; run lmstudio sul "
          "server finto con parametri espliciti e ragionamento separato nel raw e nel manifest")


def main() -> None:
    before = snapshot_corpus()
    candidates, queries = cl.load_all()
    builder = PromptBuilder(candidates, queries)
    tmp = Path(tempfile.mkdtemp(prefix="uml_rag_test_generation_"))
    print("Generazione (Passo 3a):")
    try:
        check_prompts(builder, queries)
        check_cache(tmp)
        base = check_lmstudio_client()
        check_extraction()
        check_levels()
        check_tokenizer_offline(tmp)
        check_corpus_loo(builder)
        check_pilot(builder, tmp)
        check_analyze_pilot()
        check_plantuml(builder)
        check_pilot2(tmp)
        check_smoke(tmp)
        check_server_context()
        check_runner(tmp, base)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    assert snapshot_corpus() == before, "il codice della generazione ha scritto in corpus/"
    print(f"  OK  nessuna scrittura in corpus/ ({len(before)} file, sha256 invariati)")
    print("\nTutti i test della generazione sono passati.")


if __name__ == "__main__":
    main()
