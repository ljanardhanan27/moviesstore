from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from django.contrib.auth.models import User

from cart.models import Item

@staff_member_required
def top_buyers(request):
    buyers = (
        User.objects.annotate(
            movies_purchased=Sum('order__item__quantity'),
            orders_placed=Count('order', distinct=True),
        )
        .filter(movies_purchased__gt=0)
        .order_by('-movies_purchased', 'username')
        .values('id', 'username', 'movies_purchased', 'orders_placed')
    )

    top_buyer = buyers[0] if buyers else None
    top_buyer_items = []
    tied_with_top = 0

    if top_buyer is not None:
        top_buyer_items = (
            Item.objects
            .filter(order__user_id=top_buyer['id'])
            .values('movie__name')
            .annotate(quantity=Sum('quantity')) # total copies per movie
            .order_by('-quantity', 'movie__name')
        )
        # In case of a tie with top buyers
        tied_with_top = sum(
            1 for b in buyers if b['movies_purchased'] == top_buyer['movies_purchased']
        ) - 1

    template_data = {
        'title': 'Top Buyers',
        'buyers': buyers,
        'top_buyer': top_buyer,
        'top_buyer_items': top_buyer_items,
        'tied_with_top': tied_with_top,
    }
    return render(request, 'dashboard/top_buyers.html', {'template_data': template_data})