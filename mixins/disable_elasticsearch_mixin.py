from django.db.models.signals import post_save


class DisableSignalMixin:
    model = None
    signal = post_save
    receiver = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if cls.model and cls.receiver:
            cls.signal.disconnect(cls.receiver, sender=cls.model)

    @classmethod
    def tearDownClass(cls):
        if cls.model and cls.receiver:
            cls.signal.connect(cls.receiver, sender=cls.model)
        super().tearDownClass()
