#!/usr/bin/env python

import logging
import json
import sys


logging.basicConfig(level=logging.DEBUG)
processed_messages = set()
ACTION_PASS = 'pass'
ACTION_ONLINE = 'online'
ACTION_OFFLINE = 'offline'


def main(input_filepath):
    """ Process events from a text file as per homework instructions """
    try:
        input_file = open(input_filepath)
    except IOError:
        logging.error("Invalid input file path \"%s\"" % input_filepath)
        sys.exit(1)

    input_str = input_file.read().strip()
    messages = (json.loads(json_str) for json_str in input_str.split('\n'))
    site_states = process_events(messages)
    print_output(site_states)


def process_events(messages):
    """ Takes in a iterable of events and returns site info """
    site_states = dict()
    for message in messages:
        # Skip already seen messages
        if message['id'] in processed_messages:
            continue

        site_id = message['site_id']
        site_states.setdefault(site_id, SiteState(site_id))
        site_states[site_id].process_event(message)
        processed_messages.add(message['id'])

    return site_states


def print_output(site_states):
    """ Prints out iterable of SiteState objects"""
    for site_id in sorted(site_states.iterkeys()):
        state = site_states[site_id]
        print "%s,messages=%s,emails=%s,operators=%s,visitors=%s" % (
            state.site_id,
            state.chat_count,
            state.email_count,
            state.operator_count,
            state.visitor_count
        )


class SiteState(object):
    """ An object that calculates metrics pertaining to a site """

    def __init__(self, site_id):
        self.site_id = site_id
        self.operators_online = 0
        self.operators = set()
        self.visitors = set()
        self.messages = list()
        self.operator_log = {0: dict(action=ACTION_PASS, operator=None)}
        self._cache_counts_dirty = True

    @property
    def operator_count(self):
        return len(self.operators)

    @property
    def visitor_count(self):
        return len(self.visitors)

    @property
    def chat_count(self):
        self.cache_message_counts()
        return self._chat_count

    @property
    def email_count(self):
        self.cache_message_counts()
        return self._email_count

    def cache_message_counts(self):
        if not self._cache_counts_dirty:
            return

        operator_count_changes = sorted(self.operator_log.keys())

        operator_counts = dict()
        current_operators = set()
        for operator_change_timestamp in operator_count_changes:
            event = self.operator_log[operator_change_timestamp]
            action = event['action']
            operator = event['operator']
            if action == ACTION_ONLINE:
                current_operators.add(operator)
            elif action == ACTION_OFFLINE:
                current_operators.discard(operator)
            elif action == ACTION_PASS:
                pass

            operator_counts[operator_change_timestamp] = len(current_operators)

        reversed_operator_changes = sorted(
            operator_count_changes, reverse=True)

        last_timestamp = float('Inf')
        self._chat_count = 0
        self._email_count = 0
        for operator_change_timestamp in reversed_operator_changes:
            message_count = len(filter(
                lambda t: (t >= operator_change_timestamp and
                           t < last_timestamp),
                self.messages))
            operator_count = operator_counts[operator_change_timestamp]

            if operator_count > 0:
                self._chat_count += message_count
            else:
                self._email_count += message_count

            last_timestamp = operator_change_timestamp

    def process_event(self, event):
        self._cache_counts_dirty = True
        event_type = event['type']
        if event_type == 'message':
            self._process_message(event)
        elif event_type == 'status':
            self._process_status(event)
        else:
            logging.warning("Unrecognized message type: \"%s\"" % event_type)

    def _process_message(self, event):
        self.visitors.add(event['from'])
        if not event['data']['message']:
            logging.warning("Unrecognized data: %s" % event['data'])
            return

        self.messages.append(event['timestamp'])

    def _process_status(self, event):
        operator = event['from']
        self.operators.add(operator)
        if event['data']['status'] == 'online':
            self.operator_log[event['timestamp']] = dict(
                action=ACTION_ONLINE, operator=operator)
        elif event['data']['status'] == 'offline':
            self.operator_log[event['timestamp']] = dict(
                action=ACTION_OFFLINE, operator=operator)
        else:
            logging.warning(
                "Unkown status type: \"%s\"" % event['data']['status'])


if __name__ == "__main__":
    if not len(sys.argv) == 2:
        print "Usage: python main.py <filepath>"
        sys.exit(1)

    main(str(sys.argv[1]))
