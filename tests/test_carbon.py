#!/usr/bin/env python
# Copyright 2016 Criteo
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import print_function

from biggraphite import test_utils as bg_test_utils   # noqa
bg_test_utils.prepare_graphite_imports()  # noqa

import unittest

from carbon import database
from carbon import conf as carbon_conf
from carbon import exceptions as carbon_exceptions

from biggraphite.plugins import carbon as bg_carbon


_TEST_METRIC = "mytestmetric"


class TestCarbonDatabase(bg_test_utils.TestCaseWithFakeAccessor):

    def setUp(self):
        super(TestCarbonDatabase, self).setUp()
        self.fake_drivers()
        settings = carbon_conf.Settings()
        settings["BG_CASSANDRA_CONTACT_POINTS"] = "host1,host2"
        settings["BG_CASSANDRA_KEYSPACE"] = self.KEYSPACE
        settings["STORAGE_DIR"] = self.tempdir
        self._plugin = bg_carbon.BigGraphiteDatabase(settings)
        self._plugin.create(
            _TEST_METRIC,
            retentions=[(1, 60)],
            xfilesfactor=0.5,
            aggregation_method="sum",
        )

    def test_empty_settings(self):
        database = bg_carbon.BigGraphiteDatabase(carbon_conf.Settings())
        self.assertRaises(carbon_exceptions.CarbonConfigException,
                          database.cache)

    def test_get_fs_path(self):
        path = self._plugin.getFilesystemPath(_TEST_METRIC)
        self.assertTrue(path.startswith("//biggraphite/"))
        self.assertIn(_TEST_METRIC, path)

    def test_create_get(self):
        other_metric = _TEST_METRIC + "-other"
        self._plugin.create(
            other_metric,
            retentions=[(1, 60)],
            xfilesfactor=0.5,
            aggregation_method="average",
        )
        self.assertTrue(self._plugin.exists(other_metric))
        self.assertEqual("average", self._plugin.getMetadata(other_metric, "aggregationMethod"))

    def test_nosuchmetric(self):
        other_metric = _TEST_METRIC + "-nosuchmetric"
        self.assertRaises(
            ValueError,
            self._plugin.setMetadata, other_metric, "aggregationMethod", "avg")
        self.assertRaises(
            ValueError,
            self._plugin.getMetadata, other_metric, "aggregationMethod")

    def test_set(self):
        # Setting the same value should work
        self._plugin.setMetadata(_TEST_METRIC, "aggregationMethod", "sum")
        # Setting a different value should fail
        self.assertRaises(
            ValueError,
            self._plugin.setMetadata, _TEST_METRIC, "aggregationMethod", "avg")

    def test_write(self):
        metric = bg_test_utils.make_metric(_TEST_METRIC)
        points = [(1, 42)]
        self.accessor.create_metric(metric)
        # Writing twice (the first write is sync and the next one isn't)
        self._plugin.write(metric.name, points)
        self._plugin.write(metric.name, points)
        actual_points = self.accessor.fetch_points(metric, 1, 2, stage=metric.retention[0])
        self.assertEqual(points, list(actual_points))

    def test_write_doubledots(self):
        metric = self.make_metric("a.b..c")
        metric_1 = self.make_metric("a.b.c")
        points = [(1, 42)]
        self.accessor.create_metric(metric)
        self._plugin.write(metric.name, points)
        actual_points = self.accessor.fetch_points(metric, 1, 2, stage=metric.retention[0])
        self.assertEqual(points, list(actual_points))
        actual_points = self.accessor.fetch_points(metric_1, 1, 2, stage=metric.retention[0])
        self.assertEqual(points, list(actual_points))


class TestMultiDatabase(bg_test_utils.TestCaseWithFakeAccessor):

    def setUp(self):
        super(TestMultiDatabase, self).setUp()
        self.fake_drivers()
        settings = carbon_conf.Settings()
        settings["BG_CASSANDRA_CONTACT_POINTS"] = "host1,host2"
        settings["BG_CASSANDRA_KEYSPACE"] = self.KEYSPACE
        settings["STORAGE_DIR"] = self.tempdir
        settings["LOCAL_DATA_DIR"] = self.tempdir
        self._settings = settings

    def _test_plugin(self, klass):
        plugin = klass(self._settings)
        self.assertFalse(plugin.exists(_TEST_METRIC))
        plugin.create(
            _TEST_METRIC,
            retentions=[(1, 60)],
            xfilesfactor=0.5,
            aggregation_method="sum",
        )
        self.assertTrue(plugin.exists(_TEST_METRIC))
        plugin.write(_TEST_METRIC, [(1, 1), (2, 2)])
        self.assertEquals(
            plugin.getMetadata(_TEST_METRIC, "aggregationMethod"), "sum")

    def test_whisper_and_biggraphite(self):
        self._test_plugin(bg_carbon.WhisperAndBigGraphiteDatabase)

    def test_biggraphite_and_whisper(self):
        self._test_plugin(bg_carbon.BigGraphiteAndWhisperDatabase)

    def test_plugin_registration(self):
        plugins = database.TimeSeriesDatabase.plugins.keys()
        self.assertTrue('whisper+biggraphite' in plugins)
        self.assertTrue('biggraphite+whisper' in plugins)
        self.assertTrue('biggraphite' in plugins)


if __name__ == "__main__":
    unittest.main()
