"""Test suite for Sample model."""
import os
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import (
    Tag,
)

from pangea.core.models import (
    PangeaUser,
    Organization,
    SampleGroup,
    Sample,
)


class TagModelTests(TestCase):
    """Test suite for Sample model."""

    def test_add_tag(self):
        tag = Tag.objects.create(name='mytag YUDFS')

        self.assertTrue(tag.uuid)
        self.assertEqual(tag.name, 'mytag YUDFS')
        self.assertTrue(tag.created_at)

    def test_add_tag_with_payload(self):
        tag = Tag.objects.create(name='mytag YJTUYDS', payload='FOO')

        self.assertTrue(tag.uuid)
        self.assertEqual(tag.name, 'mytag YJTUYDS')
        self.assertEqual(tag.payload, 'FOO')
        self.assertTrue(tag.created_at)

    def test_relate_tag_pair(self):
        tag1 = Tag.objects.create(name='tag1 TFDKSG')
        tag2 = Tag.objects.create(name='tag2 TFDKSG')
        tag2.add_related_tag(tag1)
        self.assertEqual(tag2.related_tags.get().other_tag, tag1)

    def test_relate_tag_triple(self):
        tag1 = Tag.objects.create(name='tag1 HJFJUS')
        tag2 = Tag.objects.create(name='tag2 HJFJUS')
        tag3 = Tag.objects.create(name='tag3 HJFJUS')
        tag2.add_related_tag(tag1)
        tag3.add_related_tag(tag2)
        tag1.add_related_tag(tag3)
        self.assertEqual(tag2.related_tags.get().other_tag, tag1)
        self.assertEqual(tag3.related_tags.get().other_tag, tag2)
        self.assertEqual(tag1.related_tags.get().other_tag, tag3)

    def test_tag_sample_group(self):
        """Ensure we can tag a sample group."""
        org = Organization.objects.create(name='org ADUJABF')
        grp = org.create_sample_group(name='GRP ADUJABF')
        tag = Tag.objects.create(name='tag ADUJABF')
        tag.tag_sample_group(grp)
        self.assertEqual(grp.tags.get().tag, tag)
        self.assertEqual(tag.tagged_sample_groups.get().sample_group, grp)

    def test_tag_sample(self):
        """Ensure we can tag a sample group."""
        org = Organization.objects.create(name='org AUHFVJKELF')
        lib = org.create_sample_group(name='LBRY_01 AUHFVJKELF', is_library=True)
        sample = lib.create_sample(name='SMPL_01 AUHFVJKELF')
        tag = Tag.objects.create(name='tag AUHFVJKELF')
        tag.tag_sample(sample)
        self.assertEqual(sample.tags.get().tag, tag)
        self.assertEqual(tag.tagged_samples.get().sample, sample)

    def test_tag_sample_and_group(self):
        """Ensure we can tag a sample group."""
        org = Organization.objects.create(name='org AUHFVJKELF')
        lib = org.create_sample_group(name='LBRY_01 AUHFVJKELF', is_library=True)
        sample = lib.create_sample(name='SMPL_01 AUHFVJKELF')
        tag = Tag.objects.create(name='tag AUHFVJKELF')
        tag.tag_sample(sample)
        tag.tag_sample_group(lib)
        self.assertEqual(sample.tags.get().tag, tag)
        self.assertEqual(tag.tagged_samples.get().sample, sample)
        self.assertEqual(lib.tags.get().tag, tag)
        self.assertEqual(tag.tagged_sample_groups.get().sample_group, lib)


class TagApiTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.org1 = Organization.objects.create(name='Test Organization')
        cls.org2 = Organization.objects.create(name='Test Organization (No Membership)')
        cls.creds = ('user@domain.com', 'Foobar22')
        cls.user = PangeaUser.objects.create(email=cls.creds[0], password=cls.creds[1])
        cls.org1.users.add(cls.user)
        cls.priv_grp_auth = cls.org1.create_sample_group(name='GRP_01', is_public=False)
        cls.pub_grp = cls.org2.create_sample_group(name='GRP_02', is_public=True)
        cls.priv_grp_unauth = cls.org2.create_sample_group(name='GRP_03', is_public=False)

    def test_create_tag(self):
        """Ensure authorized user can create sample group."""
        self.client.force_authenticate(user=self.user)

        url = reverse('tag-create')
        data = {'name': 'Test Tag'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tag.objects.count(), 1)
        self.assertEqual(Tag.objects.get().name, 'Test Tag')

    def test_tag_read(self):
        """Ensure no login is required to read a tag."""
        tag = Tag.objects.create(name='My Test Tag')
        url = reverse('tag-details', kwargs={'pk': tag.uuid})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_tag_tag(self):
        tag1 = Tag.objects.create(name='My Test Tag 1')
        tag2 = Tag.objects.create(name='My Test Tag 2')
        url = reverse('tag-tags', kwargs={'tag_pk': tag1.uuid})
        data = {'tag_uuid': tag2.uuid}
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tag1 = Tag.objects.get(pk=tag1.uuid)
        self.assertEqual(tag1.related_tags.get().other_tag, tag2)

    def test_tag_public_sample_group(self):
        tag = Tag.objects.create(name='My Test Tag AHGDGS')
        url = reverse('tag-sample-groups', kwargs={'tag_pk': tag.uuid})
        data = {'sample_group_uuid': self.pub_grp.uuid}
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tag = Tag.objects.get(pk=tag.uuid)
        self.assertEqual(tag.tagged_sample_groups.get().sample_group, self.pub_grp)

    def test_auth_tag_private_sample_group(self):
        tag = Tag.objects.create(name='My Test Tag YDSGJ')
        url = reverse('tag-sample-groups', kwargs={'tag_pk': tag.uuid})
        data = {'sample_group_uuid': self.priv_grp_auth.uuid}
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tag1 = Tag.objects.get(pk=tag.uuid)
        self.assertEqual(tag.tagged_sample_groups.get().sample_group, self.priv_grp_auth)

    def test_unauth_tag_private_sample_group(self):
        tag = Tag.objects.create(name='My Test Tag ADIRH')
        url = reverse('tag-sample-groups', kwargs={'tag_pk': tag.uuid})
        data = {'sample_group_uuid': self.priv_grp_unauth.uuid}
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_read_tagged_sample_groups(self):
        tag = Tag.objects.create(name='My Test Tag YDSGJ')
        tag.tag_sample_group(self.pub_grp)
        tag.tag_sample_group(self.priv_grp_unauth)
        tag.tag_sample_group(self.priv_grp_auth)

        url = reverse('tag-sample-groups', kwargs={'tag_pk': tag.uuid})
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_uuids = [el['uuid'] for el in response.data['results']]
        self.assertEqual(len(response_uuids), 2)
        self.assertIn(str(self.pub_grp.uuid), response_uuids)
        self.assertIn(str(self.priv_grp_auth.uuid), response_uuids)
        self.assertNotIn(str(self.priv_grp_unauth.uuid), response_uuids)

    def test_tag_public_sample(self):
        pass

    def test_auth_tag_private_sample(self):
        pass

    def test_unauth_tag_private_sample(self):
        pass

    def test_read_tagged_samples(self):
        pass
