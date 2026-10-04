from django.shortcuts import render

def index(request):
    return render(request, 'index.html')


def sobre(request):
    return render(request, "sobre.html")

# views.py
def pq_usar(request):
    return render(request, "pq_usar.html")