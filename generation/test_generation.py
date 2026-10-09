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
    # post-processing v2 (voce 89): extends / implements, blocco senza @enduml; pilot2_v1 invariata
    java = """@startuml
interface Payable {}
abstract class Person {
  + name : string
}
class Employee extends Person implements Payable, Comparable {
  + salary : double
}
class Manager extends Employee { + level : int }
class Intern extends Person {}
interface Comparable
Person "1" -- "0..*" Employee
@enduml"""
    v1 = ppu.validate_plantuml_response(java, "stop", "t", "pilot2_v1")
    v = ppu.validate_plantuml_response(java, "stop", "t", "v2")
    assert v1.postprocess_version == "pilot2_v1" and len(v1.discarded_lines) >= 4  # intestazioni e corpi scartati
    assert v.level == 4 and not v.discarded_lines, (v.failure, v.errors, v.discarded_lines)
    assert v.syntax_rewrites == {"headers": 3, "extends": 3, "implements": 2}
    names = {n["id"]: n["data"]["name"] for n in v.diagram["nodes"]}
    rels = {(e["type"], names[e["source"]], names[e["target"]]) for e in v.diagram["edges"]}
    assert {("ClassInheritance", "Employee", "Person"), ("ClassInheritance", "Manager", "Employee"),
            ("ClassInheritance", "Intern", "Person"), ("ClassRealization", "Employee", "Payable"),
            ("ClassRealization", "Employee", "Comparable")} <= rels
    attrs = {n["data"]["name"]: [a["name"] for a in n["data"]["attributes"]] for n in v.diagram["nodes"]}
    assert attrs["Employee"] == ["+ salary : double"] and attrs["Manager"] == ["+ level : int"]  # corpo sulla riga
    assert "syntax_rewrites" in v.row() and v.row()["syntax_rewrites"] == "extends=3;headers=3;implements=2"
    no_end = PU_OK.replace("@enduml", "")
    assert ppu.validate_plantuml_response(no_end, "stop", "t", "pilot2_v1").failure == "incomplete_block"
    v = ppu.validate_plantuml_response(no_end, "stop", "t", "v2")
    assert v.level == 4 and "enduml_mancante" in v.format_issues
    assert ppu.validate_plantuml_response(no_end, "length", "t", "v2").failure == "truncated"  # con length: troncata
    assert ppu.validate_plantuml_response(PU_OK, "stop", "t", "pilot2_v1").level == 4
    assert ppu.DEFAULT_VERSION == "v2" and ppu.PILOT2_VERSION == "pilot2_v1"
    try:
        ppu.validate_plantuml_response(PU_OK, "stop", "t", "v3")
        raise AssertionError("versione sconosciuta accettata")
    except ValueError:
        pass
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
          "n-ario, post-processing v2 (extends / implements anche con corpo sulla riga, blocco senza @enduml) con "
          "pilot2_v1 invariata, regola automatica delle etichette, prompt PlantUML con esempi canonici e stessi esempi del formato "
          "JSON; 79 diagrammi a L4 (canonico identico al Passo 1, diagram_plantuml grezzo: 106 ruoli come etichette)")


def check_uml_structure() -> None:
    """Struttura comune, espansore unico e formato JSON compatto (generation/uml_structure.py, voce 90)."""
    import re
    import uml_structure as us
    import compact_sanity_check as cs
    st = us.structure_from_apollon(MINI)
    assert [c.name for c in st.classes] == ["Alpha", "Beta"] and st.relations[0].target_multiplicity == "1..n"
    compact = us.to_compact(st)
    assert compact == {"classes": [{"name": "Alpha", "attributes": ["+ code : string"], "methods": ["describe(): string"]},
                                   {"name": "Beta"}],
                       "relations": [{"type": "association", "source": "Alpha", "target": "Beta",
                                      "sourceMultiplicity": "1", "targetMultiplicity": "1..n"}]}
    d, _ = us.compact_to_apollon(compact, "m")
    assert d["edges"][0]["data"]["targetMultiplicity"] == "1..*"  # stessa normalizzazione del convertitore
    assert d["nodes"][0]["data"]["methods"][0]["name"] == "+ describe() : string"
    assert us.expand(us.from_compact(compact), "m")[0] == d  # deterministico
    with_empty = {"classes": [{"name": "A", "kind": "class", "attributes": [], "methods": []}, {"name": "B"}],
                  "relations": [{"type": "inheritance", "child": "A", "parent": "B", "label": ""}]}
    assert us.to_compact(us.from_compact(with_empty)) == {"classes": [{"name": "A"}, {"name": "B"}], "relations": [
        {"type": "inheritance", "child": "A", "parent": "B"}]}  # chiavi vuote accettate, poi omesse
    # verso per ruolo (STOP 1): tutto / parte e figlia / madre convertiti nel verso di Apollon
    wp = {"classes": [{"name": "Car"}, {"name": "Wheel"}, {"name": "Sedan"}], "relations": [
        {"type": "composition", "whole": "Car", "part": "Wheel", "wholeMultiplicity": "1", "partMultiplicity": "4",
         "partRole": "wheels"}, {"type": "inheritance", "child": "Sedan", "parent": "Car"}]}
    d, _ = us.compact_to_apollon(wp, "m")
    nm = {n["id"]: n["data"]["name"] for n in d["nodes"]}
    comp, inh = d["edges"]
    assert (comp["type"], nm[comp["source"]], nm[comp["target"]]) == ("ClassComposition", "Wheel", "Car")
    assert (comp["data"]["sourceMultiplicity"], comp["data"]["targetMultiplicity"], comp["data"]["sourceRole"]) == (
        "4", "1", "wheels")
    assert (inh["type"], nm[inh["source"]], nm[inh["target"]]) == ("ClassInheritance", "Sedan", "Car")
    assert us.apollon_to_compact(d) == wp  # e ritorno
    tolerant = {"classes": [{"name": "Car", "id": "c1"}, {"name": "Car"}, {"name": "Wheel"}], "version": "4.2.0",
                "relations": [{"type": "composition", "source": "Wheel", "target": "Car"},  # chiavi della famiglia sbagliata
                              {"type": "ClassComposition", "whole": "Car", "part": "Wheel"},  # tipo Apollon
                              {"type": "aggregation", "whole": "Car", "part": "Tyre"},  # classe non dichiarata
                              {"type": "association", "source": "Car", "target": "Wheel", "wholeRole": "x"}]}
    st, issues = us.read_compact(tolerant, strict=False)
    cats = sorted(c for c, _ in issues)
    assert cats == sorted(["chiave di primo livello non prevista (ignorata)", "chiave di classe non prevista (ignorata)",
                           "classe ripetuta (seconda scartata)",
                           "chiavi di verso di un'altra famiglia (relazione scartata)",
                           "tipo di relazione non previsto (relazione scartata)",
                           "relazione verso una classe non dichiarata (scartata)",
                           "chiave di relazione non prevista (ignorata)"]), cats
    assert [c.name for c in st.classes] == ["Car", "Wheel"] and len(st.relations) == 1
    bad = [{"classes": [{"name": "A"}], "version": "4.2.0"},  # metadati non ammessi
           {"classes": [{"name": "A"}, {"name": "A"}]},  # nomi ripetuti
           {"classes": [{"name": "A", "kind": "record"}]},
           {"classes": [{"name": "E", "kind": "enum", "attributes": ["X"]}]},
           {"classes": [{"name": "A", "id": "x"}]},
           {"classes": [{"name": "A"}], "relations": [{"type": "ClassBidirectional", "source": "A", "target": "A"}]}]
    for b in bad:
        try:
            us.from_compact(b)
            raise AssertionError(f"compatto non valido accettato: {b}")
        except us.StructureError:
            pass
    try:  # relazione verso una classe non dichiarata: rifiutata dall'espansore
        us.compact_to_apollon({"classes": [{"name": "A"}], "relations": [
            {"type": "association", "source": "A", "target": "Z"}]}, "m")  # stretto: anche from_compact
        raise AssertionError("relazione verso classe inesistente accettata")
    except us.StructureError:
        pass
    broken = json.loads(MINI_TXT)
    broken["edges"][0]["target"] = "nessuno"
    try:
        us.structure_from_apollon(broken)
        raise AssertionError("Apollon con riferimento rotto accettato")
    except us.StructureError:
        pass
    # PlantUML -> struttura (vincoli di generalizzazione conservati) -> espansore
    st, _ = ppu.plantuml_to_structure("@startuml\nclass A {}\nclass B {}\nclass C {}\nB --|> A : {disjoint}\n"
                                      "C --|> A : {disjoint}\n@enduml", "m")
    assert len(st.constraints) == 2 and [r.type for r in st.relations] == ["ClassInheritance"] * 2
    # esempi della specifica: coincidono con il corpus e arrivano a L4
    doc = (ROOT / "docs" / "compact_format.md").read_text(encoding="utf-8")
    blocks = [json.loads(b) for b in re.findall(r"```json\n(.*?)```", doc, re.S)]
    truck = builder_free_record("TruckLogistics")
    assert blocks[0] == us.apollon_to_compact(truck)
    for b in blocks:
        v = pp.check_l2_l4(pp.Validation(L0_extracted=True, L1_json=True, level=1), us.compact_to_apollon(b, "doc")[0])
        assert v.level == 4, (v.failure, v.errors)
    s = cs.run()  # 79 diagrammi: identici salvo gli id dei metodi (firma grezza del Passo 1)
    for k in "ab":
        assert s[f"{k}_identical"] == 57 and s[f"{k}_method_ids_only"] == 22 and not s[f"{k}_other"]
        assert s[f"{k}_method_ids"] == 148
    assert sorted(s["tokens_compact"])[len(s["tokens_compact"]) // 2] == 338 and max(s["tokens_compact"]) == 960
    print("  OK  struttura comune ed espansore unico: Apollon <-> struttura <-> JSON compatto, chiavi vuote omesse, "
          "compatto non valido rifiutato, vincoli da PlantUML conservati, esempi della specifica a L4; 79 diagrammi "
          "identici al Passo 1 nei percorsi PlantUML e compatto (57) o salvo gli id dei metodi (22, 148 id)")


def check_compact(builder: PromptBuilder, tmp: Path) -> None:
    """Strada JSON compatto (voce 91): prompt, post-processing C0-C2 + L2-L4, schema disattivato, ramo del runner."""
    import jsonschema
    import compact_postprocess as cpp
    import uml_structure as us
    q = builder.by_id["ApartmentBuilding"]
    a = builder.build(q, PromptSpec("bm25", k=2, output_format="compact"))
    z = builder.build(q, PromptSpec("zero_shot", output_format="compact"))
    assert a.instructions == z.instructions == (HERE / "templates" / "v4_compact_instructions.txt").read_text(
        encoding="utf-8") and a.task == z.task
    assert '"nodes"' not in a.examples_block and a.examples_block.count("— JSON:") == 2
    assert a.example_ids == builder.build(q, PromptSpec("bm25", k=2)).example_ids  # stessi esempi degli altri formati
    for eid in a.example_ids:  # ogni esempio e' il compatto del Passo 1, su una riga
        line = json.dumps(us.apollon_to_compact(builder.by_id[eid]["diagram_apollon_json"]), ensure_ascii=False,
                          separators=(",", ":"))
        assert line in a.examples_block
    assert a.text == builder.build(q, PromptSpec("bm25", k=2, output_format="compact")).text
    v4 = (HERE / "templates" / "v4_instructions.txt").read_text(encoding="utf-8").splitlines()
    comp = a.instructions.splitlines()
    for keep in range(61, 68):  # molteplicita' e linee guida di modellazione: identiche alla v4 (salvo i nomi)
        line = v4[keep - 1].replace("ClassComposition or ClassAggregation", "composition or aggregation")
        line = line.replace("separate edge", "separate relation").replace('"sourceRole"/"targetRole"', "the role keys")
        line = line.replace("class node", "class").replace("separate edges", "separate relations")
        line = line.replace("its own edge", "its own relation")
        assert line in comp, (keep, line)

    gt = builder.by_id["ApartmentBuilding"]["diagram_apollon_json"]
    good = json.dumps(us.apollon_to_compact(gt))
    v = cpp.validate_compact_response(good, "stop", "t")
    assert (v.C0_found, v.C1_valid_json, v.C2b_converted, v.C2_clean, v.level) == (True, True, True, True, 4)
    assert not v.format_issues and not v.normalizations and v.diagram["nodes"][0]["data"]["name"] == gt["nodes"][0]["data"]["name"]
    v = cpp.validate_compact_response("<think>x</think>Here:\n```json\n" + good + "\n```", "stop", "t")
    assert v.level == 4 and v.reasoning_removed and v.format_issues == {"extra_text": True}
    assert cpp.validate_compact_response(good[:-5], "length", "t").failure == "truncated"
    assert cpp.validate_compact_response(good[:-5], "stop", "t").failure == "incomplete_json"
    assert cpp.validate_compact_response("[1, 2]", "stop", "t").failure in ("not_object", "no_json")
    assert cpp.validate_compact_response('{"nodes": []}', "stop", "t").failure == "not_compact"
    assert cpp.validate_compact_response('{"classes": [], "relations": []}', "stop", "t").failure == "no_classes"
    assert cpp.validate_compact_response("nessun json", "stop", "t").failure == "no_json"
    messy = {"classes": [{"name": "Car", "attributes": ["- plate : String"], "id": "x"}, {"name": "Wheel"}],
             "relations": [{"type": "composition", "whole": "Car", "part": "Wheel", "partMultiplicity": "1..n"},
                           {"type": "composition", "source": "Wheel", "target": "Car"},
                           {"type": "association", "source": "Car", "target": "Driver"}]}
    v = cpp.validate_compact_response(json.dumps(messy), "stop", "t")
    assert (v.C2b_converted, v.C2_clean, v.level) == (True, False, 4), (v.failure, v.errors)
    assert sorted(c for c, _ in v.compact_issues) == sorted([
        "chiave di classe non prevista (ignorata)", "chiavi di verso di un'altra famiglia (relazione scartata)",
        "relazione verso una classe non dichiarata (scartata)"])
    assert v.normalizations == {"attributi": 1, "molteplicita'": 1}  # "- plate : String" -> "+ plate : string", 1..n
    assert len(v.diagram["edges"]) == 1 and v.row()["compact_issues_count"] == 3
    # schema per la generazione vincolata: preparato e DISATTIVATO
    sch = json.loads(cpp.SCHEMA_PATH.read_text(encoding="utf-8"))
    assert sch == cpp.generation_schema(), "schema non aggiornato: rilancia python generation/compact_postprocess.py"
    assert '"$ref"' not in json.dumps(sch) and sch["properties"]["relations"]["maxItems"] == 39
    gv = jsonschema.Draft7Validator(sch)
    assert all(not list(gv.iter_errors(us.apollon_to_compact(c["diagram_apollon_json"])))
               for c in builder.candidates + cl.load_queries())
    assert list(gv.iter_errors(messy))  # chiavi non previste rifiutate dallo schema
    for cfg_path in (ROOT / "experiments" / "configs").glob("*.yaml"):  # nessuna config lo usa
        assert "compact_generation.schema" not in cfg_path.read_text(encoding="utf-8"), cfg_path
    # ramo del runner (MockClient senza risposte: testo vuoto -> no_json)
    import yaml
    cfg = {"run_id": "c1", "split": "corpus", "query_ids": ["ApartmentBuilding"], "conditions": ["bm25"], "k": [2],
           "repetitions": 1, "seed": 0, "prompt": {"output_format": "compact"}, "client": {"kind": "mock"},
           "generation": {"temperature": 0.3, "top_p": 0.95, "top_k": 64, "max_tokens": 100, "seed": 42}}
    (tmp / "c.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
    with contextlib.redirect_stdout(io.StringIO()):
        assert rx.main([str(tmp / "c.yaml"), "--results-dir", str(tmp / "cres")]) == 0
    m = json.loads((tmp / "cres" / "c1" / "manifest.jsonl").read_text(encoding="utf-8"))
    assert m["output_format"] == "compact" and m["failure"] == "no_json"
    assert "compact_issues_count" in (tmp / "cres" / "c1" / "validation.csv").read_text(encoding="utf-8")
    prov = json.loads((tmp / "cres" / "c1" / "config.json").read_text(encoding="utf-8"))["provenance"]
    assert prov["compact_format_spec"] == "docs/compact_format.md"
    print("  OK  strada JSON compatto: istruzioni con la sola parte sul formato riscritta, esempi compatti (stessi "
          "esempi degli altri formati), C0 / C1 / C2b / C2 + L2-L4, scarti per categoria e normalizzazioni contati a "
          "parte, troncamento, schema di generazione preparato e disattivato (79 GT validi), ramo del runner")


def check_dev(builder: PromptBuilder) -> None:
    """Insieme di sviluppo (voce 92): selezione deterministica, config dev_formats, calibrazione con --formats."""
    import yaml
    import calibrate_tokens as ct
    import select_dev as sd
    import select_pilot as sp
    chosen, counts, q = sd.select(builder)
    assert [r["id"] for r in chosen] == [r["id"] for r in sd.select(builder)[0]]  # deterministica
    assert counts == {"basso": 13, "medio": 14, "alto": 11} and q == {"basso": 7, "medio": 7, "alto": 6}
    ids = [r["id"] for r in chosen]
    assert len(set(ids)) == 20 and not set(ids) & set(sd.PILOT_IDS) and not set(ids) & builder.test_ids
    assert "EatAtHome" not in ids and all(r["gt_tokens"] <= sp.testset_max_gt_tokens() for r in chosen)
    assert sd.quotas({"basso": 1, "medio": 1, "alto": 1}, 2) == {"basso": 1, "medio": 1, "alto": 0}  # parita' di resto
    assert [r["id"] for r in sd.spread([{"id": c, "size": s} for c, s in zip("abcde", (5, 1, 3, 2, 4))], 2)] == ["d", "e"]
    cfg = yaml.safe_load((ROOT / "experiments" / "configs" / "dev_formats.yaml").read_text(encoding="utf-8"))
    assert cfg["query_ids"] == ids and cfg["split"] == "corpus" and cfg["repetitions"] == 2
    pilot2 = yaml.safe_load((ROOT / "experiments" / "configs" / "pilot2_formats.yaml").read_text(encoding="utf-8"))
    assert cfg["models"] == pilot2["models"]  # stessi modelli e metadati del secondo pilota
    total = 0
    for name, fmt in (("P-G", "plantuml"), ("P-Q", "plantuml"), ("C-G", "compact"), ("C-Q", "compact")):
        r = rx.resolve_configuration(cfg, name)
        assert r["prompt"]["output_format"] == fmt and r["generation"]["structured_output"] is False
        assert (r["generation"]["temperature"], r["generation"]["top_p"], r["generation"]["top_k"],
                r["generation"]["max_tokens"], r["model_metadata"]["context_length"]) == (0.3, 0.95, 64, 12288, 32768)
        rx.check_label_rule(r)
        total += len(rx.plan(r, builder.candidates))
    assert sorted(cfg["configurations"]) == ["C-G", "C-Q", "P-G", "P-Q"] and total == 160
    srv = ThreadingHTTPServer(("127.0.0.1", 0), FakeLMStudio)  # calibrazione del compatto sul server finto
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        cq = rx.resolve_configuration(cfg, "C-Q")
        cq["client"].update(model="fake-qwen", base_url=f"http://127.0.0.1:{srv.server_address[1]}/v1")
        FakeLMStudio.models_payload = models_payload("fake-qwen", 32768, flash_attention=True)
        out = ct.calibrate(cq, rx.make_client(cq), formats=("plantuml", "compact"))
    finally:
        FakeLMStudio.models_payload = None
        srv.shutdown()
        srv.server_close()
    assert len(out["rows"]) == 40 and {r["format"] for r in out["rows"]} == {"plantuml", "compact"}
    assert set(out["summary"]) == {"plantuml", "compact"} and out["summary"]["compact"]["fits"]
    print("  OK  insieme di sviluppo: 20 esercizi (7 / 7 / 6 per fascia, quantili di dimensione, senza piloti, EatAtHome "
          "e test set), config dev_formats (4 configurazioni, 160 generazioni, stessi modelli del secondo pilota), "
          "calibrazione con --formats plantuml compact")


def check_analyze_dev(builder: PromptBuilder, tmp: Path) -> None:
    """experiments/analyze_dev.py su dati finti (voce 92): ordine dei criteri Vc, R, J, V, pareggio pieno -> PlantUML,
    J e R su tutte le risposte, coerenza tra i modelli, controllo preliminare, run finte."""
    from types import SimpleNamespace
    import yaml
    import analyze_dev as ad
    import uml_structure as us
    from plantuml_format import apollon_to_plantuml

    def M(Vc=20, R=0.5, J=0.5, V=30):
        return {"Vc": Vc, "R": R, "J": J, "V": V}

    def dec(p, c, per_model=False):
        return ad.decide({"plantuml": p, "compact": c}, per_model)

    d = dec(M(Vc=20), M(Vc=24))
    assert (d["winner"], d["decided_by"]) == ("compact", "Vc") and len(d["steps"]) == 1
    assert dec(M(Vc=24), M(Vc=20))["winner"] == "plantuml"
    d = dec(M(Vc=20, R=0.50), M(Vc=23, R=0.53))  # Vc entro la soglia (3 < 4): decide R, soglia 0,03 inclusa
    assert (d["winner"], d["decided_by"]) == ("compact", "R")
    d = dec(M(R=0.80, J=0.60), M(R=0.83, J=0.50))  # 0,83 - 0,80 in virgola mobile: soglia inclusa
    assert d["decided_by"] == "R" and d["winner"] == "compact"
    d = dec(M(R=0.50, J=0.60), M(R=0.52, J=0.50))  # R entro la soglia: decide J
    assert (d["winner"], d["decided_by"]) == ("plantuml", "J")
    d = dec(M(V=30), M(V=34, R=0.51, J=0.52, Vc=22))  # Vc, R, J entro le soglie: decide V
    assert (d["winner"], d["decided_by"]) == ("compact", "V") and [s["criterion"] for s in d["steps"]] == [
        "Vc", "R", "J", "V"]
    d = dec(M(), M(Vc=23, R=0.52, J=0.52, V=33))  # pareggio pieno: PlantUML anche se il compatto e' di poco meglio
    assert (d["winner"], d["decided_by"]) == ("plantuml", "pareggio pieno")
    assert dec(M(Vc=10), M(Vc=12), per_model=True)["decided_by"] == "Vc"  # per modello la soglia e' 2
    assert dec(M(Vc=10), M(Vc=12))["decided_by"] != "Vc"
    assert dec(M(R=None), M(R=0.1))["decided_by"] == "R"  # R non definito vale 0

    gts = [builder.by_id[q]["diagram_apollon_json"] for q in ("TruckLogistics", "Boeing")]

    def call(fmt, model, valid=True, clean=True, truncated=False, gt=gts[0], q="TruckLogistics", r=0):
        v = SimpleNamespace(level=4 if valid else -1, P1_clean=clean, C2_clean=clean, truncated=truncated,
                            diagram=gt if valid else None, L0_extracted=valid, failure="" if valid else "no_json",
                            normalizations={}, compact_issues=[], discarded_lines=[])
        return {"v": v, "gt": gt, "format": fmt, "model": model, "q": q, "r": r, "m": {"latency_s": 1.0}}

    m = ad.metrics([call("compact", "G", gt=gts[0]), call("compact", "G", valid=False, gt=gts[1])])
    assert (m["V"], m["Vc"], m["J"], m["J_valid"]) == (1, 1, 0.5, 1.0)  # J: 0 per la non valida
    e0, e1 = len(gts[0]["edges"]), len(gts[1]["edges"])
    assert abs(m["R"] - e0 / (e0 + e1)) < 1e-12 and m["R_valid"] == 1.0  # R: le relazioni del GT della non valida contano
    assert ad.metrics([call("plantuml", "G", clean=False)])["Vc"] == 0  # valida con scarti: non conta in Vc

    def infos(calls_by_conf, excluded=None):
        return {n: {"name": n, "calls": calls_by_conf.get(n, []), "excluded": (excluded or {}).get(n),
                    "level_mismatch": 0, "cfg": None} for n in ad.CONFIGURATIONS}

    def conf(fmt, model, n_valid, n=4, **kw):
        return [call(fmt, model, valid=i < n_valid, r=i, **kw) for i in range(n)]

    agree = {"P-G": conf("plantuml", "G", 4), "C-G": conf("compact", "G", 0),
             "P-Q": conf("plantuml", "Q", 4), "C-Q": conf("compact", "Q", 1)}
    res = ad.outcome(infos(agree))
    assert res["winner"] == "plantuml" and res["outcome"] == "vince il formato PlantUML"
    assert {d["winner"] for d in res["per_model"].values()} == {"plantuml"}
    split = {"P-G": conf("plantuml", "G", 4), "C-G": conf("compact", "G", 0),
             "P-Q": conf("plantuml", "Q", 0), "C-Q": conf("compact", "Q", 4)}
    res = ad.outcome(infos(split))
    assert res["winner"] is None and res["outcome"].startswith("STOP: dipende dal modello")
    res = ad.outcome(infos(agree, excluded={"C-Q": "incompleta (39/40 risposte)"}))
    assert res["winner"] is None and res["outcome"].startswith("STOP") and "C-Q" in res["excluded"]
    trunc = dict(agree, **{"C-G": conf("compact", "G", 0, truncated=True)})
    res = ad.outcome(infos(trunc))
    assert res["winner"] == "plantuml" and res["warnings"] and "C-G: 4 risposte troncate" in res["warnings"][0]
    text, _ = ad.report(infos(split))
    assert "**Esito: STOP: dipende dal modello" in text and "Gemma 4 12B QAT (40 risposte" in text

    # run finte: PlantUML canonico e compatto del GT; il compatto di Qwen rotto in 6 risposte su 40
    cfg = yaml.safe_load(ad.CONFIG.read_text(encoding="utf-8"))
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    res_dir = tmp / "dev"

    def fake_run(name, broken=0, n=None):
        r = rx.resolve_configuration(cfg, name)
        out = res_dir / r["run_id"]
        (out / "raw").mkdir(parents=True)
        (out / "config.json").write_text(json.dumps({"config": r, "provenance": {
            "plantuml_postprocess_version": "v2"}}), encoding="utf-8")
        lines, k = [], 0
        for q in r["query_ids"]:
            for rep in range(r["repetitions"]):
                cid = f"{q}__bm25__k2__r{rep}"
                fmt = r["prompt"]["output_format"]
                text = (apollon_to_plantuml(gt[q]) if fmt == "plantuml"
                        else json.dumps(us.apollon_to_compact(gt[q]), separators=(",", ":")))
                if k < broken:
                    text = text[: len(text) // 2]
                k += 1
                v = ad.validate(fmt, text, "stop", cid, "v2")
                (out / "raw" / f"{cid}.json").write_text(json.dumps({"text": text, "finish_reason": "stop"}),
                                                         encoding="utf-8")
                lines.append(json.dumps({"call_id": cid, "query_id": q, "repetition": rep, "level": v.level,
                                         "latency_s": 2.0, "prompt_tokens_server": 3000,
                                         "completion_tokens_server": 300, "reasoning_field": None,
                                         "reasoning_markers_in_content": []}))
        (out / "manifest.jsonl").write_text("\n".join(lines[:n]) + "\n", encoding="utf-8")

    fake_run("P-G")
    fake_run("C-G")
    fake_run("P-Q")
    fake_run("C-Q", broken=6)
    models = ad.expected_model_ids()
    loaded = {n: ad.load_configuration(res_dir, n, gt, models[n]) for n in ad.CONFIGURATIONS}
    assert all(i["excluded"] is None and len(i["calls"]) == 40 and i["level_mismatch"] == 0 for i in loaded.values())
    band_of = {q: "basso" for q in cfg["query_ids"]}
    text, res = ad.report(loaded, band_of)
    pooled = {s["criterion"]: s for s in res["pooled"]["steps"]}
    assert (pooled["Vc"]["plantuml"], pooled["Vc"]["compact"]) == (80, 74)  # 6 compatti rotti
    assert (res["pooled"]["winner"], res["pooled"]["decided_by"]) == ("plantuml", "Vc")
    assert res["per_model"]["G"]["decided_by"] == "pareggio pieno"  # Gemma: tutto identico -> PlantUML
    assert (res["per_model"]["Q"]["winner"], res["per_model"]["Q"]["decided_by"]) == ("plantuml", "Vc")
    assert res["winner"] == "plantuml" and "| P-G | 40/40 | 40/40 | 1.000 | 1.000 |" in text
    assert "| C-Q | 34/40 | 34/40 |" in text and "Confronto appaiato" in text and "Per fascia" in text
    other = ad.load_configuration(res_dir, "C-Q", gt, expected_model_id="altro/modello")
    assert "traccia NON usata" in other["excluded"]
    import shutil as _sh
    _sh.rmtree(res_dir / "dev_formats__C-Q")
    fake_run("C-Q", n=39)  # incompleta: STOP
    loaded["C-Q"] = ad.load_configuration(res_dir, "C-Q", gt, models["C-Q"])
    assert loaded["C-Q"]["excluded"].startswith("incompleta (39/40")
    assert ad.outcome(loaded)["outcome"].startswith("STOP: nessuna decisione")
    assert (ad.MAX_TRUNCATED, ad.TIE_WINNER, [c[0] for c in ad.CRITERIA]) == (2, "plantuml", ["Vc", "R", "J", "V"])
    assert [(c[2], c[3]) for c in ad.CRITERIA] == [(4, 2), (0.03, 0.03), (0.03, 0.03), (4, 2)]  # soglie (voce 92)
    print("  OK  analisi dell'insieme di sviluppo: criteri Vc / R / J / V con soglie incluse (anche per modello), "
          "pareggio pieno -> PlantUML, J e R su tutte le risposte (0 per le non valide), dipende dal modello, "
          "configurazione incompleta, troncamenti segnalati, run finte (160 risposte), run di un altro modello scartata")


def check_k(builder: PromptBuilder, tmp: Path) -> None:
    """Versione di configurazione (voce 93) e leva k sull'insieme di sviluppo (voce 94): config dev_k, calibrazione con
    il k piu' alto, regola di scelta di k di experiments/analyze_k.py su dati finti."""
    from types import SimpleNamespace
    import yaml
    import analyze_k as ak
    import calibrate_tokens as ct
    import uml_structure as us
    from plantuml_format import apollon_to_plantuml
    from token_estimate import count_tokens

    # versione di configurazione: confronto solo tra run dello stesso modello E della stessa versione
    meta = {"model_id": "m", "quantization": "q", "context_length": 32768}
    res = tmp / "versions"
    (res / "old").mkdir(parents=True)
    old = {"run_id": "old", "client": {"kind": "lmstudio"}, "model_metadata": meta,
           "generation": {"max_tokens": 12288}}  # run esistente senza chiave = versione 1
    (res / "old" / "config.json").write_text(json.dumps({"config": old}), encoding="utf-8")
    v2 = {"run_id": "new", "config_version": 2, "client": {"kind": "lmstudio"}, "model_metadata": meta,
          "generation": {"max_tokens": 4096}}
    assert rx.config_version(old) == 1 and rx.config_version(v2) == 2
    assert rx.inconsistent_runs(v2, res) == []  # versione diversa: ammessa
    assert rx.inconsistent_runs(dict(v2, config_version=1), res) == ["old: context_length=32768, max_tokens=12288"]
    (res / "new2").mkdir()
    (res / "new2" / "config.json").write_text(json.dumps({"config": dict(v2, run_id="new2")}), encoding="utf-8")
    assert rx.inconsistent_runs(v2, res) == []  # stessa versione, stessi valori: ammessa
    bad = dict(v2, generation={"max_tokens": 2048})  # stessa versione, valori diversi: rifiutata
    assert rx.inconsistent_runs(bad, res) == ["new2: context_length=32768, max_tokens=4096"]

    cfg = yaml.safe_load((ROOT / "experiments" / "configs" / "dev_k.yaml").read_text(encoding="utf-8"))
    dev = yaml.safe_load((ROOT / "experiments" / "configs" / "dev_formats.yaml").read_text(encoding="utf-8"))
    assert cfg["query_ids"] == dev["query_ids"] and cfg["models"] == dev["models"] and cfg["k"] == [2, 3, 5, 8]
    assert cfg["config_version"] == 2 and cfg["repetitions"] == 2 and cfg["conditions"] == ["bm25"]
    total = 0
    for name in ("P-G", "C-G", "P-Q", "C-Q"):
        r = rx.resolve_configuration(cfg, name)
        assert (r["generation"]["max_tokens"], r["model_metadata"]["context_length"], rx.config_version(r)) == (
            4096, 32768, 2)
        assert (r["generation"]["temperature"], r["generation"]["top_p"], r["generation"]["top_k"]) == (0.3, 0.95, 64)
        total += len(rx.plan(r, builder.candidates))
        real = ROOT / "data" / "results" / "generation"  # le run esistenti (versione 1) non bloccano le nuove
        assert rx.inconsistent_runs(r, real) == []
    assert total == 640
    # calibrazione con il k piu' alto (8) sul server finto
    srv = ThreadingHTTPServer(("127.0.0.1", 0), FakeLMStudio)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        cq = rx.resolve_configuration(cfg, "C-Q")
        cq["client"].update(model="fake-qwen", base_url=f"http://127.0.0.1:{srv.server_address[1]}/v1")
        FakeLMStudio.models_payload = models_payload("fake-qwen", 32768, flash_attention=True)
        out = ct.calibrate(cq, rx.make_client(cq), formats=("compact",))
    finally:
        FakeLMStudio.models_payload = None
        srv.shutdown()
        srv.server_close()
    first = builder.build(builder.by_id[cfg["query_ids"][0]], PromptSpec("bm25", k=8, output_format="compact"))
    assert out["k"] == 8 and out["config_version"] == 2 and out["rows"][0]["est"] == count_tokens(first.text)
    assert out["max_tokens"] == 4096 and out["summary"]["compact"]["fits"]

    # regola di scelta di k
    def M(Vc=30, R=0.30):
        return {"Vc": Vc, "R": R}

    assert ak.choose_k({2: M(R=0.30), 3: M(R=0.31), 5: M(R=0.32), 8: M(R=0.33)})["k"] == 2  # 0,30 = 0,33 - 0,03: incluso
    assert ak.choose_k({2: M(R=0.30), 3: M(R=0.32), 5: M(R=0.33), 8: M(R=0.35)})["k"] == 3  # 0,32 = 0,35 - 0,03: incluso
    assert ak.choose_k({2: M(R=0.30), 3: M(R=0.31), 5: M(R=0.33), 8: M(R=0.35)})["k"] == 5  # 0,31 < 0,32: escluso
    assert ak.choose_k({2: M(R=0.30), 3: M(R=0.30), 5: M(R=0.40), 8: M(R=0.41)})["k"] == 5
    d = ak.choose_k({2: M(Vc=30, R=0.30), 3: M(Vc=28, R=0.31), 5: M(Vc=27, R=0.50), 8: M(Vc=20, R=0.60)})
    assert d["admissible"] == [2, 3] and d["excluded"] == [5, 8] and d["k"] == 2  # Vc oltre 2 sotto k=2: escluso
    assert ak.choose_k({2: M(R=None), 3: M(R=None), 5: M(R=0.01), 8: M(R=0.0)})["k"] == 2  # R non definito = 0
    assert ak.choose_k({2: M(Vc=10, R=0.1), 3: M(Vc=12, R=0.5), 5: M(Vc=12, R=0.5), 8: M(Vc=12, R=0.5)})["k"] == 3

    gt = builder.by_id["TruckLogistics"]["diagram_apollon_json"]

    def call(name, k, valid=True, truncated=False, q="TruckLogistics", r=0):
        fmt_, mk = ak.CONFIGURATIONS[name]
        v = SimpleNamespace(level=4 if valid else -1, P1_clean=True, C2_clean=True, truncated=truncated,
                            diagram=gt if valid else None, L0_extracted=valid, failure="" if valid else "no_json",
                            discarded_lines=[], compact_issues=[])
        return {"v": v, "gt": gt, "format": fmt_, "model": mk, "q": q, "r": r, "k": k, "m": {"latency_s": 1.0}}

    def conf(name, valid_by_k, n=4, trunc_k=None):
        return [call(name, k, valid=i < valid_by_k[k], truncated=(k == trunc_k), r=i) for k in ak.K_VALUES
                for i in range(n)]

    def infos(by_name, excluded=None):
        return {n: {"name": n, "format": ak.CONFIGURATIONS[n][0], "model": ak.CONFIGURATIONS[n][1],
                    "calls": by_name.get(n, []), "excluded": (excluded or {}).get(n), "level_mismatch": 0}
                for n in ak.CONFIGURATIONS}

    full = {2: 4, 3: 4, 5: 4, 8: 4}
    same = {"P-G": conf("P-G", full), "P-Q": conf("P-Q", full), "C-G": conf("C-G", full), "C-Q": conf("C-Q", full)}
    out = ak.outcome(infos(same))
    assert out["formats"]["plantuml"]["k"] == 2 and out["formats"]["compact"]["k"] == 2  # tutto pari: il piu' piccolo
    diff = dict(same, **{"C-Q": conf("C-Q", {2: 1, 3: 1, 5: 4, 8: 4})})  # Qwen: R migliore con k = 5 (Vc in salita)
    out = ak.outcome(infos(diff))
    assert out["per_model"][("compact", "Q")]["k"] == 5 and out["formats"]["compact"]["outcome"].startswith(
        "STOP: dipende dal modello") and out["formats"]["plantuml"]["k"] == 2
    out = ak.outcome(infos(same, excluded={"P-Q": "incompleta (150/160 risposte)"}))
    assert out["formats"]["plantuml"]["k"] is None and "non decidibile" in out["formats"]["plantuml"]["outcome"]
    assert out["formats"]["compact"]["k"] == 2  # l'altro formato si decide comunque
    out = ak.outcome(infos(dict(same, **{"P-G": conf("P-G", full, n=4, trunc_k=8)})))
    assert out["formats"]["plantuml"]["k"] == 2 and out["warnings"] == [  # 4 > 2: segnalato, non blocca
        "P-G, k=8: 4 risposte troncate su 40 (soglia di segnalazione: piu' di 2)"]
    many = dict(same, **{"P-G": conf("P-G", full, n=40, trunc_k=8)})
    out = ak.outcome(infos(many))
    assert any("P-G, k=8: 40 risposte troncate" in w for w in out["warnings"])

    # run finte (3 esercizi, 4 k, 2 ripetizioni = 24 risposte per configurazione)
    ids = cfg["query_ids"][:3]
    gts = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    rd = tmp / "kres"

    def fake_run(name, broken_k=None, n=None):
        r = dict(rx.resolve_configuration(cfg, name), query_ids=ids)
        out_dir = rd / r["run_id"]
        (out_dir / "raw").mkdir(parents=True)
        (out_dir / "config.json").write_text(json.dumps({"config": r, "provenance": {
            "plantuml_postprocess_version": "v2"}}), encoding="utf-8")
        lines = []
        for q in ids:
            for k in r["k"]:
                for rep in range(r["repetitions"]):
                    cid = f"{q}__bm25__k{k}__r{rep}"
                    fmt_ = r["prompt"]["output_format"]
                    text = (apollon_to_plantuml(gts[q]) if fmt_ == "plantuml"
                            else json.dumps(us.apollon_to_compact(gts[q]), separators=(",", ":")))
                    if k == broken_k:
                        text = text[: len(text) // 2]
                    v = ak.ad.validate(fmt_, text, "stop", cid, "v2")
                    (out_dir / "raw" / f"{cid}.json").write_text(json.dumps({"text": text, "finish_reason": "stop"}),
                                                                 encoding="utf-8")
                    lines.append(json.dumps({"call_id": cid, "query_id": q, "repetition": rep, "k": k,
                                             "level": v.level, "latency_s": 1.0 + k, "prompt_tokens_server": 1000 * k,
                                             "completion_tokens_server": 300, "reasoning_field": None,
                                             "reasoning_markers_in_content": []}))
        (out_dir / "manifest.jsonl").write_text("\n".join(lines[:n]) + "\n", encoding="utf-8")

    for name in ("P-G", "C-G", "P-Q"):
        fake_run(name)
    fake_run("C-Q", broken_k=2)  # Qwen compatto: k = 2 tutto rotto -> R(2) = 0, sceglie il piu' piccolo tra 3, 5, 8
    models = ak.expected_model_ids()
    loaded = {n: ak.load_configuration(rd, n, gts, models[n]) for n in ak.CONFIGURATIONS}
    assert all(i["excluded"] is None and len(i["calls"]) == 24 and i["level_mismatch"] == 0 for i in loaded.values())
    text, out = ak.report(loaded, {q: "basso" for q in ids})
    assert out["formats"]["plantuml"]["k"] == 2
    assert out["per_model"][("compact", "Q")]["k"] == 3 and out["per_model"][("compact", "G")]["k"] == 2
    assert "dipende dal modello" in out["formats"]["compact"]["outcome"]
    assert "**PlantUML: k = 2**" in text and "| 3 | si | 6/6 |" in text and "Andamento per fascia" in text
    import shutil as _sh
    _sh.rmtree(rd / "dev_k__P-Q")
    fake_run("P-Q", n=20)
    loaded["P-Q"] = ak.load_configuration(rd, "P-Q", gts, models["P-Q"])
    assert loaded["P-Q"]["excluded"].startswith("incompleta (20/24")
    assert ak.outcome(loaded)["formats"]["plantuml"]["k"] is None
    assert (ak.K_VALUES, ak.BASELINE_K, ak.VC_TOLERANCE, ak.R_TOLERANCE) == ((2, 3, 5, 8), 2, 2, 0.03)  # voce 94
    print("  OK  versione di configurazione (stessa versione con valori diversi rifiutata, versione diversa ammessa, "
          "run vecchie = versione 1); config dev_k (640 generazioni, versione 2, 32768 / 4096); calibrazione con k = 8; "
          "regola di k (ammissibili per Vc, R entro 0,03 incluso, il piu' piccolo, dipende dal modello, formato non "
          "decidibile, troncamenti segnalati); run finte")


def check_instructions(builder: PromptBuilder, tmp: Path) -> None:
    """Leva "istruzioni mirate" (voci 98-100): variante delle istruzioni, blocco congelato, config, regola di adozione e
    metrica M di experiments/analyze_instructions.py, provata anche sulla baseline reale di dev_k a k = 3."""
    import difflib
    import shutil as _sh
    import yaml
    import analyze_instructions as ai
    import prompt_builder as pb
    import uml_structure as us
    from plantuml_format import apollon_to_plantuml

    # blocco congelato (sha256 dei file, LF, voce 98) e variante delle istruzioni
    tpl = HERE / "templates"
    assert hashlib.sha256((tpl / "targeted_rules_block.txt").read_bytes()).hexdigest() == \
        "211d70938f1ee7a162c41ca0221a69adb86f1cc32ef2ca3117eab9326fcc8b91"
    assert hashlib.sha256((tpl / "targeted_rules_direction.yaml").read_bytes()).hexdigest() == \
        "5b4f93fca515efefe9f99207bc86b6ad8db69f51b4b1c3c2b603807551bd108a"
    block = {f: pb.targeted_block(f) for f in ("plantuml", "compact")}
    assert "common superclass" not in block["plantuml"] and len(block["plantuml"].splitlines()) == 11
    names = {n["data"]["name"].lower() for c in builder.candidates + cl.load_queries()
             for n in c["diagram_apollon_json"]["nodes"]}
    texts = " ".join((c["description"] or "").lower() for c in builder.candidates + cl.load_queries())
    assert not {"guitar", "instrument"} & names and " guitar" not in texts and " instrument" not in texts
    for fmt in ("plantuml", "compact"):
        for q in ("Boeing", "eHome2020"):
            base = builder.build(builder.by_id[q], PromptSpec("bm25", k=3, output_format=fmt))
            assert base.text == builder.build(builder.by_id[q], PromptSpec("bm25", k=3, output_format=fmt,
                                                                            instructions_variant="base")).text
            tr = builder.build(builder.by_id[q], PromptSpec("bm25", k=3, output_format=fmt,
                                                            instructions_variant="targeted"))
            d = list(difflib.ndiff(base.text.splitlines(), tr.text.splitlines()))
            assert not [x for x in d if x.startswith("- ")]  # nessuna riga tolta o cambiata
            assert [x[2:] for x in d if x.startswith("+ ") and x[2:]] == block[fmt].splitlines()
            assert tr.example_ids == base.example_ids and tr.task == base.task
            assert tr.instructions.rstrip("\n").endswith(base.instructions.rstrip("\n").rpartition("\n\n")[2])
    for bad in (("apollon", "targeted"), ("plantuml", "altro")):
        try:
            PromptSpec("bm25", output_format=bad[0], instructions_variant=bad[1])
            raise AssertionError(f"variante non ammessa accettata: {bad}")
        except ValueError:
            pass
    try:
        pb.targeted_instructions("istruzioni senza paragrafo finale", "plantuml")
        raise AssertionError("istruzioni senza l'ultimo paragrafo accettate")
    except ValueError:
        pass
    # config: uguale alla baseline dev_k salvo la variante delle istruzioni e k = [3]
    cfg = yaml.safe_load((ROOT / "experiments" / "configs" / "dev_instructions.yaml").read_text(encoding="utf-8"))
    dk = yaml.safe_load((ROOT / "experiments" / "configs" / "dev_k.yaml").read_text(encoding="utf-8"))
    assert cfg["k"] == [3] and cfg["prompt"]["instructions_variant"] == "targeted" and sorted(cfg["configurations"]) == [
        "C-G", "P-G"]
    total = 0
    for name in ("P-G", "C-G"):
        r, b = rx.resolve_configuration(cfg, name), rx.resolve_configuration(dk, name)
        for key in ("query_ids", "repetitions", "seed", "generation", "model_metadata", "client", "config_version"):
            assert r[key] == b[key], key
        plan = rx.plan(r, builder.candidates)
        assert all(spec.instructions_variant == "targeted" and spec.k == 3 for _, spec, _, _ in plan)
        total += len(plan)
    assert total == 80

    # regola di adozione (soglie incluse in virgola mobile)
    def M(M1=0.30, R=0.30, Vc=30):
        return {"M1": M1, "R": R, "Vc": Vc}

    assert ai.adopt(M(), M(M1=0.35))["adopt"]  # dM 0,05 (incluso)
    assert not ai.adopt(M(), M(M1=0.349))["adopt"]  # dM sotto la soglia, R uguale
    assert ai.adopt(M(R=0.30), M(R=0.33))["adopt"]  # dR 0,03 (incluso)
    assert not ai.adopt(M(), M(M1=0.50, R=0.269))["adopt"]  # M migliora ma R peggiora di oltre 0,03
    assert ai.adopt(M(), M(M1=0.50, R=0.27))["adopt"]  # R peggiora esattamente di 0,03: ammesso
    assert not ai.adopt(M(), M(M1=0.50, Vc=27))["adopt"]  # Vc peggiora di 3
    assert ai.adopt(M(), M(M1=0.50, Vc=28))["adopt"]  # Vc peggiora di 2: ammesso
    assert ai.adopt(M(M1=None), M(M1=0.05))["adopt"]  # M non definito = 0

    # metrica M: estremi espliciti (primaria) e tutti (secondaria); risposta non valida = 0
    def diag(edges):
        nodes = [{"id": i, "data": {"name": n}} for i, n in (("a", "A"), ("b", "B"), ("c", "C"))]
        return {"nodes": nodes, "edges": [{"id": f"e{j}", "source": s, "target": t, "type": ty,
                                           "data": {"sourceMultiplicity": sm, "targetMultiplicity": tm}}
                                          for j, (s, t, ty, sm, tm) in enumerate(edges)]}

    gt = diag([("a", "b", "ClassBidirectional", "1", "0..*"), ("b", "c", "ClassBidirectional", "", "1"),
               ("c", "a", "ClassInheritance", "", ""), ("a", "a", "ClassBidirectional", "0..1", "*")])
    resp = diag([("b", "a", "ClassBidirectional", "n", "1"),  # stessa coppia, estremi giusti per classe (n = *)
                 ("b", "c", "ClassComposition", "1", "1"),  # tipo diverso: molteplicita' confrontate lo stesso
                 ("a", "a", "ClassBidirectional", "0..1", "1")])

    def call(d, valid=True):
        from types import SimpleNamespace
        return {"v": SimpleNamespace(level=4 if valid else -1, diagram=d if valid else None), "gt": gt}

    mc = ai.multiplicity_counts(call(resp))
    assert (mc["explicit"], mc["explicit_same"], mc["all"], mc["all_same"]) == (5, 4, 6, 4)
    assert ai.multiplicity_counts(call(resp, valid=False))["explicit_same"] == 0
    assert ai.multiplicity_counts(call(resp, valid=False))["explicit"] == 5

    # sulla baseline REALE (dev_k, Gemma, k = 3, GT attuale)
    real = ROOT / "data" / "results" / "generation"
    gts = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    base = {f: ai.load_run(real, "dev_k", n, gts, "google/gemma-4-12b-qat", 3) for n, f in ai.CONFIGURATIONS.items()}
    mb = {f: ai.metrics(b["calls"]) for f, b in base.items()}
    assert all(b["excluded"] is None and len(b["calls"]) == 40 and b["level_mismatch"] == 0 for b in base.values())
    assert (mb["plantuml"]["mult_counts"]["explicit_same"], mb["plantuml"]["mult_counts"]["explicit"]) == (137, 486)
    assert (mb["compact"]["mult_counts"]["explicit_same"], mb["compact"]["Vc"]) == (104, 34)
    # trattamenti finti costruiti dalle risposte reali: identico alla baseline (non adottato) e risposte = GT (adottato)
    res = tmp / "instr"

    def fake_treatment(name, perfect=False, n=None):
        src = real / f"dev_k__{name}"
        out = res / f"dev_instructions__{name}"
        (out / "raw").mkdir(parents=True)
        c = json.loads((src / "config.json").read_text(encoding="utf-8"))
        c["config"].update(run_id=f"dev_instructions__{name}", k=[3])
        (out / "config.json").write_text(json.dumps(c), encoding="utf-8")
        lines = []
        for line in (src / "manifest.jsonl").read_text(encoding="utf-8").splitlines():
            m = json.loads(line)
            if m["k"] != 3:
                continue
            raw = json.loads((src / "raw" / f"{m['call_id']}.json").read_text(encoding="utf-8"))
            if perfect:
                g = gts[m["query_id"]]
                raw["text"] = apollon_to_plantuml(g) if name == "P-G" else json.dumps(us.apollon_to_compact(g))
                raw["finish_reason"] = "stop"
                m["level"] = 4
            (out / "raw" / f"{m['call_id']}.json").write_text(json.dumps(raw), encoding="utf-8")
            lines.append(json.dumps(m))
        (out / "manifest.jsonl").write_text("\n".join(lines[:n]) + "\n", encoding="utf-8")

    for name in ("P-G", "C-G"):
        _sh.copytree(real / f"dev_k__{name}", res / f"dev_k__{name}")
        fake_treatment(name)
    text, out = ai.report(ai.load_pairs(res))
    assert all(not d["adopt"] and abs(d["dM1"]) < 1e-12 and d["dVc"] == 0 for d in out["formats"].values())
    assert "| PlantUML | baseline | 40/40 | 40/40 |" in text and "Tabelle di confusione" in text
    _sh.rmtree(res / "dev_instructions__C-G")
    fake_treatment("C-G", perfect=True)
    out = ai.outcome(ai.load_pairs(res))
    assert out["formats"]["compact"]["adopt"] and not out["formats"]["plantuml"]["adopt"]
    assert out["note"] and "JSON compatto" in out["note"]  # esito diverso tra i formati: segnalato
    _sh.rmtree(res / "dev_instructions__P-G")
    fake_treatment("P-G", n=30)  # trattamento incompleto: formato non decidibile
    out = ai.outcome(ai.load_pairs(res))
    assert out["formats"]["plantuml"]["adopt"] is None and "non decidibile" in out["formats"]["plantuml"]["outcome"]
    with contextlib.redirect_stdout(io.StringIO()):
        assert ai.main(["--results-dir", str(res)]) == 0
    assert (ai.ADOPT_M, ai.ADOPT_R, ai.MAX_R_LOSS, ai.MAX_VC_LOSS) == (0.05, 0.03, 0.03, 2)  # voce 98
    print("  OK  istruzioni mirate: blocco congelato (sha256), variante base = prompt invariati, variante mirata = solo il "
          "blocco in piu', config uguale alla baseline salvo le istruzioni (80 generazioni); regola di adozione con "
          "soglie incluse, metrica M (esplicita / tutti gli estremi, 0 per le non valide); sulla baseline reale (M "
          "137/486 e 104/486): trattamento identico non adottato, migliore adottato, esiti diversi segnalati, incompleto")


def check_review(builder: PromptBuilder, tmp: Path) -> None:
    """experiments/review_report.py: classificazione delle relazioni coerente con compare_relations, classi colorate,
    pagina autonoma (rendering verificato solo se java e plantuml.jar sono disponibili)."""
    import shutil as _sh
    from types import SimpleNamespace
    import review_report as rr

    gt = builder.by_id["TruckLogistics"]["diagram_apollon_json"]
    st = us_structure_from(gt)
    # risposta: GT con una composizione invertita, una relazione tolta e una classe in piu'
    resp = json.loads(json.dumps(gt))
    comp = next(e for e in resp["edges"] if e["type"] == "ClassComposition")
    comp["source"], comp["target"] = comp["target"], comp["source"]
    resp["edges"] = [e for e in resp["edges"] if e is comp or e["type"] != "ClassBidirectional"]
    resp["nodes"].append({"id": "x", "type": "class", "position": {"x": 0, "y": 0}, "width": 1, "height": 1,
                          "measured": {"width": 1, "height": 1}, "data": {"name": "Depot", "attributes": [],
                                                                          "methods": []}})
    cats = [c for c, _ in rr.classify_relations(resp, gt)]
    rc = ap.compare_relations(resp, gt)
    assert cats.count("direzione invertita") == 1 and cats.count("mancante") == rc["gt_edges"] - rc["same_pair"] == 1
    assert sum(cats.count(x) for x in ("corretta", "direzione invertita", "molteplicita' diverse")) == rc["same_type"]
    assert [c for c, _ in rr.classify_relations(None, gt)] == ["mancante"] * len(gt["edges"])
    text = rr.colored_plantuml(resp, "t", ap.class_names(gt))
    assert "!pragma layout smetana" in text and f"class Depot {rr.ORANGE}" in text and f"class Vehicle {rr.GREEN}" in text
    assert len(st.classes) == len(gt["nodes"])
    assert rr.parse_filters(["k=3", "rep=0", "q=Boeing"]) == {"k": {"3"}, "rep": {"0"}, "q": {"Boeing"}}
    try:
        rr.parse_filters(["x=1"])
        raise AssertionError("filtro non valido accettato")
    except SystemExit:
        pass
    c_ok = {"v": SimpleNamespace(level=4, diagram=resp, truncated=False, failure="", P1_clean=True, C2_clean=True),
            "gt": gt, "q": "TruckLogistics", "r": 0, "format": "compact", "cond": "finta k=3", "version": "",
            "m": {"call_id": "TruckLogistics__bm25__k3__r0"}, "raw": {"text": "{}"}}
    c_bad = dict(c_ok, v=SimpleNamespace(level=-1, diagram=None, truncated=False, failure="no_json", P1_clean=False,
                                         C2_clean=False), r=1, raw={"text": "risposta <non valida>"})
    m_ok, m_bad = rr.response_metrics(c_ok), rr.response_metrics(c_bad)
    assert m_ok["V"] == m_ok["Vc"] == 1 and m_bad == {"V": 0, "Vc": 0, "J": 0.0, "R": 0.0, "M": 0.0}
    if rr.DEFAULT_JAR.exists() and _sh.which("java"):
        page, stats = rr.build([c_ok, c_bad], rr.DEFAULT_JAR, "prova")
        assert stats["svgs"] == stats["diagrams"] == 2 and not stats["errors"]  # GT + risposta valida
        assert page.count("data:image/svg+xml;base64,") == 2 and "&lt;non valida&gt;" in page
        assert "<script" not in page and 'src="http' not in page
        rendered = "rendering verificato"
    else:
        rendered = "rendering NON verificato (java o plantuml.jar assenti)"
    print(f"  OK  report di revisione: classificazione delle relazioni coerente con compare_relations, classi colorate "
          f"(GT / in piu'), filtri, metriche per risposta (0 per le non valide); {rendered}")


def check_run_log(tmp: Path) -> None:
    """experiments/run_log.py (voce 102): due righe per esecuzione, status per ogni modo di uscita, sha256 dei config,
    output dichiarato, registro che non cambia mai l'esito; uno script vero lanciato da riga di comando."""
    import subprocess
    import run_log as rl
    log = tmp / "run_log.jsonl"
    old_env = os.environ.get("RUN_LOG_PATH")
    os.environ["RUN_LOG_PATH"] = str(log)
    try:
        cfg = ROOT / "experiments" / "configs" / "dev_k.yaml"
        argv = ["experiments/x.py", str(cfg), "--resume"]
        with rl.logged("experiments/x.py", argv=argv):
            rl.set_output(ROOT / "data" / "results" / "generation" / "x")
        cases = ((SystemExit(0), "ok"), (SystemExit(2), "exit 2"), (SystemExit("messaggio"), "exit 1"),
                 (KeyboardInterrupt(), "interrupted"), (ValueError("boom"), "error: ValueError"))
        for exc, _ in cases:
            try:
                with rl.logged("experiments/x.py", argv=["experiments/x.py"]):
                    raise exc
            except BaseException as e:  # l'eccezione originale passa sempre
                assert type(e) is type(exc)
        rows = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()]
        assert len(rows) == 2 * (1 + len(cases)) and [r["event"] for r in rows[:2]] == ["start", "end"]
        start, end = rows[0], rows[1]
        assert start["id"] == end["id"] and start["resume"] and start["command"].startswith("python experiments/x.py")
        assert start["config_sha256"]["experiments/configs/dev_k.yaml"] == hashlib.sha256(cfg.read_bytes()).hexdigest()
        assert "retrieval/config_bm25.yaml" in start["config_sha256"]
        assert "generation/templates/targeted_rules_block.txt" in start["config_sha256"]
        assert end["output"] == "data/results/generation/x" and end["status"] == "ok" and end["duration_s"] >= 0
        assert start["commit"] and isinstance(start["worktree_dirty"], bool)
        assert [r["status"] for r in rows[3::2]] == [s for _, s in cases]
        assert rows[7]["message"] == "messaggio" and "boom" in rows[11]["message"]
        rl.set_output("ignorato")  # senza registro attivo: nessun effetto, nessun errore
        os.environ["RUN_LOG_PATH"] = str(tmp)  # percorso non scrivibile (e' una cartella): solo un avviso
        with contextlib.redirect_stderr(io.StringIO()) as err:
            with rl.logged("experiments/x.py", argv=["experiments/x.py"]):
                pass
        assert "registro non scritto" in err.getvalue()
        # uno script vero da riga di comando (dry run del runner, cartella temporanea): due righe con l'uscita
        os.environ["RUN_LOG_PATH"] = str(log)
        n0 = len(log.read_text(encoding="utf-8").splitlines())
        proc = subprocess.run([sys.executable, str(ROOT / "experiments" / "run_experiment.py"),
                               str(ROOT / "experiments" / "configs" / "mock_e2e.yaml"), "--dry-run",
                               "--results-dir", str(tmp / "rl_results")], capture_output=True, text=True, cwd=ROOT,
                              env=dict(os.environ))
        assert proc.returncode == 0, proc.stderr[-500:]
        new = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()[n0:]]
        assert [r["event"] for r in new] == ["start", "end"] and new[1]["status"] == "ok"
        assert new[0]["script"] == "experiments/run_experiment.py" and "dry_run" in new[1]["output"]
        assert "experiments/configs/mock_e2e.yaml" in new[0]["config_sha256"]
    finally:
        if old_env is None:
            os.environ.pop("RUN_LOG_PATH", None)
        else:
            os.environ["RUN_LOG_PATH"] = old_env
    print("  OK  registro delle esecuzioni: inizio e fine con lo stesso id, status per uscita normale / codice / "
          "messaggio / interruzione / errore, eccezione originale invariata, sha256 dei config, --resume, output, "
          "registro non scrivibile = solo avviso; runner vero da riga di comando registrato")


def check_provenance() -> None:
    """experiments/provenance.py (voce 106): impronta del GT stabile, indipendente dall'ordine e dagli a capo."""
    import provenance as pv
    gt = pv.corpus_gt()
    d1 = pv.gt_digest(gt)
    assert d1 == pv.gt_digest(dict(reversed(list(gt.items()))))  # ordine dei record irrilevante
    changed = json.loads(json.dumps(gt))
    changed["eHome2020"]["edges"][0]["data"]["label"] += "x"
    assert pv.gt_digest(changed) != d1  # una modifica del GT cambia l'impronta
    line = pv.provenance_line(gt)
    assert line.startswith("Analisi eseguita sul commit `") and d1 in line and f"{len(gt)} diagrammi" in line
    # l'impronta del contenuto non dipende dagli a capo del file: stessa con corpus.jsonl riletto in CRLF
    import corpus_loader as clr
    crlf = ROOT / "corpus" / "processed" / "corpus.jsonl"
    text = crlf.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\n", "\r\n")
    tmpf = Path(tempfile.mkdtemp(prefix="prov_")) / "corpus.jsonl"
    tmpf.write_bytes(text.encode("utf-8"))
    assert pv.gt_digest({c["id"]: c["diagram_apollon_json"] for c in clr.load_candidates(tmpf)}) == d1
    shutil.rmtree(tmpf.parent, ignore_errors=True)
    print(f"  OK  provenienza dei report: impronta del GT ({d1[:12]}…) stabile rispetto a ordine e a capo, sensibile "
          "a ogni modifica del GT; riga con commit e numero di diagrammi")


def us_structure_from(diagram: dict):
    import uml_structure as us
    return us.structure_from_apollon(diagram)


def builder_free_record(rid: str) -> dict:
    return next(c["diagram_apollon_json"] for c in cl.load_candidates() if c["id"] == rid)


def check_pilot2(tmp: Path) -> None:
    """Configurazioni del secondo pilota, schema per la generazione vincolata, calibrazione (server finto)."""
    import yaml
    import calibrate_tokens as ct
    import make_generation_schema as mgs
    cfg = yaml.safe_load((ROOT / "experiments" / "configs" / "pilot2_formats.yaml").read_text(encoding="utf-8"))
    assert sorted(cfg["configurations"]) == ["J-G", "J-Q", "J0-Q", "P-G", "P-Q"]  # J0-Q: riferimento (voce 83)
    first = yaml.safe_load((ROOT / "experiments" / "configs" / "pilot_temperature.yaml").read_text(encoding="utf-8"))
    assert cfg["query_ids"] == first["query_ids"]  # stessi 6 esercizi del primo pilota
    total = 0
    for name in cfg["configurations"]:
        r = rx.resolve_configuration(cfg, name)
        assert r["run_id"] == f"pilot2_formats__{name}" and r["configuration"] == name
        fmt = "plantuml" if name.startswith("P") else "apollon"
        constrained = name in ("J-G", "J-Q")  # J0-Q: JSON LIBERO, senza response_format
        assert r["prompt"]["output_format"] == fmt and r["generation"]["structured_output"] == constrained
        assert ("response_schema" in r["client"]) == constrained
        assert (r["model_metadata"]["context_length"], r["generation"]["max_tokens"]) == (32768, 12288)
        assert r["model_metadata"]["enable_thinking"] is False
        assert (r["generation"]["temperature"], r["generation"]["top_p"], r["generation"]["top_k"]) == (0.3, 0.95, 64)
        planned = rx.plan(r, cl.load_candidates())
        assert all(spec.output_format == fmt for _, spec, _, _ in planned)
        total += len(planned)
    assert total == 48 + 12  # 4 configurazioni della regola + il riferimento J0-Q
    j0, jq = rx.resolve_configuration(cfg, "J0-Q"), rx.resolve_configuration(cfg, "J-Q")
    assert (j0["client"]["model"], j0["model_metadata"]) == (jq["client"]["model"], jq["model_metadata"])
    j0_client = rx.make_client({**j0, "client": {**j0["client"], "model": "fake-7b"},  # id del 7B ancora TODO
                                "model_metadata": {**j0["model_metadata"], "model_id": "fake-7b"}})
    assert "response_format" not in j0_client.request_body([{"role": "user", "content": "x"}], rx.params_for(j0, 0))
    # stesso prompt JSON del primo pilota (Gemma libero a 0.3) e di J-Q: cambia solo il vincolo
    builder2 = PromptBuilder(*cl.load_all())
    cands = cl.load_candidates()

    def messages(c: dict) -> dict:  # query -> messaggi del prompt (prima ripetizione / temperatura)
        out = {}
        for q_rec, spec, _, _ in rx.plan(c, cands):
            out.setdefault(q_rec["id"], builder2.build(q_rec, spec).messages)
        return out

    m1, mj0, mjq = messages(first), messages(j0), messages(jq)
    assert set(m1) == set(cfg["query_ids"]) and m1 == mj0 == mjq
    q = rx.resolve_configuration(cfg, "J-Q")["model_metadata"]
    # modello Q = Qwen2.5-Coder 7B Instruct Q6_K (voci 84-85), stessi metadati del suo template
    assert (q["quantization"], q["kv_cache_quant"], q["flash_attention"]) == ("Q6_K", "F16", True)
    t7 = yaml.safe_load((ROOT / "experiments" / "configs" / "qwen25coder7b_template.yaml").read_text(encoding="utf-8"))
    assert {k: v for k, v in t7["model_metadata"].items() if k != "hardware"} == {
        k: v for k, v in q.items() if k != "hardware"}
    assert t7["model_metadata"]["source"] == "lmstudio-community/Qwen2.5-Coder-7B-Instruct-GGUF"
    assert (t7["model_metadata"]["context_length"], t7["generation"]["max_tokens"]) == (32768, 12288)
    assert t7["model_metadata"]["enable_thinking"] is False
    assert t7["client"]["model"] == t7["model_metadata"]["model_id"] == "qwen2.5-coder-7b-instruct"  # voce 86
    assert "NON USATO" in (ROOT / "experiments" / "configs" / "qwen25coder14b_template.yaml").read_text(encoding="utf-8")
    assert cfg["plantuml_label_rule"] == "auto_v1" and rx.APPROVED_LABEL_RULES == ("auto_v1",)  # voce 79
    for name in ("P-G", "P-Q"):
        rx.check_label_rule(rx.resolve_configuration(cfg, name))  # auto_v1 approvata
        for bad in ("TODO", "auto_v2", None):  # qualunque altra regola resta rifiutata
            try:
                rx.check_label_rule(dict(rx.resolve_configuration(cfg, name), plantuml_label_rule=bad))
                raise AssertionError("regola delle etichette non approvata accettata")
            except SystemExit as e:
                assert "non approvata" in str(e)
    for name in ("J-Q", "P-Q", "J0-Q"):  # id del 7B dallo smoke test (voce 86): nessun TODO
        r_q = rx.resolve_configuration(cfg, name)
        assert r_q["client"]["model"] == r_q["model_metadata"]["model_id"] == "qwen2.5-coder-7b-instruct"
        assert rx.make_client(r_q).model == "qwen2.5-coder-7b-instruct"
    g_tpl = yaml.safe_load((ROOT / "experiments" / "configs" / "gemma4_12b_qat_template.yaml").read_text(
        encoding="utf-8"))["model_metadata"]
    for name in ("J-G", "P-G"):  # metadati di caricamento di Gemma (voce 87): F16 e Flash Attention, come il template
        g = rx.resolve_configuration(cfg, name)["model_metadata"]
        assert (g["kv_cache_quant"], g["flash_attention"]) == ("F16", True) == (g_tpl["kv_cache_quant"],
                                                                               g_tpl["flash_attention"])
        assert rx.make_client(rx.resolve_configuration(cfg, name)).model == "google/gemma-4-12b-qat"
    for bad in (None, "X"):
        try:
            rx.resolve_configuration(cfg, bad)
            raise AssertionError("configurazione mancante o sconosciuta accettata")
        except SystemExit:
            pass
    client = rx.make_client(rx.resolve_configuration(cfg, "J-G"))
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
          "per configurazione, response_format solo per J-*, PlantUML solo con la regola approvata auto_v1, "
          "Qwen2.5-Coder 7B (qwen2.5-coder-7b-instruct, Q6_K, KV F16, Flash Attention, = template) pronto, Gemma "
          "pronto (KV F16, Flash Attention), template del 14B "
          "segnato come non usato; "
          "schema di generazione con $ref "
          "espansi e maxItems 39 (79 ground truth validi); calibrazione dei token con max_tokens = 1 sul server finto")


def check_analyze_pilot2(tmp: Path) -> None:
    """experiments/analyze_pilot2.py su dati finti: regola della voce 78 (pareggi e spareggi nell'ordine, soglia
    minima, configurazioni escluse), classifica completa, end-to-end su run finte con risposte grezze."""
    import yaml
    import analyze_pilot2 as a2
    from plantuml_format import apollon_to_plantuml
    from prompt_builder import serialize_diagram

    def M(name, S, tr=0, J=0.5, R=0.5, lat=10.0):
        return {"name": name, "n": 12, "S": S, "truncated": tr, "J": J, "R": R, "latency_median": lat}

    def dec(*ms, excluded=()):
        confs = {m["name"]: {"excluded": None, "metrics": m} for m in ms}
        confs.update({n: {"excluded": "motivo", "metrics": None} for n in excluded})
        return a2.decide(confs)

    d = dec(M("P-G", 10), M("P-Q", 7), M("J-G", 5), M("J-Q", 8))  # nessun pareggio
    assert d["winner"] == "P-G" and len(d["steps"]) == 1
    # classifica: la regola riapplicata alle restanti; P-Q (7) e J-Q (8) sono in pareggio, vince la strada 1
    assert [r["name"] for r in d["ranking"]] == ["P-G", "P-Q", "J-Q", "J-G"]
    assert d["ranking"][1]["decided_by"] == "strada 1 (PlantUML)"
    d = dec(M("P-G", 4), M("P-Q", 10, tr=2), M("J-G", 4), M("J-Q", 9, tr=0))  # S - 1 vince per meno troncamenti
    assert d["winner"] == "J-Q" and d["steps"][-1]["criterion"] == "meno troncamenti"
    assert d["steps"][0]["kept"] == ["P-Q", "J-Q"] and d["steps"][1]["values"] == {"P-Q": 2, "J-Q": 0}
    d = dec(M("P-G", 9, J=0.6), M("J-G", 10, J=0.7), M("P-Q", 3), M("J-Q", 3))
    assert d["winner"] == "J-G" and d["steps"][-1]["criterion"].startswith("Jaccard")
    d = dec(M("P-G", 9, R=0.4), M("J-G", 9, R=0.6), M("P-Q", 3), M("J-Q", 3))
    assert d["winner"] == "J-G" and d["steps"][-1]["criterion"].startswith("accordo")
    d = dec(M("P-G", 9, lat=50.0), M("J-G", 9, lat=20.0), M("P-Q", 3), M("J-Q", 3))
    assert d["winner"] == "J-G" and d["steps"][-1]["criterion"].startswith("latenza")
    d = dec(M("P-Q", 9), M("J-G", 9), M("P-G", 3), M("J-Q", 3))  # tutto pari: strada 1
    assert d["winner"] == "P-Q" and d["steps"][-1]["criterion"] == "strada 1 (PlantUML)"
    d = dec(M("J-G", 9), M("J-Q", 9), M("P-G", 3), M("P-Q", 3))  # tutto pari, stessa strada: Gemma
    assert d["winner"] == "J-G" and d["steps"][-1]["criterion"] == "Gemma"
    d = dec(M("P-G", 9), M("P-Q", 9), M("J-G", 9), M("J-Q", 9))
    assert d["winner"] == "P-G" and [r["name"] for r in d["ranking"]] == ["P-G", "P-Q", "J-G", "J-Q"]
    d = dec(M("P-G", 10, tr=3), M("J-Q", 8, tr=0), M("P-Q", 2), M("J-G", 2))  # S - 2: fuori dal pareggio
    assert d["winner"] == "P-G" and d["steps"][0]["kept"] == ["P-G"]
    d = dec(M("P-G", 9, J=None, tr=0), M("J-G", 9, J=0.1), M("P-Q", 0), M("J-Q", 0))  # J non definito perde
    assert d["winner"] == "J-G"
    d = dec(M("P-G", 5), M("P-Q", 4), M("J-G", 5), M("J-Q", 1))  # miglior S sotto 6/12
    assert d["winner"] is None and "soglia minima" in d["outcome"] and "5/12" in d["reasons"][0]
    assert len(d["ranking"]) == 4  # la classifica si riporta comunque
    assert dec(M("P-G", 6), M("P-Q", 4), M("J-G", 5), M("J-Q", 1))["winner"] == "P-G"  # 6/12: passa
    d = dec(M("J-G", 7), M("J-Q", 6), excluded=("P-G", "P-Q"))  # due configurazioni mancanti: si decide
    assert d["winner"] == "J-G" and [r["name"] for r in d["ranking"]] == ["J-G", "J-Q", "P-G", "P-Q"]
    assert d["ranking"][2]["excluded"] == "motivo"
    d = dec(M("J-Q", 12), excluded=("P-G", "P-Q", "J-G"))  # una sola eseguibile: STOP
    assert d["winner"] is None and d["outcome"].startswith("STOP") and "almeno 2" in d["reasons"][0]
    assert (a2.MIN_S, a2.TIE_WINDOW, a2.MIN_INCLUDED) == (6, 1, 2)  # costanti della voce 78

    # end-to-end su run finte: risposte = ground truth (PlantUML canonico / JSON compatto)
    cfg = yaml.safe_load((ROOT / "experiments" / "configs" / "pilot2_formats.yaml").read_text(encoding="utf-8"))
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    res = tmp / "pilot2"

    def fake_run(name, n=None, truncate=(), reasoning=(), other_prompt=()):
        r = rx.resolve_configuration(cfg, name)
        out = res / r["run_id"]
        (out / "raw").mkdir(parents=True)
        (out / "config.json").write_text(json.dumps({"config": r}), encoding="utf-8")
        lines = []
        for q in r["query_ids"]:
            for rep in range(r["repetitions"]):
                cid = f"{q}__bm25__k2__r{rep}"
                fmt = r["prompt"]["output_format"]
                text = (apollon_to_plantuml(gt[q]) if fmt == "plantuml"
                        else serialize_diagram(gt[q], "compact", True))
                fr = "stop"
                if cid in truncate:
                    text, fr = text[: len(text) // 2], "length"
                v = a2.validate(fmt, text, fr, cid)
                (out / "raw" / f"{cid}.json").write_text(json.dumps({"text": text, "finish_reason": fr}),
                                                         encoding="utf-8")
                lines.append(json.dumps({"call_id": cid, "query_id": q, "repetition": rep, "level": v.level,
                                         "latency_s": 5.0 + rep, "completion_tokens_server": 100,
                                         "prompt_tokens_server": 120, "prompt_tokens_est": 100,
                                         "reasoning_field": "reasoning_content" if cid in reasoning else None,
                                         "reasoning_markers_in_content": [],
                                         "prompt_sha256": f"altro-{q}" if cid in other_prompt else f"sha-{q}"}))
        (out / "manifest.jsonl").write_text("\n".join(lines[:n]) + "\n", encoding="utf-8")

    def fake_first_pilot(invalid=()):
        """Run finta del primo pilota: temperature 0 e 0.3, 3 ripetizioni, JSON libero (stesso prompt: sha-<q>)."""
        first = yaml.safe_load((ROOT / "experiments" / "configs" / "pilot_temperature.yaml").read_text(encoding="utf-8"))
        out = res / a2.FIRST_PILOT_RUN
        (out / "raw").mkdir(parents=True)
        (out / "config.json").write_text(json.dumps({"config": first}), encoding="utf-8")
        lines = []
        for q in first["query_ids"]:
            for temp in (0.0, 0.3):
                for rep in range(3):
                    cid = f"{q}__bm25__k2__t{temp:g}__r{rep}"
                    text = "{ rotto" if cid in invalid else serialize_diagram(gt[q], "compact", True)
                    v = a2.validate("apollon", text, "stop", cid)
                    (out / "raw" / f"{cid}.json").write_text(json.dumps({"text": text, "finish_reason": "stop"}),
                                                             encoding="utf-8")
                    lines.append(json.dumps({"call_id": cid, "query_id": q, "repetition": rep, "temperature": temp,
                                             "level": v.level, "latency_s": 90.0, "prompt_sha256": f"sha-{q}"}))
        (out / "manifest.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")

    fake_run("P-G")
    fake_run("P-Q", truncate=("Louvre__bm25__k2__r0",))
    fake_run("J-Q", reasoning=("Sober__bm25__k2__r1",))  # J-G assente
    infos = {n: a2.load_configuration(res, n, gt) for n in a2.CONFIGURATIONS}
    assert infos["P-G"]["metrics"]["S"] == 12 and infos["P-G"]["metrics"]["J"] == 1.0
    assert infos["P-G"]["metrics"]["R"] == 1.0 and infos["P-G"]["metrics"]["latency_median"] == 5.5
    assert (infos["P-Q"]["metrics"]["S"], infos["P-Q"]["metrics"]["truncated"]) == (11, 1)
    assert "non eseguita" in infos["J-G"]["excluded"] and "ragionamento" in infos["J-Q"]["excluded"]
    assert all(i["level_mismatch"] == 0 for i in infos.values())
    assert infos["J-Q"]["metrics"]["S"] == 12  # le metriche di un'esclusa si riportano comunque
    text, d = a2.report(infos)
    assert d["winner"] == "P-G" and d["steps"][-1]["criterion"] == "meno troncamenti"  # 12 e 11: pareggio
    assert a2.SIZE_NOTE in text and "taglia diversa" in a2.SIZE_NOTE
    assert "scelta la configurazione P-G" in text and "ESCLUSA: non eseguita" in text and "fermata per ragionamento" in text
    assert text.count("| P-G (strada 1 (PlantUML), Gemma 4 12B QAT) |") == 1
    assert "| 1 | P-G (strada 1 (PlantUML), Gemma 4 12B QAT) | 12/12 | 12/12 | 0 | 1.000 | 1.000 | 5.5 |" in text
    assert "| 2 | P-Q (strada 1 (PlantUML), Qwen2.5-Coder 7B) | 11/12 | 11/12 | 1 |" in text  # colonna P1 (voce 89)
    assert "| J-Q (strada 2 (JSON vincolato), Qwen2.5-Coder 7B) | 12/12 | — |" in text
    assert "interactive_present n/a (aggiunto dal convertitore)" in text and "interactive_present 12" not in text
    # RIFERIMENTI (voce 83): J0-Q e Gemma libero del primo pilota, fuori dalla regola e dalla classifica
    refs = {a2.FIRST_PILOT_NAME: a2.load_first_pilot(res, gt), "J0-Q": a2.load_configuration(res, "J0-Q", gt)}
    assert refs[a2.FIRST_PILOT_NAME]["excluded"].startswith("run del primo pilota assente")
    text_r, d_r = a2.report(infos, refs)
    assert text_r.startswith(text) and d_r == d  # i riferimenti non toccano regola e classifica
    assert "| Gemma 4 12B QAT | — | — |" in text_r and "| Qwen2.5-Coder 7B | — | 12/12 (1.00) |" in text_r
    fake_first_pilot(invalid=("Louvre__bm25__k2__t0.3__r2", "Sober__bm25__k2__t0__r0"))
    fake_run("J0-Q", other_prompt=("FilmSet__bm25__k2__r1",))
    refs = {a2.FIRST_PILOT_NAME: a2.load_first_pilot(res, gt), "J0-Q": a2.load_configuration(res, "J0-Q", gt)}
    fp = refs[a2.FIRST_PILOT_NAME]
    assert len(fp["calls"]) == 18 and {c["m"]["temperature"] for c in fp["calls"]} == {0.3}  # solo temperature 0.3
    assert (fp["metrics"]["S"], fp["expected"], fp["level_mismatch"]) == (17, 18, 0)
    assert refs["J0-Q"]["excluded"] is None and refs["J0-Q"]["metrics"]["S"] == 12
    text_r, d_r = a2.report(infos, refs)
    assert d_r == d and all(r["name"] != "J0-Q" for r in d_r["ranking"])  # fuori dalla classifica
    body = text_r[len(text):]
    assert body.startswith("\n## Riferimenti") and "| J0-Q" not in text  # J0-Q solo nella sezione dei riferimenti
    assert "| G-libero (primo pilota) | Gemma 4 12B QAT |" in body
    assert "| 17/18 (0.94) | 17 | 17 | 17 | 17 | 17 | 0 |" in body  # "{ rotto" non supera neppure L0
    assert "| J0-Q | Qwen2.5-Coder 7B | `pilot2_formats__J0-Q` | 12/12 (1.00) |" in body
    assert "- J-Q: 12/12 risposte\n" in body and "- J0-Q: 11/12 risposte — **PROMPT DIVERSI**" in body
    assert "| Gemma 4 12B QAT | 17/18 (0.94) | — |" in body  # J-G assente
    assert "| Qwen2.5-Coder 7B | 12/12 (1.00) | 12/12 (1.00) |" in body
    shutil.rmtree(res / "pilot2_formats__P-Q")
    fake_run("P-Q", n=11)  # run incompleta: esclusa, resta solo P-G -> STOP
    infos = {n: a2.load_configuration(res, n, gt) for n in a2.CONFIGURATIONS}
    assert infos["P-Q"]["excluded"].startswith("incompleta (11/12")
    # la run finta e' del 7B; se il config attuale indicasse un altro modello (es. il 14B) sarebbe una traccia
    old = a2.load_configuration(res, "J0-Q", gt, expected_model_id="qwen/qwen2.5-coder-14b")
    assert "traccia NON usata" in old["excluded"] and old["metrics"] is None and not old["calls"]
    assert a2.load_configuration(res, "J0-Q", gt, expected_model_id="qwen2.5-coder-7b-instruct")["excluded"] is None
    assert a2.expected_model_ids() == {"P-G": "google/gemma-4-12b-qat", "J-G": "google/gemma-4-12b-qat",
                                       "P-Q": "qwen2.5-coder-7b-instruct", "J-Q": "qwen2.5-coder-7b-instruct",
                                       "J0-Q": "qwen2.5-coder-7b-instruct"}
    text, d = a2.report(infos)
    assert d["winner"] is None and "STOP" in text
    with contextlib.redirect_stdout(io.StringIO()):
        assert a2.main(["--results-dir", str(res)]) == 0
    refs = {a2.FIRST_PILOT_NAME: a2.load_first_pilot(res, gt), "J0-Q": a2.load_configuration(res, "J0-Q", gt)}
    assert (res / a2.OUT_NAME / "summary.md").read_text(encoding="utf-8") == a2.report(infos, refs)[0]
    # analisi v2 (voce 89): descrittiva, cartella a parte, l'originale non cambia
    original = (res / a2.OUT_NAME / "summary.md").read_bytes()
    with contextlib.redirect_stdout(io.StringIO()):
        assert a2.main(["--results-dir", str(res), "--postprocess", "v2"]) == 0
    assert (res / a2.OUT_NAME / "summary.md").read_bytes() == original
    v2_text = (res / f"{a2.OUT_NAME}_v2" / "summary.md").read_text(encoding="utf-8")
    assert v2_text.startswith("# Secondo pilota — ANALISI v2 (SOLO DESCRITTIVA")
    assert "Esito che la regola darebbe con la v2" in v2_text and "**Esito:" not in v2_text
    assert "## Risposte cambiate rispetto all'analisi originale" in v2_text
    assert "| nessuna | — | — | — | — | — |" in v2_text  # risposte finte = GT canonico: nessun cambiamento
    # visualizzatore (experiments/render_pilot2.py): pagina autonoma, solo lettura delle run
    import render_pilot2 as rp
    before = sorted(p.relative_to(res) for p in res.rglob("*") if p.is_file())
    with contextlib.redirect_stdout(io.StringIO()):
        assert rp.main(["--results-dir", str(res)]) == 0
    after = sorted(p.relative_to(res) for p in res.rglob("*") if p.is_file())
    assert set(after) - set(before) == {Path(a2.OUT_NAME) / "viewer.html"}  # scrive solo viewer.html
    page = (res / a2.OUT_NAME / "viewer.html").read_text(encoding="utf-8")
    assert all(f'id="{q}"' in page for q in cfg["query_ids"])
    assert not any(x in page for x in ("<script", "<link", "src=", 'href="http'))  # nessuna risorsa esterna
    assert "&lt;|--" in page or "*--" in page  # PlantUML del GT presente ed escapato
    assert "incompleta (11/12" in page  # stato della run incompleta riportato
    n_calls = sum(len(i["calls"]) for i in infos.values()) + len(refs["J0-Q"]["calls"])
    assert page.count("<details>") == n_calls
    print("  OK  analisi del secondo pilota: regola della voce 78 (pareggio entro 1, spareggi nell'ordine troncamenti "
          "/ Jaccard / relazioni / latenza / strada 1 / Gemma, soglia 6/12, meno di 2 eseguibili), classifica "
          "completa con le escluse; run finte: assente, fermata per ragionamento, incompleta, troncata; riferimenti "
          "J0-Q e Gemma libero del primo pilota (solo t = 0.3) fuori dalla regola, controllo del prompt, tabella 2x2")


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


def check_retrievers(builder: PromptBuilder) -> None:
    """Condizioni dense / hybrid / oracle_jt del prompt builder (voce 109) con embedding FINTI (nessun download),
    config dev_retrievers.yaml contro dev_k.yaml, regola di esclusione e interpretazione dell'oracolo di
    experiments/analyze_retrievers.py."""
    import re as _re
    import numpy as np
    import yaml
    import analyze_retrievers as ar
    import prompt_builder as pb
    from dense_retriever import DenseRetriever
    import relevance

    def fake(texts):
        out = np.zeros((len(texts), 64), dtype=np.float32)
        for i, s in enumerate(texts):
            for w in _re.findall(r"[a-z]+", s.lower()):
                out[i, int(hashlib.sha256(w.encode()).hexdigest(), 16) % 64] += 1
        return out

    assert {"dense", "hybrid", "oracle_jt"} <= set(pb.CONDITIONS) and "oracle_jt" in pb.ANALYSIS_ONLY
    assert pb.dense_model() == ("sentence-transformers/all-MiniLM-L6-v2", "1110a243fdf4706b3f48f1d95db1a4f5529b4d41")
    fb = PromptBuilder(builder.candidates, [], dense=DenseRetriever("finto", "0" * 40, encoder=fake, cache_dir=None))
    for q in builder.candidates[:12]:
        pool = {c["id"] for c in fb.pool(q)}
        assert fb.excluded(q) == {q["id"]}
        base = fb.build(q, PromptSpec("bm25", k=3, output_format="plantuml"))
        for cond in ("dense", "hybrid", "oracle_jt"):
            bp = fb.build(q, PromptSpec(cond, k=3, output_format="plantuml"))
            assert q["id"] not in bp.example_ids and set(bp.example_ids) <= pool and len(bp.example_ids) == 3
            assert bp.analysis_only == (cond == "oracle_jt")
            assert bp.instructions == base.instructions and bp.task == base.task
            assert bp.text.replace(bp.examples_block, "") == base.text.replace(base.examples_block, "")
        # il piu' simile per ULTIMO: dense = top-3 del denso (finto) rovesciato; oracle_jt = top-3 per Jt rovesciato
        top = [r.id for r in fb.dense.retrieve(q["description"], 3, exclude_ids={q["id"]})]
        assert [e["id"] for e in fb.select(q, PromptSpec("dense", k=3))] == list(reversed(top))
        qt = relevance.class_tokens(q["diagram_apollon_json"])
        jt = sorted(pool, key=lambda i: (-cl.jaccard(qt, fb.tokens[i]), i))[:3]
        assert [e["id"] for e in fb.select(q, PromptSpec("oracle_jt", k=3))] == list(reversed(jt))
    assert "sentence_transformers" not in sys.modules, "i test non devono caricare sentence-transformers"

    # config: uguale a dev_k salvo condizioni, k = [3], modelli (solo G) e configurazioni (P-G, C-G); 240 generazioni
    cfg = yaml.safe_load((ROOT / "experiments" / "configs" / "dev_retrievers.yaml").read_text(encoding="utf-8"))
    dk = yaml.safe_load((ROOT / "experiments" / "configs" / "dev_k.yaml").read_text(encoding="utf-8"))
    assert cfg["conditions"] == ["dense", "hybrid", "oracle_jt"] and cfg["k"] == [3]
    assert "instructions_variant" not in cfg["prompt"] and sorted(cfg["configurations"]) == ["C-G", "P-G"]
    total = 0
    for name in ("P-G", "C-G"):
        r, b = rx.resolve_configuration(cfg, name), rx.resolve_configuration(dk, name)
        for key in ("query_ids", "repetitions", "seed", "generation", "model_metadata", "client", "config_version",
                    "prompt", "split", "stop_on_reasoning", "plantuml_label_rule"):
            assert r[key] == b[key], key
        total += len(rx.plan(r, builder.candidates))
    assert total == 240, total

    # regola di esclusione (voce 109, con le modifiche): Vc -4 ammesso, -5 escluso; 1 troncamento ammesso (allegato),
    # 2 esclusi; un prompt oltre il budget escluso
    B = {"Vc": 34}
    assert not ar.exclusion(B, {"Vc": 30}, 0, 0)["excluded"]
    assert ar.exclusion(B, {"Vc": 29}, 0, 0)["excluded"]
    e1 = ar.exclusion(B, {"Vc": 34}, 1, 0)
    assert not e1["excluded"] and e1["report_truncated"]
    assert ar.exclusion(B, {"Vc": 40}, 2, 0)["excluded"]
    assert ar.exclusion(B, {"Vc": 40}, 0, 1)["excluded"]
    calls = [{"m": {"call_id": "a", "prompt_tokens_server": 28672}}, {"m": {"call_id": "b", "prompt_tokens_server": 28673}},
             {"m": {"call_id": "c", "prompt_tokens_est": 30000}}]
    assert ar.over_budget(calls, 32768, 4096) == ["b", "c"]
    # oracolo: soglia 0,03 inclusa nel "margine"
    assert ar.oracle_reading({"plantuml": 0.029, "compact": 0.0}).startswith("la qualità del retrieval non")
    assert ar.oracle_reading({"plantuml": 0.03, "compact": -0.1}).startswith("un retrieval migliore")
    assert ar.oracle_reading({"plantuml": 0.0, "compact": 0.05}).startswith("un retrieval migliore")
    print("  OK  retriever come fattore (voce 109): dense / hybrid / oracle_jt con embedding finti (stessi candidati di "
          "bm25, query mai tra gli esempi, il piu' simile per ultimo, prompt uguali salvo gli esempi), config uguale a "
          "dev_k (240 generazioni), regola di esclusione e lettura dell'oracolo sulle soglie")


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
        check_uml_structure()
        check_compact(builder, tmp)
        check_dev(builder)
        check_analyze_dev(builder, tmp)
        check_k(builder, tmp)
        check_instructions(builder, tmp)
        check_retrievers(builder)
        check_review(builder, tmp)
        check_run_log(tmp)
        check_provenance()
        check_pilot2(tmp)
        check_analyze_pilot2(tmp)
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
