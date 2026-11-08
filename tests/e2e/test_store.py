
"""Fluxos E2E reais no navegador da loja."""

import os

import pytest
from playwright.sync_api import expect

from tests.e2e.pages.home_page import HomePage


pytestmark = [
    pytest.mark.e2e,
    pytest.mark.usefixtures("live_server"),
]

BASE_URL = os.getenv(
    "E2E_BASE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


def test_homepage_and_navigation_to_collection(page):
    # Arrange
    home = HomePage(page).open(BASE_URL)

    # Act
    home.expect_loaded()
    home.open_collection()

    # Assert
    expect(page).to_have_url(f"{BASE_URL}/products.html")
    expect(
        page.get_by_role(
            "heading",
            name="A coleção.",
            exact=True,
        )
    ).to_be_visible()


def test_catalog_search_field_is_available(page):
    # Arrange
    page.goto(f"{BASE_URL}/products.html")

    # Assert
    expect(
        page.get_by_placeholder("Buscar produtos...")
    ).to_be_visible()

    expect(
        page.locator("#category")
    ).to_be_visible()
