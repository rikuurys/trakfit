from django.shortcuts import render

# Create your views here.

def login(request):
    return render(request, 'login.html')

def logout(request):
    return render(request, 'login.html')

def register(request):
    return render(request, 'register.html')

def resetPassword(request):
    return render(request, 'resetPassword.html')