# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.management import call_command

from unittest import mock

from olympia import amo
from olympia.amo.tests import TestCase
from olympia.addons.models import Addon
from olympia.applications.models import AppVersion
from olympia.files.models import File
from olympia.files.tests.test_models import UploadMixin
from olympia.files.utils import parse_addon
from olympia.versions.models import Version
from olympia.users.models import UserProfile


class TestExtractHostPermissions(UploadMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        versions = {
            amo.DEFAULT_WEBEXT_MIN_VERSION_NO_ID,
            amo.DEFAULT_WEBEXT_MIN_VERSION_ANDROID,
            amo.DEFAULT_WEBEXT_MAX_VERSION,
        }
        for version in versions:
            AppVersion.objects.create(application=amo.FIREFOX.id, version=version)
            AppVersion.objects.create(application=amo.ANDROID.id, version=version)

    def setUp(self):
        super(TestExtractHostPermissions, self).setUp()
        self.addon = Addon.objects.create(
            guid='mv3@extension', type=amo.ADDON_EXTENSION, name='xxx'
        )
        self.version = Version.objects.create(addon=self.addon)
        UserProfile.objects.create(pk=settings.TASK_USER_ID)

    def test_extract(self):
        upload = self.get_upload('webextension_mv3.xpi')
        parsed_data = parse_addon(
            upload, addon=self.addon, user=mock.Mock(groups_list=[])
        )

        # Remove the host permissions from the parsed data so they aren't
        # added.
        pdata_host_permissions = parsed_data.pop('host_permissions')
        file_ = File.from_upload(upload, self.version, parsed_data=parsed_data)
        assert file_.host_permissions == []

        call_command('extract_host_permissions')

        file_ = File.objects.get(id=file_.id)
        host_permissions = file_.host_permissions
        assert len(host_permissions) == 2
        assert host_permissions == pdata_host_permissions
