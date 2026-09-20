"""
Adaptador de dados do Webull -> DataFrame OHLCV do quantday.

Contexto importante
-------------------
As barras do Webull chegam num formato especifico (campos como STRING, tempo
ISO-8601 em UTC, ordenadas do mais NOVO para o mais antigo). Este modulo
normaliza esse formato para o DataFrame que o motor de backtest espera:
index datetime (UTC, tz-naive), colunas [open, high, low, close, volume] float,
ordenado do mais antigo para o mais novo.

Duas formas de obter os dados:

1. `normalize_bars(records)` / `load_raw_json(path)`  -> puro, sem rede.
   Use quando ja tem o JSON de barras (por exemplo, salvo por uma chamada da
   ferramenta MCP do Webull, ou por qualquer outro meio).

2. `WebullMDataClient`  -> busca via Webull OpenAPI SDK, com SUAS credenciais.
   Requer `pip install webull-python-sdk-core webull-python-sdk-mdata` e as
   variaveis de ambiente WEBULL_APP_KEY / WEBULL_APP_SECRET. Faz paginacao
   automatica para montar historicos longos.

Restricoes conhecidas da conta/assinatura usada neste projeto:
  * Dados de FUTUROS (US_FUTURES) exigem assinatura separada — indisponiveis
    aqui. Por isso NASDAQ usa o ETF QQQ e "forex" usa ETFs de moeda (FXE, FXB)
    como proxy, todos negociando como US_ETF.
  * ETFs de moeda (FXE=EUR/USD, FXB=GBP/USD) negociam SO no pregao dos EUA
    (RTH), tem baixa liquidez intradiaria (barras com lacunas) e NAO sao o
    mercado forex 24h. Sao um proxy razoavel dado o acesso, com ressalvas.
"""
from __future__ import annotations

import json
import os
from typing import Iterable

import pandas as pd

OHLCV = ["open", "high", "low", "close", "volume"]


# ---------------------------------------------------------------------------
# Normalizacao (sem rede)
# ---------------------------------------------------------------------------
def normalize_bars(records: Iterable[dict]) -> pd.DataFrame:
    """Converte uma lista de barras do Webull no DataFrame OHLCV do quantday.

    Aceita os campos do endpoint get_stock_bars / get_futures_bars:
    time (ISO-8601 UTC), open/high/low/close/volume (string ou numero).
    Ordena do mais antigo para o mais novo e remove duplicatas de tempo.
    """
    rows = list(records)
    if not rows:
        return pd.DataFrame(columns=OHLCV)
    df = pd.DataFrame(rows)

    time_col = next((c for c in ("time", "timestamp", "date") if c in df.columns), None)
    if time_col is None:
        raise ValueError("Barras do Webull sem coluna de tempo (time/timestamp).")

    idx = pd.to_datetime(df[time_col], utc=True)
    out = pd.DataFrame(index=idx)
    for col in OHLCV:
        if col not in df.columns:
            raise ValueError(f"Coluna ausente nas barras do Webull: {col}")
        out[col] = pd.to_numeric(df[col], errors="coerce").values

    out.index = out.index.tz_convert("UTC").tz_localize(None)
    out.index.name = "timestamp"
    out = out[~out.index.duplicated(keep="first")].sort_index()
    out = out.dropna(subset=["open", "high", "low", "close"])
    return out


def load_raw_json(path: str) -> pd.DataFrame:
    """Le um arquivo com o JSON de barras do Webull e normaliza.

    Aceita tanto uma lista JSON quanto um objeto {"data": [...]} ou similar.
    """
    with open(path, "r") as fh:
        payload = json.load(fh)
    if isinstance(payload, dict):
        for key in ("data", "bars", "candles", "result"):
            if key in payload and isinstance(payload[key], list):
                payload = payload[key]
                break
    if not isinstance(payload, list):
        raise ValueError(f"Formato inesperado de JSON em {path}: {type(payload)}")
    return normalize_bars(payload)


def save_csv(df: pd.DataFrame, path: str) -> None:
    """Salva o DataFrame OHLCV no formato lido por quantday.data.load_csv."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    df.to_csv(path, index_label="timestamp")


# ---------------------------------------------------------------------------
# Cliente do Webull OpenAPI SDK (busca via rede, com credenciais do usuario)
# ---------------------------------------------------------------------------
class WebullMDataClient:
    """Cliente fino sobre o Webull OpenAPI Market Data SDK.

    Uso:
        cli = WebullMDataClient()                 # le WEBULL_APP_KEY/SECRET do env
        df = cli.get_bars("QQQ", "US_ETF", "M5", count=3000)
        WebullMDataClient.to_csv(df, "data/QQQ_M5.csv")

    Requer:
        pip install webull-python-sdk-core webull-python-sdk-mdata
        export WEBULL_APP_KEY=...   WEBULL_APP_SECRET=...   (e regiao, se aplicavel)

    Observacao: os nomes exatos de metodos do SDK podem variar por versao;
    este cliente isola essa dependencia num unico ponto (`_market_api`) para
    facilitar o ajuste. A normalizacao do resultado usa `normalize_bars`, que e
    estavel e testada.
    """

    MAX_PER_CALL = 1200  # limite do endpoint por chamada (M1 vai a 1650)

    def __init__(self, app_key: str | None = None, app_secret: str | None = None,
                 region: str = "us"):
        self.app_key = app_key or os.environ.get("WEBULL_APP_KEY")
        self.app_secret = app_secret or os.environ.get("WEBULL_APP_SECRET")
        if not self.app_key or not self.app_secret:
            raise RuntimeError(
                "Defina WEBULL_APP_KEY e WEBULL_APP_SECRET (ou passe no construtor)."
            )
        self.region = region
        self._api = None

    def _market_api(self):
        """Instancia (uma vez) o cliente de market data do SDK oficial."""
        if self._api is not None:
            return self._api
        try:
            from webullsdkcore.client import ApiClient  # type: ignore
            from webullsdkmdata.api import API  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "SDK do Webull ausente. Instale: "
                "pip install webull-python-sdk-core webull-python-sdk-mdata"
            ) from exc
        client = ApiClient(self.app_key, self.app_secret, self.region)
        self._api = API(client)
        return self._api

    def _fetch_once(self, symbol: str, category: str, timespan: str,
                    count: int, end_time_ms: int | None) -> list[dict]:
        """Uma chamada ao SDK. Retorna lista de dicts de barras (bruto)."""
        api = self._market_api()
        # A API de barras costuma se chamar get_bars/query_bars conforme a versao.
        fn = getattr(api.market_data, "get_bars", None) or getattr(
            api.market_data, "query_bars", None
        )
        if fn is None:  # pragma: no cover
            raise RuntimeError(
                "Metodo de barras nao encontrado no SDK; ajuste `_fetch_once` "
                "para a versao instalada (veja a doc do webull-python-sdk-mdata)."
            )
        kwargs = dict(symbol=symbol, category=category, timespan=timespan, count=count)
        if end_time_ms is not None:
            kwargs["end_time"] = end_time_ms
        resp = fn(**kwargs)
        data = getattr(resp, "data", resp)
        if isinstance(data, dict):
            data = data.get("data", data.get("bars", []))
        return list(data)

    def get_bars(self, symbol: str, category: str, timespan: str = "M5",
                 count: int = 1200) -> pd.DataFrame:
        """Busca `count` barras, paginando por end_time quando count > limite."""
        collected: list[dict] = []
        remaining = count
        end_time_ms: int | None = None
        seen: set = set()
        while remaining > 0:
            batch_n = min(remaining, self.MAX_PER_CALL)
            batch = self._fetch_once(symbol, category, timespan, batch_n, end_time_ms)
            if not batch:
                break
            # remove sobreposicao de paginas
            fresh = [b for b in batch if b.get("time") not in seen]
            for b in fresh:
                seen.add(b.get("time"))
            collected.extend(fresh)
            # barra mais antiga desta pagina -> proximo end_time (paginacao p/ tras)
            oldest = min(batch, key=lambda b: b["time"])
            ts = pd.to_datetime(oldest["time"], utc=True)
            end_time_ms = int(ts.timestamp() * 1000) - 1
            remaining -= len(fresh)
            if len(fresh) == 0:
                break
        return normalize_bars(collected)

    @staticmethod
    def to_csv(df: pd.DataFrame, path: str) -> None:
        save_csv(df, path)
