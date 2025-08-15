from django.test import TestCase

class FastAPITestCase(TestCase):

    def test_hello(self):
        response = self.client.get("/api/fastapi/hello")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Hello from FastAPI"})

    def test_healthcheck(self):
        response = self.client.get("/api/fastapi/healthcheck")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
