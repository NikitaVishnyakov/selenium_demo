import random
from faker import Faker

fake = Faker()


def make_pet(status: str = "available") -> dict:
    return {
        "id": random.randint(10 ** 8, 10 ** 9),
        "name": fake.first_name(),
        "status": status,
        "category": {"id": 1, "name": "dogs"},
        "photoUrls": [fake.image_url()],
        "tags": [{"id": 1, "name": fake.word()}],
    }