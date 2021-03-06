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
"""Read Command."""

from __future__ import print_function

import time
import datetime

from biggraphite.cli import command
from biggraphite import accessor as bg_accessor


class CommandRead(command.BaseCommand):
    """Read points."""

    NAME = "read"
    HELP = "read points for a specific metric."

    def add_arguments(self, parser):
        """Add custom arguments.

        See command.CommandBase.
        """
        parser.add_argument("metric")
        parser.add_argument(
            "--time-start",
            action=command.ParseDateTimeArg,
            help="Read points written later than this time.",
            default=datetime.datetime.now() - datetime.timedelta(minutes=10),
            required=False,
        )
        parser.add_argument(
            "--time-end",
            action=command.ParseDateTimeArg,
            help="Read points written earlier than this time.",
            default=datetime.datetime.now(),
            required=False,
        )
        parser.add_argument(
            "--stage",
            help="Read points from this specific stage.",
            default="",
            required=False,
        )

    def run(self, accessor, opts):
        """Read points.

        See command.CommandBase.
        """
        accessor.connect()
        metric = accessor.get_metric(opts.metric)
        if metric is None:
            print ("Metric '%s' doesn't exist" % opts.metric)
            return

        if opts.stage:
            stage = bg_accessor.Stage.from_string(opts.stage)
        else:
            # TODO(c.chary): get a stage that matches the time window.
            stage = metric.metadata.retention[0]

        time_start = stage.round_up(time.mktime(opts.time_start.timetuple()))
        time_stop = stage.round_up(time.mktime(opts.time_end.timetuple()))

        print("Name: ", metric.name)
        print("Metadata: ", metric.metadata.as_string_dict())
        print("Time window: %s to %s" % (time_start, time_stop))
        print("Stage: ", str(stage))
        print("Points:")

        points = accessor.fetch_points(
            metric,
            time_start,
            time_stop,
            stage
        )

        for point in points:
            print('%s: %s' % (point[0], point[1]))
