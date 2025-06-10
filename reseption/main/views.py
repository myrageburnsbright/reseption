from django.shortcuts import render

# Create your views here.
def index(request):
    context = {}

    return render(request, 'main/index.html', context=context)

def katalog(request):
    context = {}

    return render(request, 'main/katalog.html', context=context)