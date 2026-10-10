from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Movie(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    price = models.IntegerField()
    description = models.TextField()
    image = models.ImageField(upload_to='movie_images/')
    def __str__(self):
        return str(self.id) + ' - ' + self.name

class Review(models.Model):
    id = models.AutoField(primary_key=True)
    comment = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    
    is_reported = models.BooleanField(default=False)
    
    movie = models.ForeignKey(Movie,
        on_delete=models.CASCADE)
    
    user = models.ForeignKey(User,
        on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.id} - {self.comment} - {self.review}'

class Rating(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['movie', 'user'],
                name='one_rating_per_user_per_movie'
            )
        ]

    def __str__(self):
        return f'{self.user.username} rated {self.movie.name}: {self.value}/5'