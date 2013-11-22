# -*- coding: utf-8 -*-
from django.views.generic import View, ListView, DetailView, FormView, TemplateView
from django.views.generic.edit import FormMixin
from django.views.generic.detail import SingleObjectMixin
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from .settings import PAGINATE_BY
from .models import Newsletter, NewsletterList
from .forms import SubscriptionForm, UnsubscribeForm, UnsubscribeAllForm


class NewsletterListView(ListView):
    model = Newsletter
    context_object_name = 'newsletters'
    template_name = 'courriers/newsletter_list.html'
    paginate_by = PAGINATE_BY

    @cached_property
    def newsletter_list(self):
        return get_object_or_404(NewsletterList, slug=self.kwargs.get('slug'))

    def get_queryset(self):
        if self.kwargs.get('lang'):
            return self.newsletter_list.newsletters \
                                       .status_online() \
                                       .filter(languages__contains=self.kwargs.get('lang')) \
                                       .order_by('published_at')
        return self.newsletter_list.newsletters.status_online().order_by('published_at')

    def get_context_data(self, **kwargs):
        context = super(NewsletterListView, self).get_context_data(**kwargs)
        context['newsletter_list'] = self.newsletter_list
        return context


class NewsletterDisplayView(DetailView):
    model = Newsletter
    context_object_name = 'newsletter'
    template_name = 'courriers/newsletter_detail.html'

    def get_context_data(self, **kwargs):
        context = super(NewsletterDisplayView, self).get_context_data(**kwargs)

        context['form'] = SubscriptionForm(user=self.request.user,
                                           newsletter_list=self.model.newsletter_list)

        if self.kwargs.get('action'):
            context['action'] = self.kwargs.get('action')

        return context


class NewsletterFormView(SingleObjectMixin, FormView):
    template_name = 'courriers/newsletter_detail.html'
    form_class = SubscriptionForm
    model = Newsletter
    context_object_name = 'newsletter'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(NewsletterFormView, self).post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(NewsletterFormView, self).get_context_data(**kwargs)
        context.update(SingleObjectMixin.get_context_data(self, **kwargs))
        return context

    def get_form_kwargs(self):
        return dict(super(NewsletterFormView, self).get_form_kwargs(), **{
            'newsletter_list': self.object.newsletter_list
        })

    def form_valid(self, form):
        if self.request.user.is_authenticated():
            form.save(self.request.user)
        else:
            form.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return self.object.get_absolute_url()


class NewsletterDetailView(View):
    def get(self, request, *args, **kwargs):
        view = NewsletterDisplayView.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = NewsletterFormView.as_view()
        return view(request, *args, **kwargs)


class NewsletterRawDetailView(DetailView):
    model = Newsletter
    template_name = 'courriers/newsletter_raw_detail.html'

    def get_context_data(self, **kwargs):
        context = super(NewsletterRawDetailView, self).get_context_data(**kwargs)

        context['items'] = self.object.items.all()

        return context


class NewsletterListUnsubscribeView(FormMixin, TemplateView):
    template_name = 'courriers/newsletter_list_unsubscribe.html'
    model = NewsletterList
    context_object_name = 'newsletter_list'

    def get_form_class(self):
        if not self.kwargs.get('slug', None):
            return UnsubscribeAllForm

        return UnsubscribeForm

    def get_initial(self):
        initial = super(NewsletterListUnsubscribeView, self).get_initial()
        email = self.request.GET.get('email', None)

        if email:
            initial['email'] = email

        return initial.copy()

    def get_form_kwargs(self):
        kwargs = super(NewsletterListUnsubscribeView, self).get_form_kwargs()

        if self.object:
            return dict(kwargs, **{
                'newsletter_list': self.object
            })

        return kwargs

    def get_context_data(self, **kwargs):
        context = super(NewsletterListUnsubscribeView, self).get_context_data(**kwargs)

        form_class = self.get_form_class()
        context['form'] = self.get_form(form_class)

        if self.object:
            context[self.context_object_name] = self.object

        return context

    @cached_property
    def object(self):
        slug = self.kwargs.get('slug', None)

        if slug:
            return get_object_or_404(self.model, slug=slug)

        return None

    def post(self, request, *args, **kwargs):
        self.get_context_data(**kwargs)

        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid():
            return self.form_valid(form)

        return self.form_invalid(form)

    def form_valid(self, form):
        form.save()

        return super(NewsletterListUnsubscribeView, self).form_valid(form)

    def get_success_url(self):
        if self.object:
            return reverse('newsletter_list_unsubscribe_done',
                           kwargs={'slug': self.object.slug})

        return reverse('newsletter_list_unsubscribe_done')


class NewsletterListUnsubscribeDoneView(TemplateView):
    template_name = "courriers/newsletter_list_unsubscribe_done.html"
    model = NewsletterList
    context_object_name = 'newsletter_list'

    def get_context_data(self, **kwargs):
        context = super(NewsletterListUnsubscribeDoneView, self).get_context_data(**kwargs)

        slug = self.kwargs.get('slug', None)

        if slug:
            context[self.context_object_name] = get_object_or_404(self.model, slug=slug)

        return context
