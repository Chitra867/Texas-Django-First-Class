from django.shortcuts import render
from.import models
def home(request):
    products = models.Product.objects.all()
    return render(request, 'home.html', {'products': products})

def about(request):

    return render(request, 'about.html',{})
def contact(request):

    return render(request, 'contact.html',{})

