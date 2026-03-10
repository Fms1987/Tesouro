# 🏦 SADIPEM API Explorer

Explorador interativo da API do [SADIPEM](https://apidatalake.tesouro.gov.br/docs/sadipem/) — Sistema de Análise da Dívida Pública, Operações de Crédito e Garantias da União, Estados e Municípios.

![preview](https://img.shields.io/badge/API-Tesouro%20Nacional-00c896?style=flat-square)
![react](https://img.shields.io/badge/React-18-4f9ef8?style=flat-square)

---

## 📋 O que esse projeto faz

Permite consultar a API pública do Tesouro Nacional de forma visual, sem precisar digitar URLs manualmente. Você escolhe o endpoint, preenche os filtros e vê os dados retornados em formato organizado.

**Endpoints disponíveis:**
- PVL — Dados Básicos (filtre por UF, tipo de ente, código IBGE)
- Cronograma de Liberações
- Cronograma de Pagamentos
- Taxas de Câmbio
- Resumo — Pagamentos
- Resumo — CDP (Cadastro da Dívida Pública)

---

## 🚀 Como rodar no seu computador

### Passo 1 — Instale o Node.js
Acesse [nodejs.org](https://nodejs.org) e baixe a versão **LTS** (recomendada). Instale normalmente.

### Passo 2 — Baixe este projeto
Clique em **Code → Download ZIP** no GitHub, extraia a pasta.

Ou, se tiver Git instalado, rode no terminal:
```bash
git clone https://github.com/SEU-USUARIO/sadipem-explorer.git
cd sadipem-explorer
```

### Passo 3 — Instale as dependências
Abra o terminal dentro da pasta do projeto e rode:
```bash
npm install
```

### Passo 4 — Inicie o projeto
```bash
npm run dev
```

Abra o navegador em **http://localhost:5173** 🎉

---

## ☁️ Como publicar online (grátis)

### Opção A — Vercel (mais fácil)
1. Crie conta em [vercel.com](https://vercel.com)
2. Clique em **Add New → Project**
3. Conecte seu GitHub e selecione este repositório
4. Clique em **Deploy** — pronto!

### Opção B — Netlify
1. Crie conta em [netlify.com](https://netlify.com)
2. Arraste a pasta do projeto para o painel do Netlify
3. O site fica online automaticamente

---

## 📁 Estrutura do projeto

```
sadipem-explorer/
├── index.html          ← página principal
├── package.json        ← configurações e dependências
├── vite.config.js      ← configuração do bundler
└── src/
    ├── main.jsx        ← ponto de entrada do React
    └── App.jsx         ← todo o código do explorador
```

---

## 🔗 Referências

- [Documentação da API SADIPEM](https://apidatalake.tesouro.gov.br/docs/sadipem/)
- [Tesouro Transparente](https://www.tesourotransparente.gov.br)
- [APIs do Tesouro Nacional](https://www.gov.br/tesouronacional/pt-br/central-de-conteudo/apis)
