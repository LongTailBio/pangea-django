import os
import datetime
import requests
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from pangea.core.encrypted_fields import EncryptedString
from pangea.core.models import (
    PangeaUser,
    Organization,
    Sample,
    Pipeline,
    PipelineModule,
    WorkOrder,
    WorkOrderProto,
    JobOrder,
    JobOrderProto,
    PrivilegedUser,
)

from .constants import (
    UPLOAD_TEST_FILENAME,
    UPLOAD_TEST_FILEPATH,
)


class WorkOrderTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(name='Test Organization')
        cls.user = PangeaUser.objects.create(email='user@domain.com', password='Foobar22')
        cls.group = cls.organization.create_sample_group(name='GRP_01', is_library=True)
        cls.sample = cls.group.create_sample(name='SMPL_01')

    def test_create_work_order(self):
        wop = WorkOrderProto.objects.create(name='test work order')
        url = reverse(
            'sample-create-workorder',
            kwargs={'sample_pk': self.sample.pk, 'wop_pk': wop.pk}
        )
        self.organization.users.add(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['uuid'])
        self.assertTrue(WorkOrder.objects.exists())

    def test_modify_job_order(self):
        wop = WorkOrderProto.objects.create(name='test work order')
        jop = JobOrderProto.objects.create(name='test job order', work_order_proto=wop)
        wo = wop.work_order(self.sample)
        jo = wo.jobs.get()
        self.assertEqual(jo.name, jop.name)
        PrivilegedUser.objects.create(user=self.user, work_order_proto=wop)
        self.client.force_authenticate(user=self.user)
        url = reverse('job-order-detail', kwargs={'pk': jo.pk})
        response = self.client.patch(url, {'name': 'new name'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        jo = wo.jobs.get()
        self.assertEqual(jo.name, 'new name')

    def test_non_privileged_cannot_modify_job_order(self):
        wop = WorkOrderProto.objects.create(name='test work order')
        jop = JobOrderProto.objects.create(name='test job order', work_order_proto=wop)
        wo = wop.work_order(self.sample)
        jo = wo.jobs.get()
        self.assertEqual(jo.name, jop.name)
        self.client.force_authenticate(user=self.user)
        url = reverse('job-order-detail', kwargs={'pk': jo.pk})
        response = self.client.patch(url, {'name': 'new name'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_work_order_protos(self):
        wop = WorkOrderProto.objects.create(name='test work order')
        url = reverse('work-order-proto-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_list_job_order_protos(self):
        wop = WorkOrderProto.objects.create(name='test work order')
        JobOrderProto.objects.create(
            name='test job order',
            work_order_proto=wop,
        )
        url = reverse('job-order-proto-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_work_order_proto_detail(self):
        wop = WorkOrderProto.objects.create(name='test work order')
        url = reverse('work-order-proto-detail', kwargs={'pk': wop.pk})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['uuid'], str(wop.uuid))

    def test_get_work_order_detail(self):
        wop = WorkOrderProto.objects.create(name='test work order')
        wo = wop.work_order(self.sample)
        url = reverse('work-order-detail', kwargs={'pk': wo.pk})
        self.organization.users.add(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['uuid'], str(wo.uuid))

    def test_get_work_order_detail_extended(self):
        wop = WorkOrderProto.objects.create(name='test work order')
        jop = JobOrderProto.objects.create(
            name='test job order',
            work_order_proto=wop,
        )
        wo = wop.work_order(self.sample)
        url = reverse('work-order-detail', kwargs={'pk': wo.pk})
        self.organization.users.add(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['uuid'], str(wo.uuid))
        self.assertEqual(response.data['status'], 'pending')
        self.assertEqual(len(response.data['job_order_objs']), 1)

    def test_get_work_order_detail_unauth(self):
        wop = WorkOrderProto.objects.create(name='test work order')
        wo = wop.work_order(self.sample)
        url = reverse('work-order-detail', kwargs={'pk': wo.pk})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_work_order_in_sample(self):
        wop = WorkOrderProto.objects.create(name='test work order')
        wo = wop.work_order(self.sample)
        url = reverse('sample-list-workorder', kwargs={'sample_pk': self.sample.pk})
        self.organization.users.add(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['uuid'], str(wo.uuid))

    def test_get_job_order_proto_detail(self):
        wop = WorkOrderProto.objects.create(name='test work order')
        jop = JobOrderProto.objects.create(
            name='test job order',
            work_order_proto=wop,
        )
        url = reverse('job-order-proto-detail', kwargs={'pk': jop.pk})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['uuid'], str(jop.uuid))

    def test_get_job_order_detail_unauth(self):
        wop = WorkOrderProto.objects.create(name='test work order')
        jop = JobOrderProto.objects.create(name='test job order', work_order_proto=wop)
        wo = wop.work_order(self.sample)
        jo = wo.jobs.get()
        url = reverse('job-order-detail', kwargs={'pk': jo.pk})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_job_order_detail(self):
        wop = WorkOrderProto.objects.create(name='test work order')
        jop = JobOrderProto.objects.create(name='test job order', work_order_proto=wop)
        wo = wop.work_order(self.sample)
        jo = wo.jobs.get()
        url = reverse('job-order-detail', kwargs={'pk': jo.pk})
        self.organization.users.add(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['uuid'], str(jo.uuid))
