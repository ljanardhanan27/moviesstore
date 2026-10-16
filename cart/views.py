from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from movies.models import Movie
from .utils import calculate_cart_total
from .models import Order, Item
from django.contrib.auth.decorators import login_required

from datetime import timedelta

from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponseBadRequest
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .regions import REGIONS, REGION_CHOICES

def index(request):
    cart_total = 0
    movies_in_cart = []
    cart = request.session.get('cart', {})
    movie_ids = list(cart.keys())
    if (movie_ids != []):
        movies_in_cart = Movie.objects.filter(id__in=movie_ids)
        cart_total = calculate_cart_total(cart, movies_in_cart)

    template_data = {}
    template_data['title'] = 'Cart'
    template_data['movies_in_cart'] = movies_in_cart
    template_data['cart_total'] = cart_total
    template_data['regions'] = REGION_CHOICES
    return render(request, 'cart/index.html', {'template_data': template_data})

def add(request, id):
    get_object_or_404(Movie, id=id)
    cart = request.session.get('cart', {})
    cart[id] = request.POST['quantity']
    request.session['cart'] = cart
    return redirect('cart.index')

def clear(request):
    request.session['cart'] = {}
    return redirect('cart.index')

def add_to_cart(request, id):
    get_object_or_404(Movie, id=id)
    cart = request.session.get('cart', {})
    cart[id] = request.POST['quantity']
    request.session['cart'] = cart
    return redirect('cart.index')

@login_required
@require_POST
def purchase(request):
    cart = request.session.get('cart', {})

    if not cart:
        return redirect("cart.index")
    
    region = request.POST.get("region", "")

    if region not in REGIONS:
        return HttpResponseBadRequest("Please select a valid region")
    
    try:
        quantities = {
            int(movie_id): int(quantity)
            for movie_id, quantity in cart.items()
        }
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Invalid cart")
    

    if any(quantity < 1 or quantity > 90 for quantity in quantities.values()):
        return HttpResponseBadRequest(
            "Each movie quantity must be btween 1 and 90"
        )
    
    movies = list(Movie.objects.filter(id__in=quantities))

    if len(movies) != len(quantities):
        return HttpResponseBadRequest(
            "A movie in your cart is no longer available. Please clear the cart"
        )
    
    total = sum(
        movie.prices + quantities[movie.id]
        for movie in movies
    )

    with transaction.atomic():
        order = Order.objects.create(
            user=request.user,
            total = total,
            region=region,
        )
        

        Item.objects.bulk_create(
            Item(
                movie=movie,
                prices=movie.price,
                order=order,
                quantity = quantities[movie.id]
            )
            for movie in movies
        )

    request.session["cart"] = {}

    return render(
        request,
        "cart/purchase.html",
        {
            "template_data": {
                "title": "Purchase confirmation",
                "order_id": order.id,
            }
        },
    )


@login_required
def popularity_map(request):
    cutoff = timezone.now() - timedelta(days=30)

    purchases = (
        Item.objects
        .filter(
            order__date__gte=cutoff,
            order__region__in=REGIONS.keys(),
            quantity__gt=0,
        )
        .values("order__region", "movie_id", "movie__name")
        .annotate(purchase_count=Sum("quantity"))
        .order_by(
            "order__region",
            "-purchase_count",
            "movie__name",
            "movie_id",
        )
    )

    regions = {
        code: {
            "code": code,
            "name": region["name"],
            "lat": region["lat"],
            "lng": region["lng"],
            "total": 0,
            "movies": [],
        }
        for code, region in REGIONS.items()
    }

    for purchase in purchases:
        region = regions[purchase["order__region"]]
        region["total"] += purchase["purchase_count"]

        if len(region["movies"] < 5):
            region["movies"].append({
                "title": purchase["movie__name"],
                "count": purchase["purchase_count"],
                "url": reverse(
                    "movies.show",
                    args=[purchase["movie_id"]],
                ),
            })

    return render(
        request,
        "cart/popularity_map.html",
        {
            "template_data": {
                "title": "Local Popularity Map",
            },
            "regions": list(regions.values()),
        },
    )