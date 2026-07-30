# Law & Tech News

A static site built with [Zola](https://www.getzola.org/) that publishes the
European law-and-technology digest produced by the `Law tech news tracker`
daily job.

The whole digest is a single scrollable page, grouped by date. Each headline
links straight to the original source. **The internal relevance ratings from
`news.md` are stripped and never published.**

## Layout

```
config.toml                 site configuration (theme = "zola-pickles")
content/_index.md           the generated news page (do not edit by hand)
templates/index.html        overrides the theme home page to render one long list
static/news.css             styling for the news list
scripts/import_news.py      regenerates content/_index.md from news.md
themes/zola-pickles/        the pickles theme, v0.3.6
```

## Updating the news

After the daily job refreshes `news.md`, regenerate the page:

```sh
python3 scripts/import_news.py            # reads ../news.md
python3 scripts/import_news.py /path/to/news.md
```

The script refuses to write the page if a rating string somehow survives.

## Preview and build

Zola 0.19 or newer is required.

```sh
zola serve     # preview at http://127.0.0.1:1111
zola build     # output in ./public
```

Set `base_url` in `config.toml` to the real domain before publishing.

## Theme

[pickles](https://github.com/lukehsiao/zola-pickles) by Luke Hsiao, ported from
the Hugo theme of the same name by Misumi Takuma. Licensed under BlueOak-1.0.0
(see `themes/zola-pickles/LICENSE.md`). It is vendored in `themes/` rather than
added as a submodule so the site builds from a plain clone.
