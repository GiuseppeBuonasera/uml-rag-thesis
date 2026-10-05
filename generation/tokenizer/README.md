# Vocabolario cl100k_base (tiktoken)

`cl100k_base.tiktoken` è il vocabolario BPE dell'encoding `cl100k_base` usato da
[tiktoken](https://github.com/openai/tiktoken). Serve solo a **stimare** i token dei prompt (dry run, `manifest.jsonl`);
la stima è un'approssimazione, perché i modelli locali usano tokenizer propri.

| | |
|---|---|
| Fonte | `https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken` (URL ufficiale in `tiktoken_ext/openai_public.py`) |
| Versione di tiktoken | 0.14.0 (`requirements.txt`) |
| Dimensione | 1.681.126 byte, a capo LF |
| sha256 | `223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7` (anche in `cl100k_base.tiktoken.sha256`; uguale all'`expected_hash` di tiktoken 0.14.0) |
| Licenza | tiktoken è distribuito con licenza MIT: [LICENSE](https://github.com/openai/tiktoken/blob/main/LICENSE). Il file del vocabolario è pubblicato da OpenAI per tiktoken e non ha una licenza propria separata. |

## Perché è nel repository
Stessa regola delle stopword (`retrieval/stopwords_en.txt`): **niente download a runtime**. `tiktoken.get_encoding`
scaricherebbe il file al primo uso e fallisce offline o se il download è bloccato. `generation/token_estimate.py`
costruisce l'encoding da questo file e verifica lo sha256 a ogni caricamento (se non coincide, errore). Vedi
`docs/decisions.md`, voce 67.

`.gitattributes` marca questa cartella `-text`: con `core.autocrlf=true` un checkout Windows convertirebbe gli a capo
e lo sha256 non coinciderebbe più.

## Verifica manuale
```
cd generation/tokenizer
sha256sum -c cl100k_base.tiktoken.sha256
```
