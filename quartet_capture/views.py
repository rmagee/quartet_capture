# -*- coding: utf-8 -*-
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    UpdateView,
    ListView
)

from .models import (
	message,
)


class messageCreateView(CreateView):

    model = message


class messageDeleteView(DeleteView):

    model = message


class messageDetailView(DetailView):

    model = message


class messageUpdateView(UpdateView):

    model = message


class messageListView(ListView):

    model = message

