# wagtail-mptt-comments

**Oferece comentários em árvore para páginas, proteção antispam para visitantes, moderação opcional, notificações e ferramentas do admin do Wagtail. Foi criado para comentários em artigos, não para áreas de fórum ou mensagens privadas.**

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md) · [Italiano](README.it.md) · [Português (Brasil)](README.pt-BR.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Türkçe](README.tr.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

## Principais recursos

- Respostas aninhadas com django-mptt.
- Honeypot, token temporal e desafio simples para envios de visitantes.
- Moderação opcional e notificações a administradores/autores das respostas.
- Tags de template para árvore e widget de comentários recentes, filtrados pelo Site atual.

## Requisitos e compatibilidade

- Dependências declaradas: `Wagtail >= 6.0; django-mptt >= 0.16.0; django-prose-editor >= 0.26; nh3 >= 0.2.14`.
- A compatibilidade entre Python, Django e Wagtail deve ser verificada em conjunto. A dependência mínima do pacote não confirma suporte a todas as versões.

Os metadados declaram Wagtail >= 6.0, mas uma dependência mínima não comprova compatibilidade. Este arquivo não inclui uma matriz automatizada completa para todas as combinações de Django/Wagtail. Antes de atualizar produção, teste as versões exatas, o banco de dados, o armazenamento e as configurações de implantação em staging.

## Instalação

Instale o pacote no mesmo ambiente virtual do seu projeto Wagtail:

```bash
pip install wagtail-mptt-comments
```

Adicione os apps nesta ordem, mantendo as demais dependências do projeto:

```python
INSTALLED_APPS = [
    # Preserve também as outras dependências Django/Wagtail já necessárias.
    "mptt",
    "django_prose_editor",
    "wagtail_mptt_comments",
]
```

```python
from django.urls import include, path
urlpatterns = [
    # ...
    path("comments/", include("wagtail_mptt_comments.urls")),
]
```

Execute `python manage.py migrate wagtail_mptt_comments`.


## Configuração inicial

Exemplo mínimo para começar. Adapte nomes de modelos, campos da API e URLs à sua configuração.

```django
{% load mptt_comment_tags %}
{% render_comments page %}
```

Os comentários recentes podem ser exibidos com `{% get_latest_comments 5 as latest_comments %}`. Use a tag em um contexto de requisição com o Wagtail Site atual configurado.

Use a tag em vez de preparar novamente a árvore, o formulário e a contagem em `Page.get_context()`. A tabela completa de configurações, o fluxo de moderação e as variáveis CSS estão no README em inglês.


## Configurações e comportamento importantes

O README em inglês deste diretório é a referência canônica e contém as tabelas completas de opções e exemplos detalhados. Esta tradução cobre a configuração prática e os avisos essenciais de segurança; consulte a referência em inglês antes de alterar opções avançadas.

Consulte o [README em inglês](README.md) para a referência completa das configurações.

### Observações importantes

Use `{% render_comments page %}` no template e não prepare novamente formulário/árvore em `get_context()`. Comentários recentes devem ser limitados ao Site atual; não confie em cabeçalhos de proxy sem um proxy confiável configurado.

## Segurança e operação

- Mantenha as dependências atualizadas. Para HTML escrito por usuários, use o fluxo previsto de sanitização e renderização; não exiba comentários ou posts armazenados com `|safe` incondicional.
- Verifique migrações e permissões com usuários comuns, restritos, moderadores e administradores.
- Em instalações multissite, teste cada domínio configurado e um host desconhecido. Se nenhum Site for encontrado, a consulta não deve abranger registros de todos os sites.
- Trate tokens de API, credenciais SMTP e URLs privadas como segredos. Não os envie ao Git nem os inclua em relatórios públicos.
- Faça backup do banco de dados e dos arquivos de mídia antes de migrações, movimentações em lote, importações ou da primeira publicação em massa. Teste primeiro em staging.

## Combinações recomendadas

- `wagtail-simple-forum` complementa os comentários de artigos com discussões por tópico e mensagens privadas.
- A organização de imagens e o seletor são opcionais.

## Lista de verificação

- [ ] Instale a versão candidata em staging e registre as versões de Python, Django, Wagtail e banco de dados.
- [ ] Execute `python manage.py check` e as migrações do pacote.
- [ ] Teste o fluxo principal com usuário comum e usuário restrito.
- [ ] Confira logs, acesso, cache, backups e restauração.

O arquivo passou pelas verificações estáticas de sintaxe e empacotamento, mas a integração completa com Django/Wagtail não foi executada neste ambiente. Trate a lista abaixo como requisito para o lançamento, não como prova de que todas as combinações foram testadas.

## Solução de problemas

Se o fluxo não funcionar, confira a configuração do app, migrações, ordem das URLs, permissões e logs do Django. Compare a versão e o exemplo com o README em inglês.

## Licença e suporte

MIT. Código-fonte: [https://github.com/vovansrnd/wagtail-mptt-comments](https://github.com/vovansrnd/wagtail-mptt-comments).

