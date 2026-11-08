"""Factory de dados sintéticos para os testes NORTHMEN."""
from faker import Faker

fake = Faker("pt_BR")


class ProductFactory:
    """Gera payloads de produtos válidos para a API administrativa."""

    @staticmethod
    def build(**overrides):
        data = {
            "name": f"Camiseta {fake.color_name()} {fake.word()}",
            "category": "Camisetas",
            "description": fake.sentence(),
            "price": round(fake.pyfloat(min_value=49, max_value=250, right_digits=2), 2),
            "cost": round(fake.pyfloat(min_value=15, max_value=100, right_digits=2), 2),
            "image": "campaign-look.jpg",
        }
        data.update(overrides)
        return data
