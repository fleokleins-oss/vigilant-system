# 🦈 APEX PREDATOR — GUIA REAL (Pop OS + OpenClaw + Binance)

**Para: Léo Sabino (starbot666)**
**Capital: US$ 81.75 | Estratégia: THE TRINITY**
**Data: Março 2026**

---

## ⚠️ ANTES DE TUDO — VERDADE CRUA

Arbitragem triangular com $81 não funciona. As firmas com servidores
DENTRO da Binance pegam essas oportunidades em 2ms. De Curitiba,
com 150ms+ de latência, você chega atrasado em toda oportunidade.

A TRINITY é a estratégia certa:
- **Pilar 1 (Predador):** Detecta anomalias de volume em moedas antes do varejo entrar
- **Pilar 2 (Fazendeiro):** Extrai funding rate de forma delta-neutral (spot + futures)
- **Pilar 3 (Cofre):** Capital ocioso rende 18-50% APR no Simple Earn

---

## PASSO 1: INSTALAR NODE.JS 22 NO POP OS

Abre o terminal (Ctrl+Alt+T) e cola CADA bloco separado.
Espera cada um terminar antes de colar o próximo.

```bash
# Bloco 1: Instalar NVM (gerenciador de versões do Node)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
```

FECHA o terminal e ABRE um novo. Depois cola:

```bash
# Bloco 2: Instalar Node 22
nvm install 22
```

Depois cola:

```bash
# Bloco 3: Verificar se deu certo
node --version
```

Deve mostrar algo como `v22.x.x`. Se não mostrou, NÃO continue.
Fecha o terminal, abre de novo, e tenta `node --version` de novo.

---

## PASSO 2: INSTALAR OPENCLAW

```bash
# Bloco 4: Instalar OpenClaw (comando oficial)
curl -fsSL https://install.openclaw.ai | bash
```

Vai aparecer um wizard (tela interativa). Siga assim:

1. **AI Provider:** Escolhe `Anthropic`
2. **API Key:** Cola sua API key da Anthropic (pega em https://console.anthropic.com)
   - NÃO tem aspas. Cola só o texto da key. Exemplo:
   - CERTO: `sk-ant-api03-XXXXXX`
   - ERRADO: `"sk-ant-api03-XXXXXX"`
3. **Model:** Escolhe `claude-sonnet-4-20250514` (bom e barato)
4. **Channels:** Pode pular por agora (Skip)
5. **Skills:** Pode pular (vamos instalar manual)
6. **Hooks:** Pular

Quando terminar, testa:

```bash
# Bloco 5: Verificar se OpenClaw está rodando
openclaw status
```

Deve mostrar `Gateway: running` ou algo similar.

---

## PASSO 3: INSTALAR FERRAMENTAS NECESSÁRIAS

```bash
# Bloco 6: Instalar dependências que os skills precisam
sudo apt update
sudo apt install -y curl openssl jq python3 python3-pip
```

---

## PASSO 4: INSTALAR A SKILL BINANCE (OFICIAL)

```bash
# Bloco 7: Instalar skill oficial da Binance para OpenClaw
openclaw skills add openclaw/skills --skill binance
```

Se esse comando não funcionar, faz manual:

```bash
# Bloco 7b: Instalação manual
mkdir -p ~/.openclaw/skills/binance
curl -o ~/.openclaw/skills/binance/SKILL.md https://raw.githubusercontent.com/openclaw/skills/main/skills/openclaw/binance/SKILL.md
```

---

## PASSO 5: CONFIGURAR SUAS CHAVES BINANCE

Primeiro, pega suas chaves na Binance:
1. Vai em https://www.binance.com/en/my/settings/api-management
2. Cria uma API key nova
3. Permissões: ✅ Enable Reading ✅ Enable Spot Trading ✅ Enable Futures
4. Copia a API Key e o Secret Key

Agora configura no OpenClaw:

```bash
# Bloco 8: Abrir arquivo de configuração do OpenClaw
nano ~/.openclaw/openclaw.json
```

Procura a seção `env` (ou cria se não existir) e adiciona:

```json
{
  "env": {
    "BINANCE_API_KEY": "cola-sua-api-key-aqui-sem-aspas-extras",
    "BINANCE_API_SECRET": "cola-seu-secret-aqui-sem-aspas-extras"
  }
}
```

**ATENÇÃO sobre aspas:**
- O arquivo JSON PRECISA das aspas `"` como mostrado acima
- Mas o VALOR da key é só o texto. Exemplo:
  - CERTO: `"BINANCE_API_KEY": "aB3cD4eF5gH6iJ7kL8"`
  - ERRADO: `"BINANCE_API_KEY": ""aB3cD4eF5gH6iJ7kL8""` (aspas duplas)

Salva: Ctrl+O, Enter, Ctrl+X

---

## PASSO 6: INSTALAR A SKILL TRINITY (NOSSA)

```bash
# Bloco 9: Criar pasta da skill
mkdir -p ~/.openclaw/skills/trinity
```

Agora cria o arquivo da skill:

```bash
# Bloco 10: Criar o SKILL.md da Trinity
cat > ~/.openclaw/skills/trinity/SKILL.md << 'SKILL_EOF'
---
name: trinity-capital-manager
description: >
  Gestor de capital para banca de US$ 81.75 na Binance. Executa 3 pilares:
  Sniping de narrativas (volume anomaly em spot), Delta-Neutral Funding
  (spot+futures), e Tesouraria Automática (Binance Simple Earn).
metadata:
  openclaw:
    emoji: "🦈"
    requires:
      bins: ["curl", "openssl", "jq", "python3"]
      env: ["BINANCE_API_KEY", "BINANCE_API_SECRET"]
---

# 🦈 THE TRINITY — Apex Predator Lean

Você é o Trinity Capital Manager, sistema autônomo de gestão de capital
para a conta Binance do Léo Sabino (starbot666).

## Regras Inquebráveis

1. Capital total na conta: US$ 81.75 (atualizar se mudar)
2. Máximo por trade: US$ 6.00 (ou 8% do equity, o que for menor)
3. NUNCA operar em testnet a menos que Léo peça
4. Se drawdown total > 4%, PARAR TUDO por 30 minutos
5. Todo lucro > US$ 0.05 vai para Simple Earn automaticamente
6. Sempre confirmar com Léo antes de executar trades reais
7. Se não há oportunidade clara, mover capital para Simple Earn

## Os 3 Pilares

### Pilar 1: Predador (Sniping de Narrativas)

Detecta anomalias de volume em moedas de baixo/médio cap ANTES do varejo
entrar. NÃO é scalping de milissegundos — são ineficiências de minutos/horas.

Quando Léo perguntar sobre oportunidades:

1. Verificar top movers das últimas 1-4 horas via Binance API:
   ```
   curl -s "https://api.binance.com/api/v3/ticker/24hr" | \
     jq -r 'sort_by(-.priceChangePercent | tonumber) | .[0:20] | .[] |
     "\(.symbol) \(.priceChangePercent)% vol:\(.quoteVolume)"'
   ```

2. Para cada candidato, verificar:
   - Volume 24h > US$ 500.000 (liquidez suficiente)
   - Price change > 5% nas últimas 4h (momentum)
   - Não está no top 10 por market cap (não é BTC/ETH, é mid-cap)

3. Reportar para Léo com recomendação: COMPRAR / ESPERAR / IGNORAR

4. Se Léo aprovar, executar:
   ```
   # Comprar US$ 6 de um token
   TIMESTAMP=$(date +%s%3N)
   QUERY="symbol=TOKENUSDT&side=BUY&type=MARKET&quoteOrderQty=6&timestamp=$TIMESTAMP"
   SIGNATURE=$(echo -n "$QUERY" | openssl dgst -sha256 -hmac "$BINANCE_API_SECRET" | cut -d' ' -f2)
   curl -s -X POST "https://api.binance.com/api/v3/order?$QUERY&signature=$SIGNATURE" \
     -H "X-MBX-APIKEY: $BINANCE_API_KEY"
   ```

### Pilar 2: Fazendeiro (Delta-Neutral Funding)

Extrai funding rate de forma neutra (compra spot + vende futures 1x).
SÓ executa quando funding rate > 0.1% por 8h (= 1.5% ao dia).

Para verificar funding rates:
```
curl -s "https://fapi.binance.com/fapi/v1/premiumIndex" | \
  jq -r 'sort_by(-.lastFundingRate | tonumber) | .[0:10] | .[] |
  "\(.symbol) funding:\(.lastFundingRate) mark:\(.markPrice)"'
```

Se funding > 0.001 (0.1%):
1. Reportar para Léo: "ETHUSDT funding 0.15% — vale US$ 0.009/8h com $6"
2. Se aprovado: comprar $6 de ETH no spot + abrir short $6 de ETHUSDT futures
3. Coletar funding a cada 8h
4. Fechar quando funding normalizar (< 0.05%)

### Pilar 3: Cofre (Tesouraria Automática)

Todo capital que NÃO está em trade ativo vai para Simple Earn.

Para verificar produtos disponíveis:
```
TIMESTAMP=$(date +%s%3N)
QUERY="asset=USDT&size=10&timestamp=$TIMESTAMP"
SIGNATURE=$(echo -n "$QUERY" | openssl dgst -sha256 -hmac "$BINANCE_API_SECRET" | cut -d' ' -f2)
curl -s "https://api.binance.com/sapi/v1/simple-earn/flexible/list?$QUERY&signature=$SIGNATURE" \
  -H "X-MBX-APIKEY: $BINANCE_API_KEY" | jq '.rows[0:5]'
```

Para subscrever lucro no Simple Earn:
```
TIMESTAMP=$(date +%s%3N)
QUERY="productId=PRODUTO_ID&amount=VALOR&timestamp=$TIMESTAMP"
SIGNATURE=$(echo -n "$QUERY" | openssl dgst -sha256 -hmac "$BINANCE_API_SECRET" | cut -d' ' -f2)
curl -s -X POST "https://api.binance.com/sapi/v1/simple-earn/flexible/subscribe?$QUERY&signature=$SIGNATURE" \
  -H "X-MBX-APIKEY: $BINANCE_API_KEY"
```

## Robin Hood Risk (sempre ativo)

Antes de QUALQUER operação, verificar:

```
# Saldo atual
TIMESTAMP=$(date +%s%3N)
QUERY="timestamp=$TIMESTAMP"
SIGNATURE=$(echo -n "$QUERY" | openssl dgst -sha256 -hmac "$BINANCE_API_SECRET" | cut -d' ' -f2)
curl -s "https://api.binance.com/api/v3/account?$QUERY&signature=$SIGNATURE" \
  -H "X-MBX-APIKEY: $BINANCE_API_KEY" | \
  jq '[.balances[] | select(.free | tonumber > 0)]'
```

Se equity total < US$ 78.50 (drawdown > 4%):
- NÃO executar nenhum trade
- Informar Léo: "Robin Hood ativou. DD > 4%. Pausa 30 min."
- Mover todo capital disponível para Simple Earn

## Rotina Diária (quando Léo perguntar "o que temos hoje?")

1. Checar saldo total (spot + earn + futures)
2. Listar posições abertas
3. Verificar funding rates (Pilar 2)
4. Verificar top movers (Pilar 1)
5. Reportar: "Saldo: $X | Earn: $Y | Posições: Z | Oportunidades: ..."

## Formato de Resposta

Sempre responder assim:
- 💰 Saldo: US$ XX.XX
- 📊 Oportunidades encontradas (ou "nada relevante agora")
- ✅ Ação recomendada
- ⚠️ Riscos identificados
SKILL_EOF
```

---

## PASSO 7: REINICIAR OPENCLAW

```bash
# Bloco 11: Reiniciar para carregar as novas skills
openclaw restart
```

Verifica se as skills foram carregadas:

```bash
# Bloco 12: Listar skills instaladas
openclaw skills list
```

Deve mostrar `binance` e `trinity` na lista.

---

## PASSO 8: TESTAR

Abre o chat do OpenClaw (no terminal ou web UI):

```bash
# Bloco 13: Abrir chat no terminal
openclaw chat
```

Agora digita no chat:

```
Verifica meu saldo na Binance e me diz quais são os top 5 movers
das últimas 4 horas com volume acima de $500k
```

Se funcionar, você tem o sistema rodando. Se der erro de API key,
volta no Passo 5 e verifica se as chaves estão certas.

---

## FAQ — PERGUNTAS QUE VOCÊ VAI TER

**P: As aspas do JSON são obrigatórias?**
R: SIM. O arquivo openclaw.json é JSON, então todo texto precisa
   de aspas duplas ao redor. Mas o CONTEÚDO da sua key não tem
   aspas extras. Se sua key é `abc123`, no JSON fica `"abc123"`.

**P: Posso usar minha API key da Anthropic que já tenho?**
R: SIM. O OpenClaw usa a Anthropic para pensar (o "cérebro") e
   a Binance para agir (as "mãos"). São duas keys diferentes.

**P: O OpenClaw vai operar sozinho enquanto eu durmo?**
R: NÃO nesta versão. A Trinity pede confirmação antes de trades.
   Quando você confiar no sistema, podemos remover a confirmação.

**P: E se eu quiser voltar para arb triangular depois?**
R: Quando tiver $500+, podemos criar uma skill de arb. Com $81
   o risco/retorno não justifica.

**P: Preciso de Docker?**
R: NÃO. OpenClaw roda direto no Pop OS. Zero Docker.

**P: E o Podman Desktop que eu encontrei?**
R: Podman é alternativa ao Docker. Não precisa dele para a Trinity.
   Se quiser usar depois para outros projetos, ele funciona bem
   no Pop OS.

---

## PRÓXIMOS PASSOS (depois de tudo funcionando)

1. **Semana 1:** Só monitorar. Usar a Trinity para ver oportunidades
   mas não executar trades reais. Entender o que ela detecta.

2. **Semana 2:** Ativar Pilar 3 (Cofre). Mover capital ocioso para
   Simple Earn. Risco zero, começa a render.

3. **Semana 3:** Ativar Pilar 2 (Fazendeiro). Quando funding rate
   for absurdo (>0.1%), fazer delta-neutral com $6.

4. **Semana 4:** Ativar Pilar 1 (Predador). Começar com $3 por
   trade (metade do máximo) até calibrar.

---

*APEX PREDATOR NEO v666.1 — THE TRINITY*
*starbot666 🦈*
