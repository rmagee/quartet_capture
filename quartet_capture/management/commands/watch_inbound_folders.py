# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2018 SerialLab Corp.  All rights reserved.
import logging
import os
import time
import uuid
from django.core.management.base import BaseCommand
from django.db import reset_queries
from django.utils.translation import gettext as _
from shutil import chown
from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver

from quartet_capture.models import Rule
from quartet_capture.tasks import create_and_queue_task


class ProcessInboundFiles(FileSystemEventHandler):
    '''
    Processes files that were created.
    '''

    def __init__(self, inbound_file_directory_processed) -> None:
        super().__init__()
        self.inbound_file_directory_processed = inbound_file_directory_processed

    def create_task_for_inbound_file(self, filepath: str, rule_name: str):
        '''
        Sends the contents of the file to be processed.
        '''
        with open(filepath, "rb") as f:
            data = f.read()
            logging.info("Creating task for file %s and rule %s" % (
                filepath, rule_name))
            create_and_queue_task(data=data,
                                  rule_name=rule_name,
                                  task_type="Input",
                                  run_immediately=False,
                                  initial_status="QUEUED",
                                  task_parameters=[])

    def on_created(self, event):
        '''
        Moves file received and creates a task for it.
        '''
        try:
            if os.path.isdir(event.src_path):
                logging.info("%s is a directory, ignoring" % event.src_path)
                return
            logging.info("A file was created %s" % event.src_path)
            if self.check_for_file_expansion(event.src_path):
                path = os.path.split(event.src_path)
                fname = path[1]
                rule_directory = path[0].split(os.sep)[-1]
                processing_file_path = os.path.join(
                    self.inbound_file_directory_processed,
                    rule_directory,
                    fname + "-" + str(uuid.uuid1()))
                # moving the file to processed folder, with unique name.
                os.rename(event.src_path, processing_file_path)
                logging.info("Processing %s" % processing_file_path)
                rule_name = rule_directory.replace('-', ' ')
                try:
                    rule = Rule.objects.get(name=rule_name)
                except Rule.DoesNotExist:
                    logging.info("Rule not found %s for file %s" % (
                        rule_name, processing_file_path))
                    reset_queries()
                    return
                self.create_task_for_inbound_file(processing_file_path,
                                                  rule_name)
                reset_queries()
            else:
                raise self.FileIncompleteException('The file could not be '
                                                   'read for processing since '
                                                   'it was still being written')
        except Exception as e:
            logging.warning(
                "An exception occurred while processing creation event, recovering. %s" % str(
                    e))
            reset_queries()

    def check_for_file_expansion(self, file_path, tries=120, try_interval=.5,
                                 success_tries=6):
        """
        If the file is growing it hasn't been fully written out yet.
        :param tries: The max number of times to check
        :param tries: The number of tries before stopping
        :param try_interval: The interval between tries.
        :param success_tries: The number of consecutive successes that must
        occur before it can be determined the file isn't growing.
        :return: True if the file isn't growing false if it still was
        showing growth past the tries limit.
        """
        current_tries = 0
        cursize = os.path.getsize(file_path)
        success_count = 0
        while success_count < success_tries and current_tries < tries:
            current_tries += 1
            fsize = os.path.getsize(file_path)
            if cursize == fsize:
                success_count += 1
            else:
                cursize = fsize
                success_count = 0
            time.sleep(try_interval)
        return success_count == success_tries

    def on_modified(self, event):
        logging.info("A file was modified %s" % event.src_path)

    class FileIncompleteException(Exception):
        pass


class Command(BaseCommand):
    help = _(
        'Monitors a folder for files added, process them to the appropriate '
        'rule based on folder')

    def create_folders_for_rules(self, root_directory, group_name):
        '''
        Automatically creates a folder for a given rule.
        '''
        all_rules = Rule.objects.all()
        for rule in all_rules:
            directory_name = rule.name.replace(' ', '-')
            directory_path = os.path.join(root_directory, directory_name)
            try:
                os.stat(directory_path)
            except:
                logging.info("Creating directory %s" % directory_path)
                os.mkdir(directory_path)
                chown(directory_path, group=group_name)
                os.chmod(directory_path, 0o775)

    def handle(self, *args, **options):
        inbound_file_directory = options['inbound_dir']
        inbound_file_directory_processed = options['processed_dir']
        group_name = options['group']
        self.create_folders_for_rules(inbound_file_directory, group_name)
        self.create_folders_for_rules(inbound_file_directory_processed,
                                      group_name)
        event_handler = ProcessInboundFiles(inbound_file_directory_processed)
        observer = PollingObserver()
        observer.schedule(event_handler, inbound_file_directory,
                          recursive=True)
        observer.start()
        try:
            while True:
                self.create_folders_for_rules(inbound_file_directory,
                                              group_name)
                self.create_folders_for_rules(inbound_file_directory_processed,
                                              group_name)
                reset_queries()
                time.sleep(120)
        except:
            logging.info("An error occurred, watcher will stop.")
            observer.stop()
            raise
        finally:
            observer.join()

    def add_arguments(self, parser):
        parser.add_argument('inbound_dir', help='The inbound directory to'
                                                ' monitor.',
                            )
        parser.add_argument('processed_dir', help='The directory to store '
                                                  'files in after '
                                                  'processing',
                            )
        parser.add_argument('group', help='The default group to assign '
                                          'ownership of new directories '
                                          'to')
