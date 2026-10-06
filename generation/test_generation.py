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
import postprocess as pp  # noqa: E402
import run_experiment as rx  # noqa: E402
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

    def log_message(self, *a):
        pass

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
            "enable_thinking": False, "hardware": {"cpu": "c", "gpu": "g", "ram_gb": 1, "vram_gb": 1}}
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
        assert rx.main([str(cfg_path), "--results-dir", str(res)]) == 0
    finally:
        FakeLMStudio.script = []
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
        check_smoke(tmp)
        check_runner(tmp, base)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    assert snapshot_corpus() == before, "il codice della generazione ha scritto in corpus/"
    print(f"  OK  nessuna scrittura in corpus/ ({len(before)} file, sha256 invariati)")
    print("\nTutti i test della generazione sono passati.")


if __name__ == "__main__":
    main()
