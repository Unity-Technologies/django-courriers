from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils import timezone as datetime

from courriers.forms import SubscriptionForm
from courriers.models import Newsletter, NewsletterSubscriber
from courriers.backends import backend



class BackendsTest(TestCase):

    def setUp(self):
        self.backend = backend()

    def test_registration(self):

        # Subscribe

        self.backend.register('adele@ulule.com')

        subscriber = NewsletterSubscriber.objects.filter(email='adele@ulule.com', is_unsubscribed=False)

        self.assertEqual(subscriber.count(), 1)


        # Unsubscribe

        subscriber = NewsletterSubscriber.objects.get(email='adele@ulule.com')

        self.backend.unregister(subscriber.email)

        unsubscriber = NewsletterSubscriber.objects.filter(email='adele@ulule.com', is_unsubscribed=True)

        self.assertEqual(unsubscriber.count(), 1)



class NewslettersViewsTests(TestCase):

    def setUp(self):
        Newsletter.objects.create(name='Newsletter1', published_at=datetime.now())

    def test_newsletter_list(self):
        response = self.client.get(reverse('newsletter_list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courriers/newsletter_list.html')

    def test_newsletter_detail(self):
        response = self.client.get(reverse('newsletter_detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courriers/newsletter_detail.html')

        self.failUnless(isinstance(response.context['form'], SubscriptionForm))

    def test_newsletterraw_detail(self):
        response = self.client.get(reverse('newsletterraw_detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courriers/newsletterraw_detail.html')



class SubscribeFormTest(TestCase):

    def test_subscription_logged_out(self):
        valid_data = {'receiver': 'adele@ulule.com'}

        form = SubscriptionForm(data=valid_data)

        self.failUnless(form.is_valid())

        form.save()

        new_subscriber = NewsletterSubscriber.objects.filter(email=valid_data['receiver'])

        self.assertEqual(new_subscriber.count(), 1)


        # Test duplicate

        form2 = SubscriptionForm(data=valid_data)

        is_valid = form2.is_valid()

        self.assertEqual(is_valid, False)

    def test_subscription_logged_in(self):
        self.client.login(username='thoas', password='secret')

        valid_data = {'receiver': 'florent@ulule.com'}

        form = SubscriptionForm(data=valid_data)

        self.failUnless(form.is_valid())

        user = User.objects.create(username='thoas')

        form.save(user)

        new_subscriber = NewsletterSubscriber.objects.filter(email=valid_data['receiver'], user=user)

        self.assertEqual(new_subscriber.count(), 1)



class NewsletterModelsTest(TestCase):

    def test_navigation(self):
        n1 = Newsletter.objects.create(name='Newsletter1', status=1, published_at=datetime.now() - datetime.timedelta(hours=3))
        n2 = Newsletter.objects.create(name='Newsletter2', status=1, published_at=datetime.now() - datetime.timedelta(hours=2))
        n3 = Newsletter.objects.create(name='Newsletter3', status=1, published_at=datetime.now() - datetime.timedelta(hours=1))

        prev = n2.prev()
        self.assertEqual(prev, n1)

        next = n2.next()
        self.assertEqual(next, n3)