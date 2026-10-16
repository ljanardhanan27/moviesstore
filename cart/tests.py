from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from movies.models import Movie
from .models import Item, Order


class PopularityMapTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="buyer", password="test-password")
        cls.other = User.objects.create_user(username="other")
        cls.movie = Movie.objects.create(name="Movie A", price=10, description="A")
        cls.second = Movie.objects.create(name="Movie B", price=7, description="B")

    def setUp(self):
        self.client.force_login(self.user)

    def cart(self, quantity="2", movie_id=None):
        session = self.client.session
        session["cart"] = {str(movie_id or self.movie.id): quantity}
        session.save()

    def buy(self, movie, quantity, region="atlanta", user=None, days=0):
        order = Order.objects.create(user=user or self.user, region=region, total=movie.price * quantity)
        Item.objects.create(order=order, movie=movie, quantity=quantity, price=movie.price)
        if days:
            Order.objects.filter(pk=order.pk).update(date=timezone.now() - timedelta(days=days))
        return order

    def test_cart_renders_region_form_and_navigation(self):
        self.cart()
        response = self.client.get(reverse("cart.index"))
        self.assertContains(response, 'name="region"')
        self.assertContains(response, 'value="atlanta"')
        self.assertContains(response, reverse("cart.popularity_map"))
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_purchase_saves_region_total_and_quantity(self):
        self.cart()
        response = self.client.post(reverse("cart.purchase"), {"region": "atlanta"})
        self.assertEqual(response.status_code, 200)
        order = Order.objects.get()
        self.assertEqual((order.region, order.total, order.user), ("atlanta", 20, self.user))
        item = Item.objects.get()
        self.assertEqual((item.quantity, item.price), (2, 10))
        self.assertEqual(self.client.session["cart"], {})

    def test_invalid_region_or_quantity_creates_no_order(self):
        for quantity, region in [("2", "invalid"), ("0", "atlanta"), ("-1", "atlanta"), ("91", "atlanta"), ("abc", "atlanta")]:
            with self.subTest(quantity=quantity, region=region):
                self.cart(quantity)
                response = self.client.post(reverse("cart.purchase"), {"region": region})
                self.assertEqual(response.status_code, 400)
                self.assertFalse(Order.objects.exists())

    def test_missing_movie_creates_no_order(self):
        self.cart(movie_id=99999)
        response = self.client.post(reverse("cart.purchase"), {"region": "atlanta"})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.exists())

    def test_purchase_requires_post(self):
        self.assertEqual(self.client.get(reverse("cart.purchase")).status_code, 405)

    def test_empty_cart_redirects(self):
        response = self.client.post(reverse("cart.purchase"), {"region": "atlanta"})
        self.assertRedirects(response, reverse("cart.index"))

    def test_failed_items_roll_back_order_and_preserve_cart(self):
        self.cart()
        with patch("cart.views.Item.objects.bulk_create", side_effect=IntegrityError):
            with self.assertRaises(IntegrityError):
                self.client.post(reverse("cart.purchase"), {"region": "atlanta"})
        self.assertFalse(Order.objects.exists())
        self.assertTrue(self.client.session["cart"])

    def test_login_required(self):
        self.client.logout()
        for name in ["cart.popularity_map", "cart.purchase"]:
            response = self.client.get(reverse(name))
            self.assertRedirects(response, reverse("accounts.login") + "?next=" + reverse(name))

    def test_rankings_sum_copies_and_exclude_old_unassigned_orders(self):
        self.buy(self.movie, 2)
        self.buy(self.movie, 1, user=self.other)
        self.buy(self.second, 1)
        self.buy(self.second, 2, region="chicago")
        self.buy(self.second, 50, days=31)
        self.buy(self.second, 50, region="")
        response = self.client.get(reverse("cart.popularity_map"))
        self.assertEqual(response.status_code, 200)
        regions = {region["code"]: region for region in response.context["regions"]}
        self.assertEqual(regions["atlanta"]["total"], 4)
        self.assertEqual([(m["title"], m["count"]) for m in regions["atlanta"]["movies"]], [("Movie A", 3), ("Movie B", 1)])
        self.assertEqual(regions["chicago"]["total"], 2)
        self.assertEqual(regions["houston"]["movies"], [])

    def test_top_five_keeps_total_for_all_movies(self):
        for number in range(6):
            movie = Movie.objects.create(name=f"Movie {number}", price=1)
            self.buy(movie, number + 1)
        response = self.client.get(reverse("cart.popularity_map"))
        atlanta = next(r for r in response.context["regions"] if r["code"] == "atlanta")
        self.assertEqual(atlanta["total"], 21)
        self.assertEqual([m["count"] for m in atlanta["movies"]], [6, 5, 4, 3, 2])

    def test_empty_map_renders(self):
        response = self.client.get(reverse("cart.popularity_map"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(all(r["total"] == 0 for r in response.context["regions"]))
