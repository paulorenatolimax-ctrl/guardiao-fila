# Fila de publicação — O Guardião da Tradição

Publica um Reel por vez no @prof.paulolima1844, pela API oficial da Meta.

- **Quando:** 8h, 13h e 17h (horário de Brasília), todo dia
- **O que:** o primeiro item de `fila.json` que ainda não foi publicado
- **Vídeos:** ficam como assets da release `videos`
- **Disparo manual:** aba Actions → Publicar Reel → Run workflow

O token da API (secret `IG_TOKEN`) vence em **2 de novembro de 2026**.
A renovação de 28/10/2026 devolveu um token novo, válido até **27 de dezembro de 2026**, mas o secret ainda NÃO foi trocado (falta o secret `GH_PAT`).

**Renovação automática:** o workflow `Renovar token Instagram` (`renovar_token.yml`) roda toda segunda e por disparo manual. Para ele gravar o token novo no `IG_TOKEN`, crie o secret `GH_PAT`: um PAT com permissão `Secrets: read and write` neste repositório. Sem o `GH_PAT`, o workflow só avisa nos logs que o token mudou.
