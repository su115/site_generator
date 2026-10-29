from __future__ import annotations

import typer

from sitegen.core.cli_core3 import Controller

app = typer.Typer(
    name="sitegen",
    help=(
        "🚀 SiteGen — block-based static site generator\n\n"
        "A deterministic build system for multi-language websites.\n\n"
        "Each site is defined as a JSON block graph and rendered into static HTML.\n"
    ),
    add_completion=True,
    rich_markup_mode="rich",
)


def get_sites() -> list[dict[str, str]]:
    cont = Controller().load_config()
    return cont.sites


def complete_site(incomplete: str) -> list[str]:
    sites = [k["site_name"] for k in get_sites()]
    return [site for site in sites if site.startswith(incomplete)]


def complete_lang(ctx: typer.Context, incomplete: str) -> list[str]:
    site = ctx.params.get("site")

    langs = [k["lang"] for k in get_sites() if k["site_name"] == site]
    return [lang for lang in langs if lang.startswith(incomplete)]


@app.command(help="List available sites")
def sites() -> None:  # pragma: no cover
    result: dict[str, list[str]] = {}
    for item in get_sites():
        if item["site_name"] not in result:
            result[item["site_name"]] = []
        result[item["site_name"]].append(item["lang"])

    for site_name, langs in result.items():
        print(f"{str(site_name).ljust(30)} {langs}")


@app.command(help="Validate all blocks and build final static HTML site")
def build(
    site: str = typer.Argument(..., autocompletion=complete_site),
    lang: str = typer.Argument(..., autocompletion=complete_lang),
) -> None:
    Controller().load_config().build(site_name=site, lang=lang)
    print("Building ...")


@app.command(
    help=("Full rebuild of all sites.\nRuns full pipeline for each site:\n  clean → split → validate → build\nUseful for CI/CD or full regeneration.")
)
def regenerate() -> None:
    print("Regenerating...")
    Controller().load_config().regenerate()


@app.command(help=("Initialize basic framewaork files."))
def init() -> None:
    print("Initializing...")
    Controller().initialize_skeleton()


if __name__ == "__main__":  # pragma: no cover
    app()
