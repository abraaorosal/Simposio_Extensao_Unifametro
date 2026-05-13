# Simposio_Extensao_Unifametro

Aplicação React + Vite para publicar na web a grade consolidada do III Simpósio de Extensão Curricular da Unifametro, usando as planilhas de envio de E-pôster e escolha de data/horário.

## Rodar localmente

```bash
npm install
python3 scripts/generate_presentations.py
npm run dev
```

## Build

```bash
npm run build
```

## Publicação web

- O projeto está configurado para GitHub Pages no repositório `Simposio_Extensao_Unifametro`.
- O workflow em `.github/workflows/deploy.yml` publica automaticamente a cada push na branch `main`.
- O `base` do Vite aponta para `/Simposio_Extensao_Unifametro/`.

## Dados

- As planilhas fonte ficam na raiz do projeto.
- O consolidado usado pela interface é gerado em `src/data/presentations.json`.
- Para atualizar a página após trocar as planilhas:

```bash
python3 scripts/generate_presentations.py
npm run build
```
