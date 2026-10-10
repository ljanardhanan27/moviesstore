from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Avg
from .models import Movie, Review, Rating
from django.contrib.auth.decorators import login_required

def index(request):
    search_term = request.GET.get('search')
    if search_term:
        movies = Movie.objects.filter(name__icontains=search_term)
    else:
        movies = Movie.objects.all()

    template_data = {}
    template_data['title'] = 'Movies'
    template_data['movies'] = movies
    return render(request, 'movies/index.html', {'template_data': template_data})

def show(request, id):
    movie = get_object_or_404(Movie, id=id)
    reviews = Review.objects.filter(movie=movie, is_reported=False)
    ratings = Rating.objects.filter(movie=movie)
    average_rating = ratings.aggregate(average=Avg('value'))['average']
    user_rating = None
    if request.user.is_authenticated:
        user_rating = ratings.filter(user=request.user).first()

    template_data = {}
    template_data['title'] = movie.name
    template_data['movie'] = movie
    template_data['reviews'] = reviews
    template_data['average_rating'] = average_rating
    template_data['user_rating'] = user_rating
    return render(request, 'movies/show.html', {'template_data': template_data})

@login_required
def create_review(request, id):
    if request.method == 'POST' and request.POST.get('comment') != '':
        movie = Movie.objects.get(id=id)
        review = Review()
        review.comment = request.POST.get('comment')
        review.movie = movie
        review.user = request.user
        review.save()
        return redirect('movies.show', id=id)

    return redirect('movies.show', id=id)

@login_required
def edit_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user != review.user:
        return redirect('movies.show', id=id)

    if request.method == 'GET':
        template_data = {}
        template_data['title'] = 'Edit Review'
        template_data['review'] = review
        return render(request, 'movies/edit_review.html', {'template_data': template_data})
    elif request.method == 'POST' and request.POST['comment'] != '':
        review = Review.objects.get(id=review_id)
        review.comment = request.POST['comment']
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)

@login_required
def create_rating(request, id):
    if request.method != 'POST':
        return redirect('movies.show', id=id)

    try:
        value = int(request.POST.get('value'))
    except (TypeError, ValueError):
        return redirect('movies.show', id=id)

    if value < 1 or value > 5:
        return redirect('movies.show', id=id)

    movie = get_object_or_404(Movie, id=id)
    Rating.objects.update_or_create(
        movie=movie,
        user=request.user,
        defaults={'value': value}
    )
    return redirect('movies.show', id=id)

@login_required
def delete_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    return redirect('movies.show', id=id)

@login_required
def report_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user != review.user:
        review.is_reported = True
        review.save()

    return redirect('movies.show', id=id)