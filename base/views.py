from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .models import User, Message, Room, Topic
from .forms import RoomForm, UserForm, UserRegistrationForm


def login_user(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        try:
            user = authenticate(request, email=email, password=password)
        except:
            messages.error(request, 'User does not exist')

        if user is not None:
            login(request, user)

            return redirect('home')
        else:
            messages.error(request, 'Username or password does not exist')

    return render(request, 'base/login.html')


def logout_user(request: HttpRequest) -> HttpResponse:
    logout(request)

    return redirect('home')


def register_user(request: HttpRequest) -> HttpResponse:
    form = UserRegistrationForm()
    context = {
        'form': form
    }

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.username.lower()
            user.save()
            login(request, user)

            return redirect('home')
        else:
            messages.error(request, 'Failed to register user')

    return render(request, 'base/register.html', context)


def home(request: HttpRequest) -> HttpResponse:
    query = request.GET.get('q', None)
    context = {
        'topics': Topic.objects.all(),
    }

    if query is None:
        context['rooms'] = Room.objects.all()
        context['room_messages'] = Message.objects.all()
    else:
        context['rooms'] = Room.objects.filter(
            Q(topic__name__icontains=query) |
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )
        context['room_messages'] = Message.objects.filter(
            Q(room__topic__name__icontains=query))

    context['room_count'] = context['rooms'].count()

    return render(request, 'base/home.html', context)


def room(request: HttpRequest, pk: int) -> HttpResponse:
    found_room = Room.objects.get(id=pk)
    room_messages = found_room.message_set.all().order_by('-created')
    participants = found_room.participants.all()
    context = {
        'room': found_room,
        'room_messages': room_messages,
        'participants': participants,
    }

    if request.method == 'POST':
        message = Message.objects.create(
            user=request.user,
            room=found_room,
            body=request.POST.get('body')
        )
        found_room.participants.add(request.user)

        return redirect('room', pk=found_room.id)

    return render(request, 'base/room.html', context)


def user_profile(request: HttpRequest, pk: int) -> HttpResponse:
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {
        'user': user,
        'rooms': rooms,
        'room_messages': room_messages,
        'topics': topics,
    }

    return render(request, 'base/user_profile.html', context)


@login_required(login_url='login')
def update_user(request: HttpRequest) -> HttpResponse:
    user = request.user
    form = UserForm(instance=user)
    context = {
        'form': form,
    }

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)

        if form.is_valid():
            form.save()

            return redirect('user-profile', pk=request.user.id)

    return render(request, 'base/update-user.html', context)


@login_required(login_url='login')
def create_room(request: HttpRequest) -> HttpResponse:
    form = RoomForm()
    topics = Topic.objects.all()
    context = {
        'form': form,
        'topics': topics,
    }

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )

        # form = RoomForm(request.POST)

        # if form.is_valid():
        #     room = form.save(commit=False)
        #     room.host = request.user
        #     room.save()

        return redirect('home')

    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def update_room(request: HttpRequest, pk: int) -> HttpResponse:
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()
    context = {
        'room': room,
        'form': form,
        'topics': topics,
    }

    if request.user != room.host:
        return HttpResponse('Only host can update a room')

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()

        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )

        return redirect('home')

    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def delete_room(request: HttpRequest, pk: int) -> HttpResponse:
    room = Room.objects.get(id=pk)

    if request.method == 'POST':
        room.delete()

        return redirect('home')

    return render(request, 'base/delete.html', {'obj': room})


@login_required(login_url='login')
def delete_message(request: HttpRequest, pk: int) -> HttpResponse:
    message = Message.objects.get(id=pk)

    if request.user != message.user:
        return HttpResponse('You are not allowed to delete')

    if request.method == 'POST':
        message.delete()

        return redirect('home')

    return render(request, 'base/delete.html', {'obj': message})
