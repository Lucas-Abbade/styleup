# Open-Meteo, Supabase (supabase-py / PostgREST / Storage / Auth / RLS) e FastAPI — fatos técnicos verificados (nov/2026)

> Notas de método (leia antes de usar):
> - Data da pesquisa: 2026-11-14. Stack alvo: Python 3.12, fastapi 0.115.6, supabase-py 2.11.0, httpx 0.28, PyJWT 2.10.
> - "Fonte (código)" = li o arquivo-fonte na tag/commit indicado (clones rasos de `supabase/supabase-py` tags `v2.11.0`/`v2.34.1` e `main`, `supabase/postgrest-py v0.19.1`, `supabase/storage-py v0.10.0/v0.11.0`, `supabase/storage` HEAD de 2026-11-13, `open-meteo/open-meteo` HEAD de 2026-11-13, `fastapi 0.115.6`, `starlette 0.41.3`).
> - LIMITAÇÃO IMPORTANTE: o sandbox bloqueou chamadas a `api.open-meteo.com` (proxy 403 / robots). Nenhuma resposta da API Open-Meteo foi testada ao vivo; o que está escrito sobre o comportamento dela vem da documentação oficial e da leitura do código-fonte do servidor. Onde isso importa, está marcado "NÃO TESTADO AO VIVO".
> - Trechos de código rotulados "sugestão" são derivados dos fatos citados (inferência), não copiados de documentação.

---

## 1. Open-Meteo Forecast API: `precipitation_probability` em `current=`, `forecast_hours`, formato, limites

### Takeaway
A premissa "`precipitation_probability` é inválido em `current=` e gera HTTP 400" NÃO se sustenta no código-fonte: `current` é decodificado com o mesmo enum de variáveis usado por `hourly` (que contém `precipitation_probability`), e a doc afirma que toda variável horária também existe como condição atual — porém isso não pôde ser testado ao vivo. O caminho robusto e documentado é `current=temperature_2m,apparent_temperature,precipitation` + `hourly=precipitation_probability` com `forecast_hours` (atenção: a probabilidade horária refere-se à hora ANTERIOR ao timestamp, então a hora em curso é o 2º item, não o 1º).

### Cited Findings
**`current=` e `precipitation_probability`**
- A página de docs lista 15 checkboxes para `current` (temperature_2m, relative_humidity_2m, apparent_temperature, is_day, precipitation, rain, showers, snowfall, weather_code, cloud_cover, pressure_msl, surface_pressure, wind_speed_10m, wind_direction_10m, wind_gusts_10m) e `precipitation_probability` não aparece nessa lista de UI; a mesma página, porém, declara textualmente: "Every weather variable available in hourly data, is available as current condition as well." — [Open-Meteo Docs](https://open-meteo.com/en/docs)
- No servidor, o parâmetro `current` passa por `ForecastVariable.load(commaSeparatedOptional: params.current)`, exatamente o mesmo tipo usado para `hourly` (`typealias HourlyVariable = ForecastVariable`) — [Fonte (código) ForecastapiController.swift, linha ~295 e ~417](https://github.com/open-meteo/open-meteo/blob/HEAD/Sources/App/Controllers/ForecastapiController.swift)
- O enum de variáveis de superfície inclui `case precipitation_probability` — [Fonte (código) VariableHourly.swift, linha ~80](https://github.com/open-meteo/open-meteo/blob/HEAD/Sources/App/Controllers/VariableHourly.swift)
- A função `current(variables:)` lê cada variável num único passo de tempo (`floor` para 900 s quando há dado de 15 min, senão 3600 s); quando o leitor não devolve dado, o valor vira `.nan`, e o escritor JSON serializa não-finitos como `null` — [Fonte (código) ForecastapiController.swift, linhas ~521-550](https://github.com/open-meteo/open-meteo/blob/HEAD/Sources/App/Controllers/ForecastapiController.swift); [JsonWriter.swift linha ~116](https://github.com/open-meteo/open-meteo/blob/HEAD/Sources/App/Helper/Writer/JsonWriter.swift)
- Segundo a doc, as condições atuais derivam de dados de modelo de 15 minutos, e o campo `interval` de `current` indica a duração (em segundos) usada em somas/médias retroativas — [Open-Meteo Docs](https://open-meteo.com/en/docs)

**Erro para variável inválida**
- Um nome de variável desconhecido dispara `DecodingError.dataCorrupted` com a mensagem "Cannot initialize \(Self.self) from invalid String value \(s)" — [Fonte (código) Enums.swift linhas ~54-90](https://github.com/open-meteo/open-meteo/blob/HEAD/Sources/App/Helper/Intrinsics/Enums.swift)
- O middleware de erro converte `DecodingError` em status `.badRequest` (400) e serializa `ErrorResponse2(error: true, reason: reason)`, ou seja, corpo `{"error": true, "reason": "..."}` — [Fonte (código) configure.swift linhas ~350-430](https://github.com/open-meteo/open-meteo/blob/HEAD/Sources/App/configure.swift)
- A documentação confirma o contrato: em erro de parâmetro de URL, retorna-se um objeto JSON de erro com HTTP 400, com `"error": true` e `"reason"` — [Open-Meteo Docs](https://open-meteo.com/en/docs)
- Exemplo real (API marine) de corpo de erro 400 registrado em issue: `{ "error": true, "reason": "No data is available for this location" }`; na mesma issue, pedidos válidos sem dado retornaram HTTP 200 com valores `null` — [open-meteo issue #1364](https://github.com/open-meteo/open-meteo/issues/1364)

**`forecast_hours` / `past_hours` / 15-minutely**
- `forecast_hours`, `forecast_minutely_15`, `past_hours`, `past_minutely_15` são inteiros (>0) que controlam o número de passos horários/15-min, de forma análoga a `forecast_days`; `forecast_days` vai de 0 a 16 (default 7) e `past_days` de 0 a 92 (default 0) — [Open-Meteo Docs](https://open-meteo.com/en/docs)
- Implementação: sem `initial_hours`, o início da janela horária é o instante atual truncado para a hora cheia (no fuso pedido) e o fim é `início + forecast_hours × 3600`; `past_hours` recua o início. Existe também `initial_hours` (alinha o início a uma hora do dia) — [Fonte (código) ForecastapiQuery.swift linhas ~86-90 e ~482-512](https://github.com/open-meteo/open-meteo/blob/HEAD/Sources/App/Helper/ForecastapiQuery.swift)
- `forecast_hours`/`past_hours` não podem ser combinados com `start_date`/`end_date`: erro "Parameter 'forecast_hours' is mutually exclusive with 'start_date' and 'end_date'" — [Fonte (código) ForecastapiQuery.swift linhas ~243-247 e ~581](https://github.com/open-meteo/open-meteo/blob/HEAD/Sources/App/Helper/ForecastapiQuery.swift)
- Dados de 15 minutos nativos só existem para Europa Central e América do Norte; nas demais regiões (ex.: Brasil) o 15-min é interpolado a partir do horário — [Open-Meteo Docs](https://open-meteo.com/en/docs)

**Definições e unidades**
- `precipitation_probability` (hourly): unidade %, descrita como probabilidade de precipitação acima de 0,1 mm na HORA PRECEDENTE ("Preceding hour probability") — [Open-Meteo Docs](https://open-meteo.com/en/docs)
- Em `daily` existem `precipitation_probability_max`, `_mean` e `_min` (%) — [Open-Meteo Docs](https://open-meteo.com/en/docs); [Fonte (código) VariableDaily.swift linhas ~26-28](https://github.com/open-meteo/open-meteo/blob/HEAD/Sources/App/Controllers/VariableDaily.swift)
- Defaults: `temperature_unit=celsius` (alternativa `fahrenheit`), `precipitation_unit=mm` (alternativa `inch`), `timeformat=iso8601` (alternativa `unixtime`), `timezone=GMT` por padrão e `timezone=auto` resolve o fuso pelas coordenadas — [Open-Meteo Docs](https://open-meteo.com/en/docs)

**Formato da resposta**
- Campos de topo: `latitude`, `longitude`, `elevation`, `generationtime_ms`, `utc_offset_seconds`, `timezone`, `timezone_abbreviation`, mais os blocos `hourly` (array `time` + um array por variável), `hourly_units` e, opcionalmente, `current`, `daily`, `daily_units`; múltiplas localizações transformam a saída em lista — [Open-Meteo Docs](https://open-meteo.com/en/docs)
- O escritor JSON emite `<seção>_units` também para `current` (ou seja, `current_units`), com `"time"` em `iso8601` ou `unixtime` — [Fonte (código) JsonWriter.swift linhas ~95-130](https://github.com/open-meteo/open-meteo/blob/HEAD/Sources/App/Helper/Writer/JsonWriter.swift)

**Limites, termos e latência**
- Tier gratuito: menos de 10.000 chamadas/dia, 5.000/hora e 600/minuto; a tabela de preços também cita 300.000/mês — [Open-Meteo Terms](https://open-meteo.com/en/terms); [Open-Meteo Pricing](https://open-meteo.com/en/pricing)
- A cota é de chamadas PONDERADAS: peso por localização = `max(1, (V/10) × max(1, D/14))`, com V = nº de variáveis (uma variável pedida em `current` e em `hourly` conta duas vezes) e D = dias cobertos — [Fonte (docs do repo) api-rate-limiting.md](https://github.com/open-meteo/open-meteo/blob/HEAD/docs/api-rate-limiting.md)
- O uso gratuito é contado, em geral, por IP público de saída; aplicações em provedores com IP compartilhado podem ser limitadas pelo consumo de terceiros — [api-rate-limiting.md](https://github.com/open-meteo/open-meteo/blob/HEAD/docs/api-rate-limiting.md)
- Estouro de cota responde 429 (`tooManyRequests`) com `reason` como "Minutely API request limit exceeded. Please try again in one minute." (análogos para hora/dia), cabeçalho `Retry-After` e cabeçalhos `X-RateLimit-Limit/Remaining/Reset/Window`; sobrecarga responde 503 — [Fonte (código) RateLimiter.swift](https://github.com/open-meteo/open-meteo/blob/HEAD/Sources/App/Helper/Vapor/RateLimiter.swift); [configure.swift](https://github.com/open-meteo/open-meteo/blob/HEAD/Sources/App/configure.swift)
- Uso não comercial apenas: sites/apps com assinatura ou publicidade são exemplos de uso comercial; dados sob CC BY 4.0 com atribuição obrigatória; o serviço reserva-se o direito de bloquear apps/IPs abusivos sem aviso — [Open-Meteo Terms](https://open-meteo.com/en/terms); [Open-Meteo Pricing](https://open-meteo.com/en/pricing)
- Planos pagos usam `customer-api.open-meteo.com` com `&apikey=` (ou cabeçalho `x-api-key`), meta de 99,9% de uptime; o tier gratuito não tem garantia de uptime; servidores na Europa e América do Norte — [Open-Meteo Pricing](https://open-meteo.com/en/pricing); [api-rate-limiting.md](https://github.com/open-meteo/open-meteo/blob/HEAD/docs/api-rate-limiting.md)

### Inferences
- Pelo código, `current=...,precipitation_probability` deve responder HTTP 200 (não 400); o valor pode vir numérico ou `null` dependendo de haver dado de probabilidade para o passo lido. NÃO TESTADO AO VIVO — validar com um `curl` antes de decidir. Se o backend hoje recebe 400, a causa provável é outro nome de variável digitado errado (o `reason` do corpo diz qual).
- Requisição recomendada (robusta, independe do ponto acima), custo 1 chamada ponderada (4 variáveis):
  `GET https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,apparent_temperature,precipitation&hourly=precipitation_probability&forecast_hours=2&timezone=auto`
  - `hourly.time[0]` = hora cheia atual (ex.: 14:00 quando são 14:35) e, como a variável é "da hora precedente", representa 13:00–14:00; `hourly.time[1]` (15:00) representa a hora em curso 14:00–15:00. Para "vai chover agora?", usar o índice 1 (ou `max` dos dois). Com `forecast_hours=1` vem só o índice 0.
  - Alternativa: `forecast_days=1` e localizar em `hourly.time` o primeiro timestamp > `current.time`.
- Com `timezone=auto`, `current.time` e `hourly.time` vêm em hora local ISO8601 sem offset (ex.: `2026-11-14T14:30`); use `utc_offset_seconds` para converter.
- Um app com assinatura/anúncios (StyleUp comercial) não se enquadra no tier gratuito segundo os termos; em produção considerar plano pago ou cache agressivo por (lat,lon arredondados, hora).
- Tratar `429`/`503`/timeouts com fallback (recomendação sem clima) e cache de 10–30 min; em hospedagem com IP compartilhado o 429 pode ocorrer mesmo com uso baixo.

### Gaps
- Não foi possível executar nenhuma chamada real à API (sandbox bloqueado): não confirmei ao vivo (a) o status/valor de `current=precipitation_probability`, (b) o texto exato do `reason` para variável inválida em `current`, (c) a latência típica.
- A doc/pricing não publica número de latência; a página de preços só fala em "low latency". Não encontrei medição oficial atual (o antigo slogan "<10 ms" não foi localizado nas páginas consultadas).
- Não verifiquei se há cache HTTP/CDN nem cabeçalhos `Cache-Control` nas respostas.

---

## 2. supabase-py 2.x: cliente por requisição autenticado como o usuário (PostgREST + Storage)

### Takeaway
Na 2.11.0, `client.postgrest.auth(token)` só altera o header da sessão httpx do PostgREST (compartilhada e mutável → condição de corrida entre requisições) e NÃO afeta `client.storage`; a forma correta é criar um cliente por requisição com `create_client(url, anon_key, options=ClientOptions(headers={"Authorization": f"Bearer {token}"}))`, que propaga o JWT a PostgREST, Storage e Functions. Versões ≥2.16 permitem injetar um `httpx.Client` compartilhado (`ClientOptions(httpx_client=...)`), e ≥2.22 deixaram de mutar esse cliente — o que torna o padrão "um cliente leve por requisição + pool HTTP único" barato e seguro.

### Cited Findings
**Como a 2.11.0 monta os headers**
- `SyncClient.__init__` faz `options.headers.update(self._get_auth_headers())`; `_get_auth_headers` devolve `{"apiKey": supabase_key, "Authorization": <options.headers["Authorization"] se existir, senão "Bearer <supabase_key>">}` — [Fonte (código) supabase-py v2.11.0 `_sync/client.py`](https://github.com/supabase/supabase-py/blob/v2.11.0/supabase/_sync/client.py)
- As propriedades `postgrest`, `storage` e `functions` são criadas sob demanda a partir de `self.options.headers` (`_init_postgrest_client(rest_url, headers=self.options.headers, ...)`, `_init_storage_client(storage_url, headers=self.options.headers, ...)`) — [Fonte (código) v2.11.0 `_sync/client.py`](https://github.com/supabase/supabase-py/blob/v2.11.0/supabase/_sync/client.py)
- `SyncClient.create` só consulta `client.auth.get_session()` quando NENHUM header `Authorization` foi passado nas opções; passando o header, ele é preservado — [Fonte (código) v2.11.0 `_sync/client.py`](https://github.com/supabase/supabase-py/blob/v2.11.0/supabase/_sync/client.py)
- O PR "fix(user auth context): do not overwrite provided client options Authorization header" (bug #420) introduziu esse comportamento e documenta o uso `options = ClientOptions(headers={"Authorization": "Bearer userjwt"}); supabase = create_client(url, key, options)` como forma de definir o contexto do usuário para RLS — [supabase-py PR #766](https://github.com/supabase/supabase-py/pull/766)
- `ClientOptions.headers` usa `default_factory=DEFAULT_HEADERS.copy` (cada instância tem seu dict); defaults `auto_refresh_token=True`, `persist_session=True`, `storage=SyncMemoryStorage` — [Fonte (código) v2.11.0 `lib/client_options.py`](https://github.com/supabase/supabase-py/blob/v2.11.0/supabase/lib/client_options.py)

**`client.postgrest.auth(token)`**
- Em postgrest-py 0.19.x, `auth(token)` executa `self.session.headers["Authorization"] = f"Bearer {token}"`, isto é, muta os headers default da sessão httpx daquele cliente PostgREST — [Fonte (código) postgrest-py v0.19.1 `base_client.py`](https://github.com/supabase/postgrest-py/blob/v0.19.1/postgrest/base_client.py)
- O cliente Storage é outro objeto, com sessão httpx própria criada em `SyncStorageClient.__init__` a partir dos headers recebidos na construção (`_create_session(url, headers, ...)`, `http2=True`) — [Fonte (código) storage-py v0.10.0 `_sync/client.py`](https://github.com/supabase/storage-py/blob/v0.10.0/storage3/_sync/client.py)
- supabase 2.11.0 depende de `postgrest ^0.19`, `storage3 >=0.10,<0.12`, `gotrue ^2.11.0`, `httpx >=0.26,<0.29` — [Fonte (código) v2.11.0 `pyproject.toml`](https://github.com/supabase/supabase-py/blob/v2.11.0/pyproject.toml)

**`client.auth.set_session(...)`**
- O listener `_listen_to_auth_events` zera `_postgrest`, `_storage` e `_functions` e grava `options.headers["Authorization"]` com o access token nos eventos `SIGNED_IN`, `TOKEN_REFRESHED`, `SIGNED_OUT` — portanto `set_session` afeta PostgREST e Storage, mas alterando estado global do cliente — [Fonte (código) v2.11.0 `_sync/client.py`](https://github.com/supabase/supabase-py/blob/v2.11.0/supabase/_sync/client.py)
- `set_session(access_token, refresh_token)` exige os dois tokens; se o access token não expirou chama `get_user(access_token)` (HTTP ao Auth), se expirou tenta refresh e lança `AuthSessionMissingError` sem refresh token — [Fonte (código) supabase-py v2.34.1 `gotrue_client.py`](https://github.com/supabase/supabase-py/blob/v2.34.1/src/auth/src/supabase_auth/_sync/gotrue_client.py)
- Caso real relatado: um único cliente supabase-py num app FastAPI ficava "preso" ao último usuário logado e os inserts com RLS falhavam para os demais; o colaborador da Supabase respondeu apenas com o padrão de injeção de dependência criando cliente por requisição (`Depends(create_supabase)` com `acreate_client`) — [Supabase Discussion #37052](https://github.com/orgs/supabase/discussions/37052)

**Custo e reuso de `httpx.Client`**
- Na 2.11.0, cada `create_client` instancia de imediato o cliente Auth e o objeto Realtime; cada subcliente (auth, postgrest, storage) cria sua própria sessão httpx com `http2=True` — [Fonte (código) v2.11.0 `_sync/client.py`](https://github.com/supabase/supabase-py/blob/v2.11.0/supabase/_sync/client.py); [postgrest-py v0.19.1 `_sync/client.py`](https://github.com/supabase/postgrest-py/blob/v0.19.1/postgrest/_sync/client.py); [auth-py v2.11.0 `gotrue_base_api.py`](https://github.com/supabase/auth-py/blob/v2.11.0/supabase_auth/_sync/gotrue_base_api.py)
- 2.16.0 (2025-06-23) trouxe "allow injection of httpx client (#1117)" e "remove jwt key validation to allow new api keys (#1151)" — [CHANGELOG supabase (tag v2.34.1)](https://github.com/supabase/supabase-py/blob/v2.34.1/src/supabase/CHANGELOG.md)
- 2.22.0 (2025-10-08) corrigiu "do not mutate httpx client inside storage, postgrest and functions (#1249)" — [CHANGELOG supabase-py (main)](https://github.com/supabase/supabase-py/blob/main/CHANGELOG.md)
- Na 2.34.1, `ClientOptions.httpx_client` é documentado como instância httpx usada por PostgREST, functions, auth e storage; `_init_storage_client(..., http_client=...)` repassa o cliente; `postgrest.auth()` passou a gravar em `self.headers` do objeto cliente (não na sessão httpx) e o Storage monta `Headers(self._headers)` a cada request — [Fonte (código) v2.34.1 `lib/client_options.py`](https://github.com/supabase/supabase-py/blob/v2.34.1/src/supabase/src/supabase/lib/client_options.py); [`_sync/client.py`](https://github.com/supabase/supabase-py/blob/v2.34.1/src/supabase/src/supabase/_sync/client.py); [postgrest `base_client.py`](https://github.com/supabase/supabase-py/blob/v2.34.1/src/postgrest/src/postgrest/base_client.py); [storage `file_api.py`](https://github.com/supabase/supabase-py/blob/v2.34.1/src/storage/src/storage3/_sync/file_api.py)
- Versões: 2.11.0 saiu em 2024-12-30; a última estável no PyPI é 2.34.1 (2026-11-06), `requires_python >=3.11`; `postgrest` e `storage3` passaram a ter a mesma numeração (2.34.1) — [PyPI supabase](https://pypi.org/project/supabase/); [PyPI JSON](https://pypi.org/pypi/supabase/json)
- A branch `main` já é `3.0.0-a1` (alpha, `requires-python >=3.12`) e adiciona `Client.with_token(access_token)`, que devolve um cliente derivado compartilhando sessão HTTP/headers/opções, sem I/O, descrito como barato para criar por requisição e sem cliente `auth` próprio — [Fonte (código) supabase-py main `client.py`](https://github.com/supabase/supabase-py/blob/main/src/supabase/src/supabase/client.py); [pyproject main](https://github.com/supabase/supabase-py/blob/main/src/supabase/pyproject.toml); [MIGRATION.md](https://github.com/supabase/supabase-py/blob/main/MIGRATION.md)

**Validação de chave e sync vs async**
- A 2.11.0 rejeita qualquer `supabase_key` que não case com um regex de JWT (`raise SupabaseException("Invalid API key")`), logo chaves novas `sb_publishable_...`/`sb_secret_...` NÃO funcionam nela; a validação foi removida na 2.16.0 — [Fonte (código) v2.11.0 `_sync/client.py`](https://github.com/supabase/supabase-py/blob/v2.11.0/supabase/_sync/client.py); [CHANGELOG supabase](https://github.com/supabase/supabase-py/blob/v2.34.1/src/supabase/CHANGELOG.md)
- A 2.11.0 exporta `create_client` (sync) e `acreate_client`/`create_async_client` + `AsyncClient` (async) — [Fonte (código) v2.11.0 `__init__.py`](https://github.com/supabase/supabase-py/blob/v2.11.0/supabase/__init__.py)

### Inferences
- Por que `postgrest.auth()` num cliente global é inseguro: a sessão httpx é única; a thread A grava o token A, a thread B grava o token B, e a query de A sai com o JWT de B (vazamento entre usuários ou `42501`). No threadpool do FastAPI (endpoints `def`) isso é concorrência real.
- Por que o Storage "não apaga nada" hoje: como `postgrest.auth()` não toca em `client.storage`, os requests de Storage seguem com `Authorization: Bearer <anon key>` (role `anon`) e o RLS filtra tudo (ver seção 3).
- Sugestão para 2.11.0 (sem upgrade):
  ```python
  from supabase import create_client, ClientOptions
  def user_client(token: str):
      return create_client(SUPABASE_URL, SUPABASE_ANON_KEY, options=ClientOptions(
          headers={"Authorization": f"Bearer {token}"},
          auto_refresh_token=False, persist_session=False))
  ```
  Criar um `ClientOptions` NOVO por requisição (o construtor muta `options.headers`). Custo: até 3 sessões httpx novas (auth eager; postgrest/storage lazy) e novos handshakes TLS por requisição, sem reuso de conexão; fechar ao final (`client.postgrest.aclose()`, `client.storage.aclose()`) para não vazar sockets.
- Alternativa mais leve na 2.11.0: instanciar direto `SyncPostgrestClient(f"{url}/rest/v1", schema="public", headers={"apikey": anon, "Authorization": f"Bearer {jwt}"}, timeout=...)` e `SyncStorageClient(f"{url}/storage/v1", headers={...})`, evitando criar Auth/Realtime.
- Recomendação de médio prazo: subir para supabase ≥2.22 (ideal 2.34.x) e usar um `httpx.Client` global (pool, timeouts) injetado via `ClientOptions(httpx_client=shared)` em clientes por requisição — necessário de qualquer forma para aceitar a chave `sb_publishable_` (ver seção 6).
- `set_session` não é adequado no backend: exige refresh token, faz chamada extra ao Auth e muta o cliente.
- Cliente async (`create_async_client`) só compensa se todos os endpoints forem `async def` de ponta a ponta; misturar cliente sync dentro de `async def` bloqueia o event loop (seção 10).

### Gaps
- Não achei documentação oficial da Supabase (docs Python) descrevendo explicitamente o padrão "cliente por requisição com JWT do usuário"; a evidência é código-fonte + PR #766 + discussão #37052 (marcada como não respondida).
- Não medi o custo real (ms) de `create_client` por requisição na 2.11.0.
- Não li o código da `gotrue` exatamente na versão instalada com 2.11.0 para `set_session` (li a 2.34.1 e confirmei que a tag v2.11.0 do auth-py tem `set_session`/`get_user` e não tem `get_claims`).
- A thread-safety de `httpx.Client` compartilhado entre threads não foi verificada em fonte primária nesta pesquisa.

---

## 3. Supabase Storage com RLS: `remove`, `list`, políticas e deleção via SQL

### Takeaway
Sim: `remove([...])` sem permissão (ex.: só anon key, sem JWT do usuário) responde HTTP 200 com lista vazia e NÃO lança exceção — o servidor apaga apenas o que o RLS autoriza e devolve somente os objetos efetivamente removidos; por isso o código deve comparar o retorno com o que pediu. Para apagar são exigidas políticas `SELECT` + `DELETE` em `storage.objects`; `list` pagina com `limit` (default 100)/`offset`; `remove` aceita até 1000 paths por chamada; e `DELETE` direto em `storage.objects` via SQL está bloqueado por trigger desde março/2026.

### Cited Findings
- storage3 (0.10/0.11 e 2.34.1): `remove(paths)` envia `DELETE /object/{bucket}` com JSON `{"prefixes": paths}` e retorna `response.json()` (lista de dicts); só há exceção (`StorageApiError`) quando o HTTP é de erro (`raise_for_status`) — [Fonte (código) storage-py v0.11.0 `file_api.py`](https://github.com/supabase/storage-py/blob/v0.11.0/storage3/_sync/file_api.py); [v2.34.1 `file_api.py`](https://github.com/supabase/supabase-py/blob/v2.34.1/src/storage/src/storage3/_sync/file_api.py)
- No servidor Storage, `deleteObjects` bloqueia os alvos como superusuário, testa a permissão com a conexão do chamador (`db.testPermission(... deleteObjects ...)`), mantém apenas os nomes autorizados (`plainNames.filter(name => authorizedPlainNames.has(name))`), aplica a deleção e devolve `results` (objetos aplicados); a rota responde `response.status(200).send(results)` — [Fonte (código) supabase/storage `src/storage/object.ts`](https://github.com/supabase/storage/blob/HEAD/src/storage/object.ts); [`deleteObjects.ts`](https://github.com/supabase/storage/blob/HEAD/src/http/routes/object/deleteObjects.ts)
- A referência Python de `remove` exige: tabela `buckets` — nenhuma permissão; tabela `objects` — `delete` e `select` — [Supabase Python reference: storage remove](https://supabase.com/docs/reference/python/storage-from-remove)
- A referência Python de `list` exige `select` em `objects`; exemplos usam `{"limit": 100, "offset": 0, "sortBy": {"column": "name", "order": "desc"}, "search": ...}` — [Supabase Python reference: storage list](https://supabase.com/docs/reference/python/storage-from-list)
- Defaults do cliente para `list`: `limit=100`, `offset=0`, `sortBy={"column":"name","order":"asc"}`; o corpo enviado inclui `"prefix": path or ""` em `POST /object/list/{bucket}` — [Fonte (código) storage-py v0.11.0 `constants.py`](https://github.com/supabase/storage-py/blob/v0.11.0/storage3/constants.py); [`file_api.py`](https://github.com/supabase/storage-py/blob/v0.11.0/storage3/_sync/file_api.py)
- Limite de 1000 objetos por chamada de `remove`; objetos removidos são irrecuperáveis; esvaziar bucket via Dashboard/API tem teto de 200.000 objetos — [Supabase Docs: Delete Objects](https://supabase.com/docs/guides/storage/management/delete-objects)
- No código do servidor: `MAX_OBJECTS_PER_REQUEST = 1000` e, com hard limits ligados, o erro é "Bulk object requests are limited to N objects per request." — [Fonte (código) `src/storage/limits.ts`](https://github.com/supabase/storage/blob/HEAD/src/storage/limits.ts)
- A doc manda apagar sempre pela Storage API e nunca por SQL, pois o SQL deixa o arquivo órfão no bucket; mostra a política `for delete to authenticated using (owner = (select auth.uid()::text))` — [Supabase Docs: Delete Objects](https://supabase.com/docs/guides/storage/management/delete-objects)
- Desde a migração `0055-prevent-direct-deletes`, triggers `BEFORE DELETE ... FOR EACH STATEMENT` em `storage.objects` e `storage.buckets` chamam `storage.protect_delete()`, que lança 'Direct deletion from storage tables is not allowed. Use the Storage API instead.' (ERRCODE `42501`) salvo se o GUC `storage.allow_delete_query` for `'true'` — [Fonte (código) migração 0055](https://github.com/supabase/storage/blob/HEAD/migrations/tenant/0055-prevent-direct-deletes.sql)
- O anúncio oficial (5 mar 2026) descreve o trigger de statement que rejeita `DELETE` nas tabelas do schema Storage, diz que a Storage API seta um flag interno e que a mudança está ativa em todos os projetos/regiões; também informa a troca da listagem para paginação por cursor e recomenda o endpoint listV2 — [Supabase Blog: Storage updates](https://supabase.com/blog/supabase-storage-performance-security-reliability-updates)
- storage3 2.34.1 expõe `list_v2(options)` (`POST /object/list-v2/{bucket}`) — [Fonte (código) v2.34.1 `file_api.py`](https://github.com/supabase/supabase-py/blob/v2.34.1/src/storage/src/storage3/_sync/file_api.py)
- Por padrão o Storage não permite uploads sem políticas RLS; upload exige só `INSERT`, upsert exige também `SELECT` e `UPDATE`; exemplo de política por pasta: `(storage.foldername(name))[1] = (select auth.jwt()->>'sub')`; service key ignora RLS — [Supabase Docs: Storage Access Control](https://supabase.com/docs/guides/storage/security/access-control)
- `owner_id` é preenchido a partir do `sub` do JWT no upload; uploads com service key ficam sem dono; `owner` está depreciado em favor de `owner_id` — [Supabase Docs: Storage Ownership](https://supabase.com/docs/guides/storage/security/ownership)
- Quando o `USING` de uma política filtra a linha, nada é lançado e zero linhas casam; já violação de `WITH CHECK` gera `42501`; `auth.uid()` é `null` sem usuário autenticado — [Supabase Docs: Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)

### Inferences
- Com apenas a anon key, o role é `anon`; políticas `TO authenticated` não se aplicam, então `list()` devolve `[]` e `remove()` devolve `[]` com HTTP 200 — falha silenciosa. O backend deve tratar `len(retorno) < len(paths)` como erro.
- Sugestão para apagar tudo de `<user_id>/` no bucket `pecas` (com cliente autenticado como o usuário):
  ```python
  def delete_user_folder(storage, uid: str, bucket="pecas"):
      b = storage.from_(bucket)
      while True:
          items = b.list(uid, {"limit": 1000, "offset": 0})   # sempre offset 0: a lista encolhe
          files = [f"{uid}/{it['name']}" for it in items if it.get("id")]  # pastas: tratar à parte
          if not files: break
          removed = b.remove(files)                      # <= 1000 por chamada
          if len(removed) != len(files): raise RuntimeError("remoção parcial (RLS?)")
  ```
  `list` não é recursivo: subpastas aparecem como entradas a percorrer separadamente (ou usar `list_v2` em versões novas).
- Políticas mínimas para o fluxo (bucket privado `pecas`, pasta = uid): `SELECT`, `INSERT`, `DELETE` (e `UPDATE` se usar upsert) em `storage.objects` com `bucket_id = 'pecas' and (storage.foldername(name))[1] = (select auth.uid()::text)` `TO authenticated`.
- Qualquer função SQL/trigger antiga que faça `delete from storage.objects` (ex.: limpeza em cascata na exclusão de conta) agora falha com `42501`; a limpeza precisa passar pela Storage API.

### Gaps
- Não confirmei em doc oficial que pastas retornam como entradas com `id` nulo no `list` (comportamento conhecido, mas não verificado nesta pesquisa) nem o `limit` máximo aceito por `list`.
- Não testei ao vivo o retorno exato (campos) de `remove` em sucesso; pelo código é a lista dos objetos removidos (linhas de `storage.objects`).
- A página "Delete Objects" só mostra a política `DELETE`; a exigência de `SELECT` vem da referência Python (`delete` e `select`).

---

## 4. Exclusão de conta pelo próprio usuário (LGPD)

### Takeaway
O caminho documentado pela Supabase é a Admin API (`auth.admin.delete_user(id)`), que exige chave secreta/service_role e só deve rodar em servidor; a função SQL `security definer` com `delete from auth.users where id = (select auth.uid())` exposta via RPC é um padrão comunitário amplamente usado (aceito em discussão oficial), mas não aparece como recomendação nos guias oficiais. Em ambos os casos os arquivos do Storage precisam ser apagados antes pela Storage API, e o JWT do usuário continua válido até expirar.

### Cited Findings
- `delete_user(id, should_soft_delete=False)` — "Requires a `secret` key", deve ser chamado apenas em servidor; `should_soft_delete=True` marca `deleted_at` e desativa a conta mantendo dados no schema auth — [Supabase Python reference: auth.admin.delete_user](https://supabase.com/docs/reference/python/auth-admin-deleteuser); [Fonte (código) v2.34.1 `gotrue_admin_api.py`](https://github.com/supabase/supabase-py/blob/v2.34.1/src/auth/src/supabase_auth/_sync/gotrue_admin_api.py)
- Guia oficial: com `shouldSoftDelete: false` a linha sai de `auth.users`, cascateia para `auth.sessions` e invalida refresh tokens; banir temporariamente ou marcar "deletado" só nas tabelas do app não remove o acesso — [Supabase Docs: User Management](https://supabase.com/docs/guides/auth/managing-user-data)
- Apagar o usuário não o desloga: o JWT emitido segue "válido" até o `exp`; mitigação sugerida: expiração curta ou validar `session_id` contra `auth.sessions` em operações sensíveis — [Supabase Docs: User Management](https://supabase.com/docs/guides/auth/managing-user-data)
- A doc afirma: "You cannot delete a user if they are the owner of any objects in Supabase Storage." e sugere apagar os objetos do usuário ou reatribuir a posse — [Supabase Docs: User Management](https://supabase.com/docs/guides/auth/managing-user-data)
- No schema atual do Storage, a FK `objects_owner_fkey` foi removida (migração 0017) e `buckets_owner_fkey` também (migração 0018, que cria `owner_id text` e deprecia `owner`) — [Fonte (código) migração 0017](https://github.com/supabase/storage/blob/HEAD/migrations/tenant/0017-drop-owner-foreign-key.sql); [migração 0018](https://github.com/supabase/storage/blob/HEAD/migrations/tenant/0018-add_owner_id_column_deprecate_owner.sql) — contradiz, em parte, a frase da doc acima (ver Inferences)
- Tabelas do app devem referenciar `auth.users` com `on delete cascade` (exemplo `public.profiles`) e apenas por chave primária, pois objetos gerenciados pela Supabase podem mudar — [Supabase Docs: User Management](https://supabase.com/docs/guides/auth/managing-user-data)
- Padrão comunitário (discussão oficial, resposta marcada como selecionada em set/2025): `create or replace function delete_user() returns void as $$ begin delete from auth.users where id = (select auth.uid()); end; $$ language plpgsql security definer set search_path = '';` chamado por `rpc('delete_user')`; um usuário relatou que sem o `(select ...)` a função não surtia efeito — [Supabase Discussion #250](https://github.com/orgs/supabase/discussions/250)
- Regras oficiais para `security definer`: roda com os privilégios do criador (funções criadas no Dashboard/migração pertencem a `postgres`, que ignora RLS); é obrigatório fixar `search_path` (exemplo `security definer set search_path = ''`) e qualificar schemas; por padrão qualquer role pode executar funções — revogar com `revoke execute on function ... from public; ... from anon;` e conceder a `authenticated` — [Supabase Docs: Database Functions](https://supabase.com/docs/guides/database/functions)
- A doc de RLS recomenda nunca criar função `security definer` em schema exposto pela Data API — [Supabase Docs: Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- `DELETE` direto em `storage.objects` é bloqueado por trigger (ver seção 3) — [Fonte (código) migração 0055](https://github.com/supabase/storage/blob/HEAD/migrations/tenant/0055-prevent-direct-deletes.sql)

### Inferences
- Há tensão entre duas orientações oficiais: o padrão RPC precisa estar em schema exposto (`public`) para ser chamável, mas a doc de RLS desaconselha `security definer` em schema exposto. Se usar RPC: `set search_path = ''`, corpo restrito a `auth.uid()`, `revoke execute ... from public, anon` e `grant execute ... to authenticated`.
- Como a FK de `storage.objects.owner` foi removida em 2023, a exclusão do usuário provavelmente NÃO falha mais por "possuir objetos"; a frase da doc pode estar desatualizada. Efeito prático: se não apagar antes, os arquivos ficam órfãos (problema de LGPD), então a ordem continua sendo: (1) listar/remover objetos via Storage API com o JWT do usuário, (2) apagar linhas do app (ou confiar em `on delete cascade`), (3) apagar `auth.users`.
- Fluxo recomendado para este backend (só anon key + JWT): passos 1–2 com o cliente do usuário e passo 3 via RPC `delete_user()`; ou manter uma chave secreta apenas no servidor e usar a Admin API (caminho documentado). Fazer o passo 3 por último: depois dele, o JWT ainda "vale" até expirar, mas RLS baseado em linhas do usuário já não encontra dados.
- A função `security definer` não consegue limpar o Storage por SQL (trigger de proteção); não tente `delete from storage.objects` dentro dela.

### Gaps
- Não encontrei posição oficial explícita (doc ou maintainer) dizendo que `delete from auth.users` via função `security definer` é "suportado"; só o guia genérico (Admin API) e a discussão comunitária.
- Não verifiquei em doc quais privilégios o role `postgres` tem sobre `auth.users` em projetos atuais (a discussão #250 indica que funciona em 2025).
- Não confirmei ao vivo se a exclusão ainda é bloqueada quando o usuário tem objetos no Storage (doc diz que sim; schema indica que não).

---

## 5. Views e RLS no Supabase (`security_invoker`)

### Takeaway
Views ignoram RLS por padrão porque rodam com os privilégios/políticas do dono (normalmente `postgres`); no Postgres 15+ a correção é criar/alterar a view com `with (security_invoker = true)`, fazendo valer as políticas do usuário que consulta.

### Cited Findings
- "Views bypass RLS by default because they are usually created with the `postgres` user"; em Postgres 15+ usa-se `create view <VIEW_NAME> with(security_invoker = true) as select <QUERY>`; em versões antigas, revogar acesso de `anon`/`authenticated` ou mover a view para schema não exposto — [Supabase Docs: Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- PostgreSQL: por padrão o acesso às relações-base é decidido pelas permissões do dono da view; com RLS nas tabelas-base aplicam-se as políticas do dono; com `security_invoker = true` usam-se permissões e políticas do usuário que executa, "as if the base relations had been referenced directly", e esse usuário precisa ter permissão na view e nas tabelas-base — [PostgreSQL 18 docs: CREATE VIEW](https://www.postgresql.org/docs/current/sql-createview.html)
- Um secret key usa o role `service_role` (atributo `bypassrls`), mas só ignora RLS quando a requisição não traz access token de usuário — [Supabase Docs: Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- Boas práticas de política: envolver helpers em `select` (`(select auth.uid())`), indexar colunas filtradas, sempre nomear o role com `to`; `UPDATE` requer política `SELECT` correspondente — [Supabase Docs: Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)

### Inferences
- Para view existente: `alter view public.minha_view set (security_invoker = true);` (sintaxe padrão do Postgres 15+) e garantir `grant select` nas tabelas-base para `authenticated`, senão a view passa a dar `42501`.
- Qualquer view em `public` criada sem `security_invoker` expõe dados de todos os usuários via Data API com a anon key.

### Gaps
- Não consultei a página do Security Advisor (lint "security definer view") para citar o identificador do alerta.

---

## 6. JWT no Supabase: signing keys, rotação, novas API keys e verificação no backend

### Takeaway
Em nov/2026 o modelo vigente são JWT signing keys assimétricas (ES256 recomendado; RS256 suportado) com JWKS em `/auth/v1/.well-known/jwks.json`, e chaves de API `sb_publishable_...`/`sb_secret_...`; as chaves legadas `anon`/`service_role` estão sendo depreciadas "até o fim de 2026" e o segredo JWT legado já não pode ser rotacionado diretamente — é preciso migrar para signing keys e depois revogar. Ponto crítico: supabase-py 2.11.0 rejeita chaves `sb_publishable_` ("Invalid API key"); é preciso ≥2.16.0.

### Cited Findings
**Signing keys**
- Descoberta: `GET https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json`; algoritmos: ES256 (P-256, recomendado), RS256 (RSA 2048), EdDSA "Coming soon", HS256 não recomendado para produção — [Supabase Docs: JWT Signing Keys](https://supabase.com/docs/guides/auth/signing-keys)
- O endpoint JWKS só devolve chaves públicas de signing keys assimétricas e não devolve nada se o projeto usa segredo compartilhado — [Supabase Docs: JWTs](https://supabase.com/docs/guides/auth/jwts)
- Cache: o JWKS fica 10 min no edge da Supabase e as libs cliente podem manter mais 10 min em memória; recomenda-se esperar ao menos 20 min ao criar standby key ou revogar chave, e não cachear por mais tempo no app — [Supabase Docs: JWT Signing Keys](https://supabase.com/docs/guides/auth/signing-keys); [Supabase Docs: JWTs](https://supabase.com/docs/guides/auth/jwts)
- Migração: botão "Migrate JWT secret" importa o segredo legado para o novo sistema; cria-se uma chave assimétrica em standby; "Rotate keys" passa a assinar novos tokens com ela; depois move-se o segredo legado para "Previously used" e revoga-se (exemplo: aguardar pelo menos 1h15 se a expiração do access token é 1h) — [Supabase Docs: JWT Signing Keys](https://supabase.com/docs/guides/auth/signing-keys)
- Efeitos: rotacionar não desloga ninguém (tokens antigos seguem aceitos até a revogação manual); revogar o segredo legado invalida todo JWT assinado por ele; `anon` e `service_role` são JWTs assinados pelo segredo legado e precisam ser desativados antes da revogação; URLs assinadas do Storage usam outra chave e não são afetadas — [Supabase Docs: JWT Signing Keys](https://supabase.com/docs/guides/auth/signing-keys)
- Página de troubleshooting (atualizada em 4 nov 2026): para projetos ainda sem signing keys assimétricas, "no longer possible to rotate the legacy anon, service and JWT secrets" — deve-se migrar para signing keys + chaves publishable/secret; para projetos já no novo sistema: JWT Keys → Rotate Keys → revogar a chave anterior (sem revogar, a antiga continua válida) — [Supabase Troubleshooting: Rotating Anon, Service, and JWT Secrets](https://supabase.com/docs/guides/troubleshooting/rotating-anon-service-and-jwt-secrets-1Jq6yd)
- Linha do tempo (blog): desde 1 out 2025 projetos novos usam JWT assimétrico por padrão e os existentes tiveram o segredo legado migrado para o novo sistema sem mudança de segredos; `anon`/`service_role` expiram 10 anos após a criação do projeto — [Supabase Blog: JWT Signing Keys](https://supabase.com/blog/jwt-signing-keys)

**API keys**
- Quatro tipos: publishable (`sb_publishable_...`, baixa permissão, "Safe to expose online: web page, mobile or desktop app, GitHub actions, CLIs, source code"), secret (`sb_secret_...`, só backend), `anon` (legada, equivalente à publishable) e `service_role` (legada, equivalente à secret); as novas não são JWTs — [Supabase Docs: API keys](https://supabase.com/docs/guides/api/api-keys)
- Prazo: "Supabase is deprecating the `anon` and `service_role` keys by the end of 2026"; as legadas continuam válidas até serem desativadas em Settings > API Keys, e podem ser reativadas — [Supabase Docs: API keys](https://supabase.com/docs/guides/api/api-keys); [Supabase Docs: Migrating to new API keys](https://supabase.com/docs/guides/getting-started/migrating-to-new-api-keys)
- Cronograma do anúncio: jun/2025 preview, jul/2025 lançamento, nov/2025 projetos novos/restaurados sem chaves legadas, "late 2026 (TBC)" remoção das legadas — [Supabase Discussion #29260](https://github.com/orgs/supabase/discussions/29260)
- As novas chaves vão no header `apikey`, não em `Authorization: Bearer`; chaves secretas devem ficar fora do controle de versão; secret key em navegador recebe 401 — [Supabase Docs: API keys](https://supabase.com/docs/guides/api/api-keys)
- O que protege os dados com a publishable/anon é o RLS (roles `anon` e `authenticated`); habilitar RLS em toda tabela antes do deploy — [Supabase Docs: API keys](https://supabase.com/docs/guides/api/api-keys)

**Verificação no backend**
- Recomendação oficial: `supabase.auth.getClaims()` ou biblioteca JWT de qualidade apontada para o JWKS; verificar HS256 localmente com o segredo compartilhado é desaconselhado — a alternativa para HS256 é `GET /auth/v1/user` com `apikey` + `Authorization: Bearer <jwt>` (200 = válido), que é lenta por depender do Auth server da região — [Supabase Docs: JWTs](https://supabase.com/docs/guides/auth/jwts)
- Claims: `iss` = `https://<project-ref>.supabase.co/auth/v1`; `aud` = `"authenticated"` para tokens de usuário; `role` ∈ {`anon`, `authenticated`, `service_role`}; obrigatórios listados: `iss, aud, exp, iat, sub, role, aal, session_id, email, phone, is_anonymous`; tokens anon/service_role têm `iss: "supabase"` e claim `ref` — [Supabase Docs: JWT Claims Reference](https://supabase.com/docs/guides/auth/jwt-fields)
- PyJWT: `PyJWKClient(uri, cache_keys=False, max_cached_keys=16, cache_jwk_set=True, lifespan=300, headers=None, timeout=30, ssl_context=None, ...)`; `get_signing_key_from_jwt(token)` lê o `kid` e, se não achar, atualiza o JWKS e tenta de novo; `jwt.decode(..., algorithms=[...], audience=..., issuer=..., leeway=..., options={"require": [...]})`; exceções `ExpiredSignatureError`, `InvalidAudienceError`, `InvalidIssuerError`, `MissingRequiredClaimError`, `PyJWKClientError`, `PyJWKClientConnectionError` — [PyJWT API (2.15.1 stable)](https://pyjwt.readthedocs.io/en/stable/api.html); [PyJWT Usage](https://pyjwt.readthedocs.io/en/stable/usage.html)
- supabase-py 2.34.1 `auth.get_claims(jwt)`: valida `exp`; para HS256/sem `kid` cai em `get_user(token)`; para assimétrico busca JWKS e confere a assinatura — o código lido não verifica `aud`/`iss` — [Fonte (código) v2.34.1 `gotrue_client.py`](https://github.com/supabase/supabase-py/blob/v2.34.1/src/auth/src/supabase_auth/_sync/gotrue_client.py)
- PostgREST: JWT inválido/indecodificável → `PGRST301` (401); falha na validação de claims (ex.: expirado) → `PGRST303` (401) — [PostgREST docs (fonte) errors.rst](https://github.com/PostgREST/postgrest/blob/main/docs/references/errors.rst)

### Inferences
- Sugestão de verificação (PyJWT 2.10, projeto com signing key assimétrica):
  ```python
  jwks = jwt.PyJWKClient(f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json", cache_jwk_set=True, lifespan=600)
  key = jwks.get_signing_key_from_jwt(token)
  claims = jwt.decode(token, key.key, algorithms=["ES256", "RS256"], audience="authenticated",
                      issuer=f"{SUPABASE_URL}/auth/v1", options={"require": ["exp", "sub", "aud", "iss"]})
  ```
  Nunca aceitar `HS256` na lista quando se usa chave pública; `lifespan` ≤ 600 s respeita a orientação de não cachear além de ~10 min; `PyJWKClient` faz I/O bloqueante (rodar em dependência `def`/threadpool); ES256/RS256 exigem o pacote `cryptography`.
- Se o projeto ainda assina com HS256 (segredo legado), o JWKS vem vazio: ou migra para signing keys (recomendado), ou valida via `/auth/v1/user`.
- Segredo JWT legado vazado (ex.: commitado no repo): migrar para signing keys → rotacionar → criar chaves publishable/secret → trocar no backend/app → desativar `anon`/`service_role` → revogar o segredo legado. A revogação invalida as chaves legadas e todo token assinado com o segredo (usuários relogam).
- `.env.example` público: a chave publishable (e a `anon` legada, sua equivalente) é projetada para ser pública — segura SE o RLS estiver correto em todas as tabelas/buckets/views; `service_role`/`sb_secret_` e o JWT secret jamais devem ser commitados. Ainda assim, em `.env.example` prefira placeholder, para não acoplar o repo a um projeto real.
- Ação obrigatória antes do fim de 2026: subir supabase-py para ≥2.16.0 (ideal 2.34.x) porque a 2.11.0 rejeita `sb_publishable_...` (seção 2) e a anon legada será removida.

### Gaps
- A doc de API keys não trata especificamente de commitar a `anon` legada; a conclusão vem da equivalência declarada com a publishable.
- Não confirmei a assinatura exata de `PyJWKClient` na versão 2.10 (a doc "stable" lida é 2.15.1; `cooldown_duration` pode não existir na 2.10).
- Não há exemplo oficial em Python para verificação via JWKS (só TypeScript/`jose`).
- Não verifiquei se, com chave publishable, o envio de `Authorization: Bearer <publishable>` pelo supabase-py em chamadas anônimas é aceito pelo gateway (a doc diz para usar só `apikey`).
- Data final exata de remoção das chaves legadas: fontes dizem "by the end of 2026"/"late 2026 (TBC)", sem dia definido.

---

## 7. PostgREST: limites de URL com `.in_()`, códigos de erro e falhas de rede

### Takeaway
No Supabase, requisições com ~16 KB ou mais somando URL + headers costumam falhar com erro 520 (camada Cloudflare), e o caso clássico é um `in` com centenas/milhares de IDs; a correção oficial é mover os IDs para o corpo via RPC. Erros do banco/PostgREST chegam no `APIError` do postgrest-py (`code`, `message`, `details`, `hint`), enquanto falhas de rede sobem como exceções `httpx` cruas (na 0.19.x não há try/except nem retry).

### Cited Findings
- Erros 520 ocorrem com mais frequência quando há 16+ KB de dados em headers/URL; o exemplo oficial é um filtro `in` longo; solução: funções de banco (RPC), que levam a estrutura da consulta para o payload — ex.: função recebendo `id uuid[]` e chamada `rpc('example', { id: [...900 UUIDs] })` (página atualizada em 4 nov 2026) — [Supabase Troubleshooting: Fixing 520 Errors in the Database REST API](https://supabase.com/docs/guides/troubleshooting/fixing-520-errors-in-the-database-rest-api-Ur5-B2)
- Formato do erro PostgREST: JSON com `code`, `details`, `hint`, `message`; erros do próprio PostgREST usam prefixo `PGRST` — [PostgREST docs: Errors](https://docs.postgrest.org/en/stable/references/errors.html)
- Mapeamento SQLSTATE→HTTP: `23505` (unicidade) → 409; `23503` (FK) → 409; `42501` (privilégio insuficiente/RLS) → 403 se autenticado, senão 401; `42883` → 404; `42P01` → 404; `P0001` (`raise` padrão) → 400; `40*` → 500; `53*` → 503; `08*` → 503; demais → 400 — [PostgREST docs: Errors](https://docs.postgrest.org/en/stable/references/errors.html)
- Códigos PGRST relevantes: `PGRST116` (406: mais de 1 ou nenhum item em resposta singular), `PGRST202` (404: função não encontrada/cache de schema defasado), `PGRST204` (400: coluna), `PGRST100` (400: query string), `PGRST102` (400: corpo inválido), `PGRST000-002` (503: conexão com o banco), `PGRST003` (504: timeout do pool) — [PostgREST docs: Errors](https://docs.postgrest.org/en/stable/references/errors.html)
- JWT: `PGRST301` (401, JWT indecodificável/inválido), `PGRST302` (401), `PGRST303` (401, falha de validação/parsing de claims) — [PostgREST docs (fonte) errors.rst](https://github.com/PostgREST/postgrest/blob/main/docs/references/errors.rst)
- Erros customizados: `RAISE` com SQLSTATE `PTxyz` devolve HTTP xyz; SQLSTATE `PGRST` com JSON em message/detail controla status e headers — [PostgREST docs: Errors](https://docs.postgrest.org/en/stable/references/errors.html)
- postgrest-py 0.19.1: `APIError` expõe `message`, `code`, `hint`, `details` e `json()`; `execute()` chama `self.session.request(...)` fora de qualquer try e lança `APIError(r.json())` quando `not r.is_success`; se o corpo não é JSON usa `generate_default_error_message` (`code` = status HTTP, message "JSON could not be generated") — [Fonte (código) postgrest-py v0.19.1 `exceptions.py`](https://github.com/supabase/postgrest-py/blob/v0.19.1/postgrest/exceptions.py); [`_sync/request_builder.py`](https://github.com/supabase/postgrest-py/blob/v0.19.1/postgrest/_sync/request_builder.py)
- Hierarquia httpx: `HTTPError > RequestError > TransportError > {TimeoutException (ConnectTimeout, ReadTimeout, WriteTimeout, PoolTimeout), NetworkError (ConnectError, ReadError, WriteError, CloseError), ProtocolError, ProxyError, UnsupportedProtocol}`; `RequestError` é a base de tudo que pode ocorrer ao emitir um request — [HTTPX docs: Exceptions](https://www.python-httpx.org/exceptions/)
- Storage: erros HTTP viram `StorageApiError(message, error, statusCode)`; na 0.10/0.11 o parse do corpo de erro não é protegido (`exc.response.json()` + chaves obrigatórias) — [Fonte (código) storage-py v0.11.0 `file_api.py`](https://github.com/supabase/storage-py/blob/v0.11.0/storage3/_sync/file_api.py)
- Versões novas: postgrest 2.34.1 tem retry embutido (`send_with_retry`, `retry_enabled=True`, `.retry(False)` por query) e, na `main` (v3 alpha), `APIError` herda de `SupabaseAPIError` com `status_code` — [Fonte (código) v2.34.1 `request_builder.py`](https://github.com/supabase/supabase-py/blob/v2.34.1/src/postgrest/src/postgrest/_sync/request_builder.py); [main `exceptions.py`](https://github.com/supabase/supabase-py/blob/main/src/postgrest/src/postgrest/exceptions.py)

### Inferences
- Conta rápida: um UUID tem 36 caracteres (+1 a 3 do separador); 400 UUIDs ≈ 15–16 KB só de filtro, sem contar o JWT (~1 KB+) e a `apikey` nos headers → acima de ~300–350 UUIDs o `.in_()` fica na zona de falha. Usar RPC com `uuid[]` no corpo, ou reformular (join/view/filtro por `user_id` + `limit`), ou fatiar em lotes de ≤100.
- No Supabase o sintoma documentado é 520 (não necessariamente 414); o `APIError` resultante pode vir com `code` numérico/HTTP e mensagem "JSON could not be generated", pois o corpo é HTML do proxy.
- Tratamento sugerido: `except APIError as e:` → `e.code == "23505"` → 409; `"PGRST116"` → 404; `"42501"` → 403; `"PGRST301"/"PGRST303"` → 401; `except httpx.TimeoutException` → 504; `except httpx.RequestError` → 502/503. Na 0.19.x, um erro Storage com corpo não-JSON pode estourar `JSONDecodeError`/`KeyError` em vez de `StorageApiError`.

### Gaps
- Não encontrei doc oficial citando HTTP 414 para PostgREST/Supabase nem o limite exato de URL do PostgREST em si; a única cifra oficial é "16+KB em headers/URL" → 520.
- Não verifiquei qual versão do PostgREST a plataforma Supabase roda hoje nem se mensagens antigas ("JWT expired" sob `PGRST301`) ainda aparecem; por segurança tratar 301 e 303.
- A página "tables_views" renderizada do PostgREST bloqueou o fetch; usei o `.rst` do repositório.

---

## 8. Escritas atômicas multi-tabela via PostgREST (`rpc`)

### Takeaway
Confirmado: toda requisição PostgREST roda dentro de uma única transação que termina em `COMMIT` se nada falhar, e um `RAISE` dentro da função causa rollback — logo, uma função chamada por `rpc()` que insere em várias tabelas é atômica. Bulk insert com lista também é uma só instrução `INSERT`.

### Cited Findings
- Toda requisição executa em transação (`START TRANSACTION; ... <Main Query> END;`); se não falhar termina em `COMMIT`; qualquer falha do banco reverte; "You can also RAISE an error inside a function to cause a rollback" — [PostgREST docs: Transactions](https://docs.postgrest.org/en/stable/references/transactions.html)
- Modo de acesso: funções `VOLATILE` sob POST rodam em transação read-write; `STABLE`/`IMMUTABLE` rodam read-only (GET/HEAD e POST); isolamento default `READ COMMITTED`, alterável por role (`ALTER ROLE ... SET default_transaction_isolation`) ou por função — [PostgREST docs: Transactions](https://docs.postgrest.org/en/stable/references/transactions.html)
- Funções ficam em `/rpc/<nome>`; no POST os argumentos vão num objeto JSON (cada chave = argumento); função com um único parâmetro `json`/`jsonb` sem nome recebe o corpo inteiro; arrays vão como arrays JSON; passar um array de objetos a um parâmetro `json/jsonb` permite processar várias linhas numa chamada; stored procedures não são suportadas — [PostgREST docs: Functions as RPC](https://docs.postgrest.org/en/stable/references/api/functions.html)
- Bulk insert: enviar array JSON de objetos com chaves uniformes "uses a single INSERT statement on the back-end"; o parâmetro `columns` restringe as chaves inseridas e torna o bulk mais eficiente — [PostgREST docs (fonte) tables_views.rst](https://github.com/PostgREST/postgrest/blob/main/docs/references/api/tables_views.rst)
- Chamada em Python: `supabase.rpc('add_planet', params={'name': 'Jakku'}).execute()`; funções são `security invoker` por padrão (recomendado) — [Supabase Docs: Database Functions](https://supabase.com/docs/guides/database/functions)
- `ON CONFLICT DO UPDATE` garante resultado atômico de INSERT ou UPDATE mesmo sob alta concorrência — [PostgreSQL docs: INSERT](https://www.postgresql.org/docs/current/sql-insert.html)

### Inferences
- Padrão sugerido (security invoker → RLS do usuário continua valendo):
  ```sql
  create or replace function public.criar_look(p_look jsonb, p_itens jsonb)
  returns uuid language plpgsql set search_path = '' as $$
  declare v_id uuid;
  begin
    insert into public.looks (user_id, nome) values ((select auth.uid()), p_look->>'nome') returning id into v_id;
    insert into public.look_itens (look_id, peca_id, ordem)
      select v_id, x.peca_id, x.ordem from jsonb_to_recordset(p_itens) as x(peca_id uuid, ordem int);
    return v_id;
  end $$;
  ```
  `jsonb_to_recordset` exige a lista de colunas tipadas; `jsonb_populate_recordset(null::public.tabela, p_itens)` usa o tipo-linha da tabela.
- Duas chamadas `.insert()` separadas pelo supabase-py são duas transações: se a segunda falhar, a primeira já foi commitada (origem de registros órfãos).
- `client.table("t").insert([{...}, {...}]).execute()` com lista = um request = um `INSERT` = tudo ou nada para aquela tabela (todas as linhas devem ter as mesmas chaves).
- Após criar/alterar função, se vier `PGRST202`, o cache de schema do PostgREST precisa recarregar (`notify pgrst, 'reload schema'`).

### Gaps
- Não busquei a página de funções JSON do PostgreSQL para citar `jsonb_to_recordset`/`jsonb_populate_recordset` (funções padrão; sem fonte coletada nesta pesquisa).
- Não confirmei na referência Python da Supabase o exemplo de "bulk insert" com lista.

---

## 9. Códigos sequenciais por usuário (CLO-000001) sem colisão sob concorrência

### Takeaway
`max()+1` é sujeito a corrida sob `READ COMMITTED` e sequences nativas não são "gapless" nem por usuário; o padrão robusto é uma tabela-contador por usuário com `insert ... on conflict (user_id) do update set last_value = last_value + 1 returning last_value`, que o PostgreSQL garante atômico sob alta concorrência, de preferência dentro de um trigger `BEFORE INSERT` (ou de uma função RPC) na mesma transação do insert.

### Cited Findings
- Sequences: o valor obtido por `nextval` não é reaproveitado se a transação abortar; abortos, crashes e até `INSERT ... ON CONFLICT` geram buracos; "sequence objects cannot be used to obtain 'gapless' sequences" — [PostgreSQL docs: Sequence Functions](https://www.postgresql.org/docs/current/functions-sequence.html)
- `ON CONFLICT DO UPDATE` assegura desfecho atômico de INSERT ou UPDATE "even under high concurrency"; `RETURNING` devolve a linha inserida ou atualizada; exige privilégio `INSERT` + `UPDATE` na tabela e `SELECT` nas colunas lidas; efeitos de triggers `BEFORE INSERT` por linha refletem-se em `excluded` — [PostgreSQL docs: INSERT](https://www.postgresql.org/docs/current/sql-insert.html)
- Advisory locks: significado definido pela aplicação; os de nível de transação são liberados automaticamente no fim da transação, sem unlock explícito; os de sessão persistem até liberação/fim da sessão e não seguem semântica transacional — [PostgreSQL docs: Explicit Locking](https://www.postgresql.org/docs/current/explicit-locking.html)
- `FOR UPDATE` bloqueia outras transações que tentem `UPDATE`/`DELETE`/`SELECT FOR UPDATE` nas mesmas linhas até o fim da transação — [PostgreSQL docs: Explicit Locking](https://www.postgresql.org/docs/current/explicit-locking.html)
- PostgREST usa `READ COMMITTED` por padrão e cada request é uma transação — [PostgREST docs: Transactions](https://docs.postgrest.org/en/stable/references/transactions.html)
- Função `security definer` roda com privilégios do criador e exige `set search_path = ''`; violação de unicidade chega como `23505` → HTTP 409 — [Supabase Docs: Database Functions](https://supabase.com/docs/guides/database/functions); [PostgREST docs: Errors](https://docs.postgrest.org/en/stable/references/errors.html)

### Inferences
- Por que `max()+1` colide: duas transações `READ COMMITTED` leem o mesmo máximo antes de qualquer commit e geram o mesmo código; sem constraint única gera duplicata, com constraint gera `23505` (precisaria retry). Calcular no Python (select + insert) é ainda pior (duas requisições).
- Sugestão (contador + trigger; livre de colisão e sem buracos por rollback, pois o incremento reverte junto):
  ```sql
  create table public.peca_counters (user_id uuid primary key references auth.users on delete cascade, last_value int not null);
  alter table public.peca_counters enable row level security;  -- sem policies: só o trigger acessa
  create or replace function public.set_peca_codigo() returns trigger
  language plpgsql security definer set search_path = '' as $$
  declare v int;
  begin
    insert into public.peca_counters as c (user_id, last_value) values (new.user_id, 1)
    on conflict (user_id) do update set last_value = c.last_value + 1
    returning c.last_value into v;
    new.codigo := 'CLO-' || lpad(v::text, 6, '0');
    return new;
  end $$;
  create trigger trg_peca_codigo before insert on public.pecas for each row execute function public.set_peca_codigo();
  alter table public.pecas add constraint pecas_user_codigo_uk unique (user_id, codigo);
  ```
  O lock de linha no contador serializa inserts do mesmo usuário até o commit; usuários diferentes não se bloqueiam. Bulk insert de N peças funciona (o trigger roda por linha).
- RLS: se a função do trigger for `security invoker`, o usuário precisaria de políticas `INSERT`/`UPDATE`/`SELECT` no contador (e poderia adulterá-lo); com `security definer` o contador fica inacessível pela API. Funções de trigger não são chamáveis via `/rpc` de forma útil, mas vale revogar `execute` de `anon`/`authenticated` por higiene.
- Alternativa: `pg_advisory_xact_lock(hashtext(user_id::text))` + `max()+1` na mesma transação (lock liberado no commit); funciona, mas custa mais com muitas linhas e depende de todo caminho de escrita pegar o lock. Evitar advisory lock de sessão (pool de conexões/PostgREST).
- "Sem buracos" absoluto não existe se linhas forem deletadas; o contador garante monotonicidade e ausência de colisão. Manter a constraint única como rede de segurança e mapear `23505` para retry/409.
- Backfill: inicializar `last_value` com o maior sufixo existente por usuário antes de ligar o trigger.

### Gaps
- Não coletei citação de documentação que descreva explicitamente a corrida do `max()+1` (é inferência a partir de `READ COMMITTED`).
- A página de locking lida não nomeia `pg_advisory_xact_lock` nem trata de pool de conexões; esses pontos são conhecimento geral, não citados.

---

## 10. FastAPI: `def` vs `async def`, threadpool, lifespan, middleware e handlers de erro

### Takeaway
Endpoints e dependências `def` rodam no threadpool do AnyIO (limite default de 40 threads, compartilhado), enquanto `async def` roda direto no event loop — portanto qualquer chamada bloqueante (supabase-py sync, `httpx.get`, `PyJWKClient`) dentro de `async def` congela todas as requisições, inclusive o health check. Usar `def` para I/O sync (ou `run_in_threadpool`), `lifespan` para warm-up/ajuste do limiter, e saber que o handler de `Exception` (500) roda fora dos middlewares de usuário.

### Cited Findings
**Execução**
- Doc: path operation declarada com `def` "is run in an external threadpool that is then awaited, instead of being called directly (as it would block the server)"; o mesmo vale para dependências `def`; funções utilitárias chamadas pelo seu código não são afetadas — [FastAPI docs: Concurrency and async/await](https://fastapi.tiangolo.com/async/)
- Orientação: lib com `await` → `async def`; lib que fala com banco/API/arquivo sem `await` → `def`; "If you just don't know, use normal `def`"; funções triviais só de CPU ficam melhores como `async def`, a menos que façam I/O bloqueante — [FastAPI docs: Concurrency and async/await](https://fastapi.tiangolo.com/async/)
- Código 0.115.6: `run_endpoint_function` faz `await dependant.call(**values)` se corrotina, senão `await run_in_threadpool(dependant.call, **values)`; dependências sync também usam `run_in_threadpool`/`contextmanager_in_threadpool` — [Fonte (código) fastapi 0.115.6 `routing.py`](https://github.com/fastapi/fastapi/blob/0.115.6/fastapi/routing.py); [`dependencies/utils.py`](https://github.com/fastapi/fastapi/blob/0.115.6/fastapi/dependencies/utils.py)
- `run_in_threadpool(func, *args, **kwargs)` do Starlette embrulha kwargs com `functools.partial` e chama `anyio.to_thread.run_sync(func, *args)`; fastapi 0.115.6 exige `starlette>=0.40.0,<0.42.0` — [Fonte (código) starlette 0.41.3 `concurrency.py`](https://github.com/encode/starlette/blob/0.41.3/starlette/concurrency.py); [fastapi 0.115.6 `pyproject.toml`](https://github.com/fastapi/fastapi/blob/0.115.6/pyproject.toml)
- Starlette usa o threadpool para endpoints `def`, `FileResponse`, `UploadFile` e funções sync de `BackgroundTask`; o pool default tem 40 tokens, compartilhados com outras libs (o FastAPI o usa para dependências sync); ajuste: `limiter = anyio.to_thread.current_default_thread_limiter(); limiter.total_tokens = 100` — [Starlette docs: Thread Pool](https://www.starlette.io/threadpool/)
- AnyIO: "The default AnyIO worker thread limiter has a value of 40"; o exemplo de ajuste roda dentro de função `async`; esse limiter não afeta o executor default do asyncio — [AnyIO docs: Working with threads](https://anyio.readthedocs.io/en/stable/threads.html)

**Lifespan**
- Padrão recomendado: `@asynccontextmanager async def lifespan(app): <startup>; yield; <shutdown>` e `FastAPI(lifespan=lifespan)`; `startup`/`shutdown` por eventos estão depreciados e não são chamados quando `lifespan` é fornecido; lifespan só roda na aplicação principal, não em sub-aplicações montadas — [FastAPI docs: Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)

**Middleware e tempo**
- Exemplo oficial de timing: `@app.middleware("http")` medindo com `time.perf_counter()` em volta de `await call_next(request)` e gravando `response.headers["X-Process-Time"]`; headers customizados visíveis ao navegador exigem `expose_headers` no CORS; o último middleware adicionado é o mais externo; código de saída de dependências com `yield` roda depois do middleware e background tasks depois de todos os middlewares — [FastAPI docs: Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
- O decorator `middleware("http")` registra `BaseHTTPMiddleware` (`self.add_middleware(BaseHTTPMiddleware, dispatch=func)`) — [Fonte (código) starlette 0.41.3 `applications.py`](https://github.com/encode/starlette/blob/0.41.3/starlette/applications.py)
- Limitação documentada do `BaseHTTPMiddleware`: impede que alterações em `contextvars.ContextVar` se propaguem para cima; a alternativa é middleware ASGI puro, que altera headers embrulhando `send` e usando `MutableHeaders(scope=message)` em `http.response.start` — [Starlette docs: Middleware](https://www.starlette.io/middleware/)
- `BaseHTTPMiddleware` executa o app em task group do AnyIO com memory object stream e devolve um `_StreamingResponse` — [Fonte (código) starlette 0.41.3 `middleware/base.py`](https://github.com/encode/starlette/blob/0.41.3/starlette/middleware/base.py)
- Pilha: `ServerErrorMiddleware` (sempre o mais externo) → middlewares do usuário → `ExceptionMiddleware` → roteamento → endpoint; handlers registrados para `500` ou `Exception` vão para o `ServerErrorMiddleware`, os demais para o `ExceptionMiddleware` — [Starlette docs: Middleware](https://www.starlette.io/middleware/); [Fonte (código) starlette 0.41.3 `applications.py`](https://github.com/encode/starlette/blob/0.41.3/starlette/applications.py)

**Handlers de erro**
- Handler customizado: `@app.exception_handler(MinhaExc)` retornando `JSONResponse(status_code=..., content=...)`; para HTTP registrar no `starlette.exceptions.HTTPException` (a do FastAPI herda dela) e para validação em `fastapi.exceptions.RequestValidationError`; corpo default de validação `{"detail": [{"loc": [...], "msg": ..., "type": ...}]}`; handlers default reutilizáveis em `fastapi.exception_handlers` (`http_exception_handler`, `request_validation_exception_handler`) — [FastAPI docs: Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)

### Inferences
- Health check: se algum endpoint `async def` faz I/O bloqueante (supabase-py sync, Open-Meteo com `httpx.get`), o loop fica parado e `/health` (qualquer tipo) não responde → o orquestrador pode reiniciar o serviço. Se `/health` for `def`, ele ainda disputa um dos 40 tokens; mantenha `/health` como `async def` sem I/O.
- Regra para este backend (supabase-py sync): endpoints e dependências que tocam Supabase/Open-Meteo/JWKS como `def`; ou `async def` + `await run_in_threadpool(fn, ...)` (importável de `fastapi.concurrency`) / `httpx.AsyncClient` para o Open-Meteo.
- Capacidade: com 40 threads e chamadas de ~300 ms, o teto é ~130 req/s por processo; requisições excedentes esperam token. Aumentar no lifespan:
  ```python
  @asynccontextmanager
  async def lifespan(app):
      anyio.to_thread.current_default_thread_limiter().total_tokens = 80
      app.state.http = httpx.Client(timeout=httpx.Timeout(10, connect=3))   # pool compartilhado
      await run_in_threadpool(warm_up)   # ex.: baixar JWKS, 1 query leve no Supabase
      yield
      app.state.http.close()
  ```
- Timing: `call_next` retorna quando a resposta inicia; o header mede tempo até o início da resposta (não o streaming do corpo). Exceções tratadas por handlers específicos (HTTPException, validação, classes próprias) passam pelo middleware e recebem o header; exceções genéricas (handler de `Exception`/500) são resolvidas no `ServerErrorMiddleware`, fora dos middlewares do usuário → resposta 500 sem `X-Process-Time` (e sem headers de CORS adicionados por middleware). Para cobrir tudo: middleware ASGI puro ou capturar exceções de domínio (`APIError`, `httpx.RequestError`, `StorageApiError`) com handlers específicos em vez de depender do handler de `Exception`.
- Corpo de erro uniforme (sugestão): handlers para `StarletteHTTPException`, `RequestValidationError`, `postgrest.exceptions.APIError`, `httpx.RequestError` e `Exception`, todos retornando `{"error": {"code": ..., "message": ..., "details": ...}}`; no de validação, usar `exc.errors()` (não `str(exc)`) para não vazar detalhes internos.

### Gaps
- A doc do FastAPI não cita o número 40 nem `run_in_threadpool`; o número vem das docs do Starlette/AnyIO e o uso de `run_in_threadpool` vem do código-fonte.
- A doc do Starlette lista só a limitação de `contextvars` para `BaseHTTPMiddleware`; efeitos sobre background tasks/streaming não foram verificados em fonte primária.
- Não consultei a página de testes de lifespan (uso de `with TestClient(app)`), nem as notas de versão de FastAPI posteriores à 0.115.6.
