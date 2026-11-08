
"""Page Object da página inicial pública da loja."""

from playwright.sync_api import Page, expect


class HomePage:
    def __init__(self, page: Page):
        self.page = page

        # Seletores da página inicial
        self.logo = page.get_by_role(
            "link",
            name="ARENA WEAR",
            exact=True,
        )

        self.collection_link = page.get_by_role(
            "link",
            name="Coleção",
            exact=True,
        )

        self.hero_heading = page.get_by_role(
            "heading",
            name="VISTA SEU ESTILO.",
            exact=True,
        )

    def open(self, base_url: str):
        self.page.goto(base_url)
        return self

    def expect_loaded(self):
        expect(self.logo).to_be_visible()
        expect(self.collection_link).to_be_visible()
        expect(self.hero_heading).to_be_visible()

    def open_collection(self):
        self.collection_link.click()
