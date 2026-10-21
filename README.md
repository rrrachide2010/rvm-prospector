# RVM Prospector

Ferramenta interna da RVM que monta uma lista de prospecção por nicho e cidade a partir dos **dados abertos de CNPJ da Receita Federal**. O enriquecimento pela **Google Places API** é opcional.

Cada lead sai com:

- o sistema do **Kit Proibido** indicado para aquele negócio;
- a dor que o dono costuma falar;
- uma pontuação de 0 a 100 com o motivo de cada ponto.

Só usa a biblioteca padrão do Python 3.10+. Não precisa instalar nada.

## Uso

```bash
# 1. Confira os nichos e se os CNAEs existem na tabela da Receita
python -m prospector nichos --conferir

# 2. Recorte da cidade. Baixa ~7 GB, um arquivo por vez, e apaga cada zip depois de ler.
#    Roda uma vez por mês de base. Vale para várias cidades de uma vez:
#    --municipio SOROCABA,VOTORANTIM
python -m prospector cidade --uf SP --municipio SOROCABA   # --paralelo 3 (padrão): o servidor da Receita dá ~1 MB/s por conexão

# 3. Leads, sem rede e em segundos, quantas vezes quiser
python -m prospector leads --uf SP --municipio SOROCABA --nichos saude --anos-min 2 \
  --nao-contatar nao-contatar.txt --saida sorocaba.csv

# 4. (Opcional) Google Places nos 50 melhores.
#    Sem --confirmar, só mostra quantas chamadas faria.
export GOOGLE_PLACES_API_KEY=...   # nunca no código
python -m prospector enriquecer --entrada sorocaba.csv --saida sorocaba-google.csv --limite 50
python -m prospector enriquecer --entrada sorocaba.csv --saida sorocaba-google.csv --limite 50 --confirmar
```

- **Pasta dos dados:** `dados/`, ou o caminho em `PROSPECTOR_DADOS`.
- **Formato da planilha:** CSV com `;` e UTF-8 com BOM, que abre direto no Excel.

## Nichos

Saem da tabela "Para quem vender cada sistema" do Kit Proibido (`prospector/nichos.py`). Cada nicho aponta para um sistema do kit:

| Chave | Cliente | Sistema |
|---|---|---|
| `beleza` | barbearia, salão, estética | Easy!Appointments |
| `assistencia` | assistência técnica, oficina | MapOS |
| `alimentacao` | restaurante, lanchonete | TastyIgniter |
| `hospedagem` | pousada, hotel pequeno | QloApps |
| `comercio` | pequeno comércio, distribuidora | Dolibarr ou Odoo |
| `vendas` | imobiliária | Krayin CRM |
| `ensino` | escola, treinamento | Moodle |
| `escritorio` | contabilidade, advocacia | Nextcloud |

### Setor saúde (`--nichos saude`)

`saude` é um setor: traz os 17 nichos abaixo de uma vez (69 CNAEs conferidos na tabela da Receita). Também dá para pedir só alguns, por exemplo `--nichos farmacia,laboratorio,artigos_medicos`.

| Chave | Cliente | Ativos em Sorocaba* |
|---|---|---|
| `medico` | clínica médica, consultório | 1.943 |
| `enfermagem` | enfermagem, home care, remoção | 973 |
| `psicologia` | psicologia, saúde mental | 695 |
| `odonto` | odontologia, prótese dentária | 517 |
| `fisioterapia` | fisioterapia, terapia ocupacional | 323 |
| `farmacia` | farmácia, manipulação | 305 |
| `academia` | academia, estúdio de condicionamento físico | 304 |
| `otica` | ótica | 265 |
| `integrativas` | práticas integrativas, acupuntura, podologia, outros profissionais | 214 |
| `hospital` | hospital, pronto atendimento | 193 |
| `distribuidora_saude` | distribuidora, representante, manutenção de equipamentos médicos | 160 |
| `diagnostico` | imagem, diagnóstico e terapia especializada | 139 |
| `artigos_medicos` | loja cirúrgica, ortopédica, aluguel de equipamentos | 136 |
| `fonoaudiologia` | fonoaudiologia | 135 |
| `nutricao` | nutrição | 87 |
| `idosos` | residência geriátrica, cuidado continuado | 86 |
| `laboratorio` | laboratório de análises | 62 |

\* Base de 10/2026, CNAE principal, abertos há 1 ano ou mais: 6.537 no total, 3.160 com celular.

Ficam de fora: veterinária, planos de saúde e indústria farmacêutica. Cuidados de LGPD e de publicidade dos conselhos de saúde: [docs/LGPD.md](docs/LGPD.md).

Por padrão, só o **CNAE principal** conta. Com `--secundaria`, um CNAE secundário do nicho também conta, o que traz mais leads e mais ruído.

## Pontuação

A pontuação vai de 0 a 100. A coluna `por_que` mostra de onde veio cada ponto.

| Critério | Pontos |
|---|---|
| Tempo de atividade: 5 anos ou mais | +30 |
| Tempo de atividade: 2 anos ou mais | +20 |
| Tempo de atividade: 1 ano ou mais | +5 |
| Celular, que vira link de WhatsApp | +25 |
| Só telefone fixo | +10 |
| E-mail que não parece ser do contador | +10 |
| Microempresa ou pequeno porte | +25 |
| Porte maior (a decisão pode ser central) | +15 |
| MEI (ticket menor) | +5 |
| Nome fantasia | +10 |
| Filial | −10 |

Os pesos são uma hipótese inicial. Ajuste depois que as primeiras conversas mostrarem quem fecha.

## Fonte dos dados

- **Receita Federal:** compartilhamento público de dados abertos de CNPJ, uma pasta por mês: <https://arquivos.receitafederal.gov.br/index.php/s/YggdBLfdninEJX9>. Conferido em 20/10/2026, com base de 2026-10. Se a Receita mudar o endereço, ajuste `TOKEN` em `prospector/receita.py`.
- **Google Places API (New), Text Search:** o modo `basico` cobra o SKU Pro; o modo `completo` (site, nota, avaliações) cobra o SKU Enterprise. Confira preço e cota gratuita na página oficial antes de rodar.

## Regras

Leia o [docs/LGPD.md](docs/LGPD.md) antes de prospectar. Em resumo: uma mensagem por vez, identificar-se, dizer a fonte, atender o "não quero" na hora e não repassar a lista.

## Testes

```bash
python -m unittest discover -s tests -v
```

Os testes usam dados sintéticos (CNPJs e pessoas fictícios) e não acessam a rede.
