
"""Auditorias automatizadas Axe-core e navegação por teclado."""

import os

import pytest
from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import expect


BASE_URL = os.getenv(
    "E2E_BASE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

pytestmark = [
    pytest.mark.accessibility,
    pytest.mark.usefixtures("live_server"),
]


@pytest.mark.parametrize("path", ["/", "/products.html"])
def test_wcag_21_aa_with_axe(page, path):
    # Arrange
    page.goto(f"{BASE_URL}{path}")

    # Act
    results = Axe().run(
        page,
        options={
            "runOnly": {
                "type": "tag",
                "values": [
                    "wcag2a",
                    "wcag2aa",
                    "wcag21a",
                    "wcag21aa",
                ],
            }
        },
    )

    # Assert
    if isinstance(results, dict):
        violations = results.get("violations", [])
    elif hasattr(results, "response"):
        violations = results.response.get("violations", [])
    elif hasattr(results, "violations"):
        violations = results.violations
    else:
        raise AssertionError(
            "Formato inesperado retornado pelo Axe-core."
        )

    assert not violations, (
        f"Violações WCAG 2.1 AA encontradas em {path}: "
        f"{violations}"
    )


def test_homepage_keyboard_navigation_reaches_logo(page):
    # Arrange
    page.goto(BASE_URL)

    logo = page.locator("header a.logo").first

    # Confirma que o logo existe na página.
    expect(logo).to_be_visible()

    # Act: navega pelos elementos usando somente a tecla Tab.
    logo_reached = False

    for _ in range(30):
        page.keyboard.press("Tab")

        is_logo_focused = page.evaluate(
            """() => {
                const focused = document.activeElement;
                return focused?.matches("header a.logo") ?? false;
            }"""
        )

        if is_logo_focused:
            logo_reached = True
            break

    # Assert
    assert logo_reached, (
        "O logo da loja não foi alcançado pela navegação "
        "por teclado usando Tab."
    )

    expect(logo).to_be_focused()
