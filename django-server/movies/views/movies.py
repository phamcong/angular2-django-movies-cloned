from django.http import JsonResponse
from django.db.models import Avg, Count, Func
from ..models import Movie, Rating, Comment


def new_movie(request):
    if request.method != 'POST':
        pass

    # get movie id and title
    id = request.POST.get('id', '')
    title = request.POST.get('title', '')

    # save new movie
    m = Movie(source_id = id, title = title)
    try:
        m.save()
    except Exception as e:
        return JsonResponse({
            'status': 'fail',
            'data': {
                'message': str(e) if type(e) == ValueError else 'Error while saving movie'
            }
        }, status=500)

    return JsonResponse({
        'status': 'success',
        'data': {
            'title': m.title
        }
    })


def movie_details(request, movie_id):
    if request.method != 'GET':
        pass

    # get movie
    try:
        m = Movie.objects.get(source_id=movie_id)
    except Movie.DoesNotExist:
        return JsonResponse({
            'status': 'success',
            'data': {
                'rating': {
                    'avg': None,
                    'comments': None
                }
            }
        })

    # get rating
    r = Rating.objects.filter(movie=m)\
        .values('rating')\
        .aggregate(
            avg_rating=Avg('rating'),
            rating_count=Count('rating')
        )
    avg_rating = r['avg_rating']
    rating_count = r['rating_count']

    # get comments
    c = Comment.objects.filter(movie=m).values('body', 'username')

    return JsonResponse({
        'status': 'success',
        'data': {
            'rating': {
                'avg': '{:.1f}'.format(avg_rating) if avg_rating is not None else None,
                'count': rating_count
            },
            'comments': list(c)
        }
    })

class Round(Func):
    function = 'ROUND'
    template='%(function)s(%(expressions)s, 1)'

def movies_summary(request):
    if request.method != 'GET':
        pass

    # get all requested movie ids
    movie_ids = request.GET.get('ids', '').split(',')

    m = Movie.objects.filter(source_id__in=movie_ids).annotate(
        avg_rating=Round(Avg('rating__rating')), # avg on rating column of rating table
        comment_count=Count('comment', distinct=True)
    ).values()

    movies = {}
    for movie in list(m):
        movies[movie.get('source_id')] = movie

    return JsonResponse({
        'status': 'success',
        'data': {
            'movies': movies
        }
    })
