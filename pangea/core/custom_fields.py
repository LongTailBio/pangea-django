from django.db.models import BooleanField


class AtMostOneBooleanField(BooleanField):

    def pre_save(self, model_instance, add):
        objects = model_instance.__class__.objects
        # If True then set all others as False
        if getattr(model_instance, self.attname):
            objects.update(**{self.attname: False})
        return getattr(model_instance, self.attname)
