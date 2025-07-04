from .models import Category

def categories_context(request):
    """
    Context processor to make categories available in all templates
    """
    return {
        'nav_categories': Category.objects.all().order_by('order', 'name')
    }
