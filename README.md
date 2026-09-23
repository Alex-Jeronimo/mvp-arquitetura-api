# Organizador de Estudos — API de atividades

Esta é a API do Organizador de Estudos, feita em Python com Flask. Ela recebe os cadastros de atividades, aplica os filtros de consulta e salva os dados em SQLite. Também consulta a BrasilAPI para identificar entregas que coincidem com feriados nacionais.

A API é o back-end do **cenário 1.1** do MVP de Arquitetura de Software. A interface fica em um repositório separado e acessa os dados pelas rotas abaixo.

## Rotas próprias

| Método | Rota | Finalidade |
| --- | --- | --- |
| POST | `/atividades` | Cadastrar atividade. |
| GET | `/atividades` | Listar e filtrar por disciplina, prioridade, status e urgência. |
| GET | `/atividades/resumo` | Consultar totais gerais por status, urgência e prazo vencido. |
| GET | `/atividades/<id>` | Consultar atividade por ID. |
| PUT | `/atividades/<id>` | Atualizar atividade ou seu status. |
| DELETE | `/atividades/<id>` | Excluir atividade. |
| GET | `/planejamento/feriados?ano=2026` | Consultar feriados nacionais e listar atividades abertas com entrega na mesma data. |

Documentação interativa: `http://localhost:5000/openapi/swagger`. O endpoint `/` redireciona para o Swagger.

A API tem **quatro caminhos distintos**, com sete operações HTTP. Alguns caminhos aceitam mais de um método, como `/atividades/<id>`, que permite consultar, editar e excluir uma atividade.

## Evolução do componente

O cadastro de atividades e os filtros vieram do meu MVP do semestre anterior. Para esta sprint foram acrescentados o resumo geral, a integração com feriados, o cruzamento entre dados externos e atividades locais, a configuração de banco persistente para Docker, o Dockerfile e os testes automatizados. A API mantém o planejamento separado do CRUD: se a BrasilAPI estiver indisponível, a rota de feriados informa a falha, mas as atividades gravadas continuam acessíveis.

## API externa

O back-end consome `GET https://brasilapi.com.br/api/feriados/v1/{ano}` para obter `date` e `name` de feriados nacionais. Esses dados são tratados e combinados com as atividades gravadas localmente; a interface não redireciona o usuário para a BrasilAPI. A consulta tem tempo limite de cinco segundos e uma falha externa retorna HTTP 502, sem impedir o CRUD local.

A [BrasilAPI](https://github.com/BrasilAPI/BrasilAPI) é um serviço público e gratuito. A rota usada não exige cadastro nem chave de acesso. O [código do projeto tem licença MIT](https://github.com/BrasilAPI/BrasilAPI/blob/main/LICENSE). A [documentação consultada de feriados](https://github.com/BrasilAPI/BrasilAPI/blob/main/pages/docs/doc/holydays.json) não informa uma licença adicional para consumo nem um limite numérico de requisições.

O resultado considera somente atividades ainda não concluídas e informa o total de coincidências. A BrasilAPI cobre feriados **nacionais**; esta consulta não inclui feriados estaduais ou municipais.

## Executar com Docker

Pré-requisitos: Docker Desktop (ou Docker Engine) em modo de contêineres Linux, conexão com a internet para construir a imagem e consultar a BrasilAPI, e porta local `5000` disponível. Na raiz deste repositório:

```sh
docker build -t organizador-api .
docker network create organizador-net
docker volume create organizador-dados
docker run --rm --name api --network organizador-net -p 5000:5000 -v organizador-dados:/app/database organizador-api
```

Se a rede ou o volume já existir, reutilize-os. O arquivo SQLite é criado automaticamente em `/app/database/db.sqlite3`; o volume preserva os dados ao recriar o contêiner. O contêiner da interface deve entrar na mesma rede com o nome `front`, como descrito no README dela.

Também é possível iniciar os dois componentes com `docker compose up --build` na raiz do repositório da interface, após posicionar este repositório como pasta irmã chamada `meu_app_api`.

## Executar sem Docker

Requer Python 3.12. Na raiz deste repositório, crie um ambiente virtual, instale as dependências de `requirements.txt` e inicie a API com os comandos abaixo. Por padrão, o banco fica em `database/db.sqlite3` dentro do diretório de execução. A variável `DATABASE_PATH` permite informar um arquivo diferente.

No Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

No macOS/Linux:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Para testar a integração sem consultar o serviço real, `BRASILAPI_URL` pode apontar para um servidor HTTP de teste que ofereça `/api/feriados/v1/{ano}`.

## Testes

```sh
python -m unittest discover -s tests -v
```

Os testes usam um banco temporário e respostas simuladas da BrasilAPI. Eles verificam o cadastro, as consultas, a edição, a exclusão e o tratamento de falhas na integração. Na edição, também conferem se omitir a descrição mantém o texto e se enviar uma descrição vazia apaga o conteúdo.

A consulta real à BrasilAPI é uma verificação separada: com os contêineres em execução, abra a interface, cadastre uma entrega em um feriado nacional e consulte o ano correspondente.
