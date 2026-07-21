from django.shortcuts import render


def Home(request):
    return render(request, 'base.html' )


def contact_view(request):
    return render(request, 'contact.html')    