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
import os
import time
import uuid
from datetime import datetime
from django.utils.translation import gettext as _
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import reset_queries
from quartet_capture.models import Rule, Task, TaskHistory, TaskParameter
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from quartet_capture.tasks import create_and_queue_task

DEFAULT_INBOUND_FILE_DIRECTORY = "/var/sftp/inbound/"
DEFAULT_INBOUND_FILE_DIRECTORY_PROCESSED = "/var/quartet/inbound-processed/"

inbound_file_directory = getattr(settings,
                                 'INBOUND_FILE_DIRECTORY',
                                 DEFAULT_INBOUND_FILE_DIRECTORY)

inbound_file_directory_processed = getattr(settings,
                                           'INBOUND_FILE_DIRECTORY_PROCESSED',
                                           DEFAULT_INBOUND_FILE_DIRECTORY_PROCESSED)


def print_dt(log_msg):
    now = str(datetime.now())
    print(now + " -- " + log_msg)


class ProcessInboundFiles(FileSystemEventHandler):
    '''
    Processes files that were created.
    '''
    def create_task_for_inbound_file(self, filepath: str, rule_name: str):
        '''
        Sends the contents of the file to be processed.
        '''
        with open(filepath, "rb") as f:
            data = f.read()
            print_dt("Creating task for file %s and rule %s" % (filepath, rule_name))
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
                print_dt("%s is a directory, ignoring" % event.src_path)
                return
            print_dt("A file was created %s" % event.src_path)
            path = os.path.split(event.src_path)
            fname = path[1]
            rule_directory = path[0].split(os.sep)[-1]
            processing_file_path = os.path.join(inbound_file_directory_processed,
                                                rule_directory,
                                                fname + "-" + str(uuid.uuid1()))
            # moving the file to processed folder, with unique name.
            os.rename(event.src_path, processing_file_path)
            print_dt("Processing %s" % processing_file_path)
            rule_name = rule_directory.replace('-', ' ')
            try:
                rule = Rule.objects.get(name=rule_name)
            except Rule.DoesNotExist:
                print_dt("Rule not found %s for file %s" % (rule_name, processing_file_path))
                reset_queries()
                return
            self.create_task_for_inbound_file(processing_file_path, rule_name)
            reset_queries()
        except Exception as e:
            print_dt("An exception occurred while processing creation event, recovering. %s" % str(e))
            reset_queries()

    def on_modified(self, event):
        print_dt("A file was modified %s" % event.src_path)


class Command(BaseCommand):
    help = _('Monitors a folder for files added, process them to the appropriate rule based on folder')
    default_inbound_path = "/var/quartet/inbound/"
    default_processed_directory = "/var/quartet/inbound-processed/"
    
    def create_folders_for_rules(self, root_directory):
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
                print_dt("Creating directory %s" % directory_path)
                os.mkdir(directory_path)
        
    def handle(self, *args, **options):
        self.create_folders_for_rules(inbound_file_directory)
        self.create_folders_for_rules(inbound_file_directory_processed)
        event_handler = ProcessInboundFiles()
        observer = Observer()
        observer.schedule(event_handler, inbound_file_directory, recursive=True)
        observer.start()
        try:
            while True:
                self.create_folders_for_rules(inbound_file_directory)
                self.create_folders_for_rules(inbound_file_directory_processed)
                reset_queries()
                time.sleep(120)
        except:
            print_dt("An error occurred, watcher will stop.")
            observer.stop()
            raise            
        observer.join()
