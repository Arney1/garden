# garden

my digital garden :P — a personal, evolving space for notes, ideas, and experiments. a place where pieces of knowledge intertwine, forming an interconnected web of information.

🌱 **Live site:** https://arney-garden.pages.dev

## Static website build

Logseq's public export is the source. A post-export build turns it into ordinary
HTML pages, with a dark sidebar, nested outlines, and an interactive graph view. Visitors do not download a
Logseq database, React, or WASM to read the garden.

```sh
./build-static.sh
python3 -m http.server 8000 --directory dist
```

Open http://localhost:8000. On **Cloudflare Pages**, use build command
`./build-static.sh` and output directory **`dist`**. For direct uploads, upload the
contents of `dist/`, not this repository's raw export.

After each **Export public pages** from Logseq, rebuild. The existing source export
and `patch-index.py` remain available; the loader patch is not needed for the
static version. Check `dist-report.json` for missing links or attachments already
absent from the source export.

The graph loads only at `/graph/`; notes also link to their local neighborhood.
The “a” logo is kept in `static-garden/branding/` so fresh Logseq exports do not
overwrite it in the built site.

The installed pre-commit hook validates the staged export without patching,
compressing, or staging files. On a new clone, run `./install-hooks.sh`.

See [the converter guide](static-garden/README.md) for setup, customization, tests,
supported features, and limitations. Configure the homepage, navigation, and
canonical domain in [site.json](static-garden/site.json).

## About this project

This is a personal digital garden, so content and structure may change over time as ideas grow.

> *"How can I know what I think till I see what I say?"*  
> — **E.M. Forster**, *Aspects of the Novel*

## Writeups & CTF notes

This garden also contains writeups and CTF notes (for example, descriptions of exploitation types, techniques, and walkthroughs). I don't currently maintain a separate writeup repository — these notes live here in the digital garden. Only writeups that are allowed to be publicized are included.
