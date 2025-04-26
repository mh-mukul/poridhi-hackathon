from locust import HttpUser, task, between
import random


def get_random_query():
    queries = [
        "cheap air jordan",
        "best running shoes",
        "latest smartphone",
        "gaming laptop deals",
        "wireless headphones",
        "smartwatch for fitness",
        "4K TV discounts",
        "home office furniture",
        "kitchen appliances sale",
        "outdoor gear clearance"
    ]
    return random.choice(queries)


class APILoadTest(HttpUser):
    wait_time = between(1, 2)  # Wait between 1 and 2 seconds between requests

    @task
    def search_products(self):
        headers = {
            "Authorization": "997gJaBqJtFYkVaqIlz-jH1ZpxMOOmvRvr66lQJ8jD8",
            "Content-Type": "application/json"
        }
        payload = {
            "collection_name": "products",
            "query": get_random_query(),
            "limit": 10
        }
        self.client.post(
            "/api/v1/search",
            json=payload,
            headers=headers,
            name="Search Products"
        )

    def on_start(self):
        print("Starting user simulation...")
