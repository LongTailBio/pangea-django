from django.contrib.auth import get_user_model
from django.db import models

from pangea.core.mixins import AutoCreatedUpdatedMixin

from .work_order_proto import WorkOrderProto


class PrivilegedUser(AutoCreatedUpdatedMixin):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    work_order_proto = models.ForeignKey(WorkOrderProto, on_delete=models.CASCADE, related_name='privileged_users')
