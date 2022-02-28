from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

from .models import Room, Topic
from .forms import RoomForm
# Create your views here.


def login_user(request: HttpRequest) -> HttpResponse:
    flow = 'login'

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            User.objects.get(username=username)
        except:
            messages.error(request, 'User does not exist')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            return redirect('home')
        else:
            messages.error(request, 'Username or password does not exist')

    context = {
        'flow': flow
    }

    return render(request, 'base/login_register.html', context)


def logout_user(request: HttpRequest) -> HttpResponse:
    logout(request)

    return redirect('home')


def register_user(request: HttpRequest) -> HttpResponse:
    form = UserCreationForm()
    context = {
        'form': form
    }

    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.username.lower()
            user.save()
            login(request, user)

            return redirect('home')
        else:
            messages.error(request, 'Failed to register user')

    return render(request, 'base/login_register.html', context)


def home(request: HttpRequest) -> HttpResponse:
    query = request.GET.get('q', None)
    context = {
        'topics': Topic.objects.all(),
    }

    if query is None:
        context['rooms'] = Room.objects.all()
    else:
        context['rooms'] = Room.objects.filter(
            Q(topic__name__icontains=query) |
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    context['room_count'] = context['rooms'].count()

    return render(request, 'base/home.html', context)


def room(request: HttpRequest, pk: int) -> HttpResponse:
    found_room = Room.objects.get(id=pk)

    return render(request, 'base/room.html', {'room': found_room})


@login_required(login_url='/login')
def create_room(request: HttpRequest) -> HttpResponse:
    form = RoomForm()

    if request.method == 'POST':
        form = RoomForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect('home')

    return render(request, 'base/room_form.html', {'form': form})


@login_required(login_url='/login')
def update_room(request: HttpRequest, pk: int) -> HttpResponse:
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)

    if request.user != room.host:
        return HttpResponse('Only host can update a room')

    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)

        if form.is_valid():
            form.save()

            return redirect('home')

    return render(request, 'base/room_form.html', {'form': form})


@login_required(login_url='/login')
def delete_room(request: HttpRequest, pk: int) -> HttpResponse:
    room = Room.objects.get(id=pk)

    if request.method == 'POST':
        room.delete()

        return redirect('home')

    return render(request, 'base/delete.html', {'obj': room})
