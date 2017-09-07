#!/usr/bin/env python3

import argparse
import io
import os
import sys
import json
import threading
import http.client
import urllib
from datetime import datetime
import collections

import pkg_resources
from jsonschema.validators import Draft4Validator
from intercom.client import Client
import singer

logger = singer.get_logger()

def emit_state(state):
    if state is not None:
        line = json.dumps(state)
        logger.debug('Emitting state {}'.format(line))
        sys.stdout.write("{}\n".format(line))
        sys.stdout.flush()

def flatten(d, parent_key='', sep='__'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, str(v) if type(v) is list else v))
    return dict(items)

def persist_users(lines):
    state = None
    schemas = {}
    key_properties = {}
    headers = {}
    validators = {}

    now = datetime.now().strftime('%Y%m%dT%H%M%S')
    logger.info('hello world')
    for line in lines:
        try:
            o = json.loads(line)
        except json.decoder.JSONDecodeError:
            logger.error("Unable to parse:\n{}".format(line))
            raise

        if 'type' not in o:
            raise Exception("Line is missing required key 'type': {}".format(line))
        t = o['type']

        if t == 'RECORD':
            if 'stream' not in o:
                raise Exception("Line is missing required key 'stream': {}".format(line))
            if o['stream'] not in schemas:
                raise Exception("A record for stream {} was encountered before a corresponding schema".format(o['stream']))

            schema = schemas[o['stream']]
            validators[o['stream']].validate(o['record'])

            logger.info('Stream {}'.format(o['stream']))
            if o['stream'] == config.get('users_stream'):
                flattened_record = flatten(o['record'])

                reserved_fields = ['id','user_id','name','email','phone']
                reserved_field_overrides = config.get('reserved_field_overrides')
                if reserved_field_overrides:
                    # replace overides with keys expected by Intercom
                    for k,v in reserved_field_overrides.items():
                        flattened_record[k] = flattened_record[v]
                        del flattened_record[v]

                custom_attribute_keys = set(flattened_record.keys()) - set(reserved_fields)
                custom_attributes = { ca_key: flattened_record[ca_key] for ca_key in custom_attribute_keys }
                for ca_key in custom_attribute_keys: del flattened_record[ca_key]

                flattened_record['custom_attributes'] = custom_attributes

                logger.info('Core Attributes: {}'.format(flattened_record))
                job_id = intercom.users.submit_bulk_job(create_items=[flattened_record]);
                logger.info('bulk job id: {}'.format(job_id.__dict__))
            else:
                logger.info('Unsupported Stream: {}'.format(o['stream']))
            state = None
        elif t == 'STATE':
            logger.debug('Setting state to {}'.format(o['value']))
            state = o['value']
        elif t == 'SCHEMA':
            if 'stream' not in o:
                raise Exception("Line is missing required key 'stream': {}".format(line))
            stream = o['stream']
            schemas[stream] = o['schema']
            validators[stream] = Draft4Validator(o['schema'])
            if 'key_properties' not in o:
                raise Exception("key_properties field is required")
            key_properties[stream] = o['key_properties']
        else:
            raise Exception("Unknown message type {} in message {}"
                            .format(o['type'], o))

    return state


def send_usage_stats():
    try:
        version = pkg_resources.get_distribution('target-intercom').version
        conn = http.client.HTTPSConnection('collector.stitchdata.com', timeout=10)
        conn.connect()
        params = {
            'e': 'se',
            'aid': 'singer',
            'se_ca': 'target-intercom',
            'se_ac': 'open',
            'se_la': version,
        }
        conn.request('GET', '/i?' + urllib.parse.urlencode(params))
        response = conn.getresponse()
        conn.close()
    except:
        logger.debug('Collection request failed')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='Config file')
    args = parser.parse_args()

    global config
    if args.config:
        with open(args.config) as input:
            config = json.load(input)
    else:
        config = {}

    if not config.get('disable_collection', False):
        logger.info('Sending version information to stitchdata.com. ' +
                    'To disable sending anonymous usage data, set ' +
                    'the config parameter "disable_collection" to true')
        threading.Thread(target=send_usage_stats).start()

    global intercom
    intercom = Client(personal_access_token=config.get('access_token'))
    input = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    state = persist_users(input)

    emit_state(state)
    logger.debug("Exiting normally")


if __name__ == '__main__':
    main()
