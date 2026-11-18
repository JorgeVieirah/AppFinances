# AppFinances: controle de gastos pessoais

Aplicação web em **Flask** para registrar e acompanhar gastos pessoais por categoria, com login de usuários. Desenvolvida como trabalho de conclusão da disciplina de **Desenvolvimento Rápido de Aplicações em Python** (ADS).

## Funcionalidades

- Cadastro e login de usuários, com senhas armazenadas como **hash** (Werkzeug)
- Registro de gastos com categoria, valor, data e descrição
- Dashboard com os gastos do usuário

## Como executar

```bash
pip install -r requirements.txt
python app.py
# acesse http://127.0.0.1:5000
```

O banco SQLite (`gastos.db`) é criado automaticamente na primeira execução.

## Próximos passos

- [ ] Ler a `secret_key` de uma variável de ambiente em vez de deixá-la no código
- [ ] Gráficos de gastos por categoria e por mês
- [ ] Exportação para CSV

## Stack

Python · Flask · SQLite · HTML/CSS (Jinja2)
