import factory
from communications.models import NotificationType


class NotificationTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NotificationType

    code = factory.Sequence(lambda n: f"test_type_{n}")
    name = factory.LazyAttribute(lambda o: f"Test Type {o.code.split('_')[-1]}")
    description = "Test Description"
    default_frequency = 'immediate'
    is_active = True
