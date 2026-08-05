# Law & Tech News

A static site built with [Zola](https://www.getzola.org/) that publishes the
European law-and-technology digest produced by the `Law tech news tracker`
daily job.

Stories are grouped by date and paginated at **10 per page**, with Newer/Older
navigation. Each headline links straight to the original source. **The internal
relevance ratings from `news.md` are stripped and never published.**

## Layout

```
config.toml                 site configuration (theme = "zola-pickles")
content/_index.md           page 1                       ->  /
content/page/_index.md      wrapper section, not rendered
content/page/2/_index.md    page 2                       ->  /page/2/
templates/index.html        overrides the theme home page: one list + prev/next nav
static/news.css             styling for the news list
scripts/import_news.py      regenerates all of content/ from news.md
themes/zola-pickles/        the pickles theme, v0.3.6
```

Everything under `content/` is generated -- don't edit it by hand.

### Why pagination is generated, not `paginate_by`

Zola's built-in paginator splits a section's *pages*, so using it would mean one
`.md` file, and one published URL, per story. This site shows the full summary
inline and links out to the source instead, so there is nothing for a per-story
page to hold. `import_news.py` therefore writes one section per page of ten and
puts the prev/next links in each section's `[extra]`, which
`templates/index.html` renders using the theme's own pagination markup.

Change `PER_PAGE` at the top of `scripts/import_news.py` to use a different page
size, then re-run the script.

## Updating the news

After the daily job refreshes `news.md`, regenerate the pages:

```sh
python3 scripts/import_news.py            # reads ../news.md
python3 scripts/import_news.py /path/to/news.md
```

It rebuilds `content/` from scratch, so pages that are no longer needed
disappear. The script refuses to write anything if a rating string somehow
survives.

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
