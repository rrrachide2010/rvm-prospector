# Prospecção com dado público: o que fazer e o que não fazer

Este documento é um checklist operacional, não um parecer jurídico. Antes de prospectar em volume, vale validar com um advogado de proteção de dados.

## Por que dado público ainda é dado pessoal

A base de CNPJ da Receita é pública. Mesmo assim, parte do que ela traz é **dado pessoal** pela LGPD:

- o nome de quem é MEI ou empresário individual (a razão social é o nome da pessoa);
- o telefone e o e-mail de um negócio de uma pessoa só.

Ser público não dispensa uma base legal para usar o dado em prospecção. A LGPD exige respeitar a finalidade, a boa-fé e o interesse público que justificaram a publicação (art. 7º, §§ 3º e 4º).

**Base legal usada aqui:** legítimo interesse (art. 7º, IX, e art. 10). A ANPD tem um guia orientativo sobre essa base legal. Ele pede registrar por escrito o *teste de legítimo interesse*, respondendo a três perguntas:

1. **Finalidade legítima:** oferecer um serviço relacionado à atividade do próprio negócio (sistema de agenda para barbearia, de ordem de serviço para oficina).
2. **Necessidade:** só os dados de contato comercial e de atividade. Nada de sócios, CPF ou endereço residencial.
3. **Expectativa e direitos do titular:** uma oferta B2B ligada à atividade dele, com saída fácil a qualquer momento.

## O que o Prospector já faz

- **Não lê o arquivo de Sócios** (nomes e CPFs de sócios).
- **Tira o CPF** que a Receita cola no fim da razão social de MEI e de empresário individual.
- **Lista de "não contatar"** (`--nao-contatar`): CNPJ ou telefone de quem pediu para sair nunca volta numa lista nova.
- **Fonte e mês da base em toda linha**, para responder "de onde vocês tiraram meu contato?".
- **Aviso quando o e-mail parece ser do contador**, para não mandar oferta para a pessoa errada.

## O que você precisa fazer

- **Identifique-se na primeira mensagem:** seu nome, sua empresa (RVM) e de onde veio o contato ("cadastro público de CNPJ da Receita Federal").
- **Mande uma a uma, escritas para aquele negócio.** Disparo em massa no WhatsApp viola as regras da plataforma, derruba o número e queima a reputação.
- **Atenda o "não quero" na hora:** acrescente o CNPJ e o telefone ao arquivo de não contatar.
- **Apague os leads que não viraram conversa** depois de um prazo definido (sugestão: 6 meses). Lista velha só acumula risco.
- **Não venda nem repasse a lista.** O teste de legítimo interesse foi feito para o seu uso, não para terceiros.

## Google Places (enriquecimento)

- **Sem chave, nada roda.** A chave fica na variável de ambiente `GOOGLE_PLACES_API_KEY`, nunca no código ou na planilha.
- **Os Termos da Google Maps Platform limitam o que pode ser guardado.** O `place_id` pode ser guardado. Trate nota, avaliações e site como consulta pontual: a planilha registra a data da consulta, e você deve consultar de novo antes de usar o dado depois.
- **Defina um limite de gasto real** no Google Cloud, com cota por API. Alerta de orçamento sozinho não segura a cobrança.
