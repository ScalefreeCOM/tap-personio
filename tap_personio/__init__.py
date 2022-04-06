#!/usr/bin/env python3
import os
import json
from pickle import NEXT_BUFFER
import singer
from singer import utils, metadata, metrics
from singer.catalog import Catalog, CatalogEntry
from singer.schema import Schema
import requests
from tap_personio.context import Context
from datetime import date

REQUIRED_CONFIG_KEYS = ["client_id", "client_secret", "start_date"]
LOGGER = singer.get_logger()

STREAM_PARAMS = {
    'employees': {
        'query_params': ['limit', 'offset'],
        'sub_operations': ['{employee_id}', 
                           '{employee_id}/absences/balance',
                           'custom-attributes',
                           'attributes',
                           '{employee_id}/profile-picture/{width}']
    },
    'attendances': {
        'query_params': ['start_date', 'end_date', 'limit', 'offset'],
        'sub_operations': None
    },
    'projects': {
        'query_params': None,
        'sub_operations': None
    }
}

SUB_STREAMS = {
    'projects': 'attendances/projects'
}


def get_abs_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


def load_schemas():
    """ Load schemas from schemas folder """
    schemas = {}
    for filename in os.listdir(get_abs_path('schemas')):
        path = get_abs_path('schemas') + '/' + filename
        file_raw = filename.replace('.json', '')
        with open(path) as file:
            schemas[file_raw] = Schema.from_dict(json.load(file))
    return schemas


def discover():
    raw_schemas = load_schemas()
    streams = []
    for stream_id, schema in raw_schemas.items():
        # TODO: populate any metadata and stream's key properties here..
        stream_metadata = []
        key_properties = []
        streams.append(
            CatalogEntry(
                tap_stream_id=stream_id,
                stream=stream_id,
                schema=schema,
                key_properties=key_properties,
                metadata=stream_metadata,
                replication_key=None,
                is_view=None,
                database=None,
                table=None,
                row_count=None,
                stream_alias=None,
                replication_method=None,
            )
        )
    return Catalog(streams)


def auth():
    client_id = Context.config.get('client_id')
    client_secret = Context.config.get('client_secret')
    
    LOGGER.debug("Getting new authorization token")
    url = "https://api.personio.de/v1/auth"

    querystring = {"client_id": client_id, "client_secret": client_secret}
    headers = {'accept': 'application/json'}
    response = requests.request("POST", url, headers=headers, params=querystring).json()
    
    # Check if authentication was successful
    if response['success']:
        # extract token from response
        token = response['data']['token']
    else:
        LOGGER.error(f"Could not authorize with Personio: {response['data']['message']}")
    LOGGER.debug(f"Auth Response: {response}")
    LOGGER.debug("Successfully authorized to Personio")
    return token

#def sync_stream(stream_name):
#    #stream_metadata = metadata.to_map(Context.get_catalog_entry(stream_name)['metadata'])
#    #LOGGER.info(f"Stream medatada {stream_metadata}")
#    extraction_time = singer.utils.now()
#    bookmark_column = stream.replication_key
#    replication_key = metadata.get(stream_metadata, (), 'valid-replication-keys')[0]

def sync_stream(url, headers, limit=200, offset=0, start_date=None, end_date=None):
    page = 1
    LOGGER.info(f"Start date: {start_date}")

    session = requests.Session()
    
    querystring = {
        "start_date": str(start_date),
        "end_date": str(end_date),
        "limit": int(limit),
        "offset": int(offset)
        }
    
    headers['Authorization'] = f"Bearer {auth()}"
    response = session.request("GET", url, headers=headers, params=querystring)
    LOGGER.info("API request: " + url)
    first_page = response.json()
    yield first_page
    
    if 'metadata' in first_page:
        LOGGER.info(f"Metadata: {first_page['metadata']}")
        number_pages = first_page['metadata']['total_pages']
        total_elements = first_page['metadata']['total_elements']
        
        LOGGER.debug(f"Total elements: {total_elements}")
        LOGGER.info(f"Batch 1 of {number_pages}")
        
        for page in range(1, number_pages):
            LOGGER.info(f"Batch {page+1} of {number_pages}")
            if 'time-offs' in url:
                querystring['offset'] += 1
            else:
                querystring['offset'] += limit
            headers['Authorization'] = f"Bearer {auth()}"
            response = session.request("GET", url, headers=headers, params=querystring)
            next_page = response.json()
            yield next_page
        

def sync(config, state, catalog):
    """ Sync data from tap source """
    #for stream in catalog.streams:
    #    LOGGER.info(stream)
    #LOGGER.info(catalog.get_selected_streams(state))
    LOGGER.info(f"State: {state}")
    # Loop over selected streams in catalog
    for stream in catalog.get_selected_streams(state):
        LOGGER.info("Syncing stream:" + stream.tap_stream_id)
        
        bookmark_column = stream.replication_key
        is_sorted = True  # TODO: indicate whether data is sorted ascending on bookmark value

        singer.write_schema(
            stream_name=stream.tap_stream_id,
            schema=stream.schema.to_dict(),
            key_properties=stream.key_properties,
        )
        
        Context.new_counts[stream.tap_stream_id] = 0
        Context.updated_counts[stream.tap_stream_id] = 0

        if stream.tap_stream_id in SUB_STREAMS:
            url = f"https://api.personio.de/v1/company/{SUB_STREAMS[stream.tap_stream_id]}"
        else:
            url = f"https://api.personio.de/v1/company/{stream.tap_stream_id}"
        headers = {'accept': 'application/json', 'Authorization': 'Bearer {token}'.format(token=Context.auth_token)}
        
        start_date = Context.config.get('start_date')
        end_date = date.today()

        max_bookmark = None
        for batch in sync_stream(url=url, headers=headers, start_date=start_date, end_date=end_date):
            if batch['success']:
                if 'metadata' in batch:
                    Context.new_counts[stream.tap_stream_id] = batch['metadata']['total_elements']
                else:
                    Context.new_counts[stream.tap_stream_id] = len(batch['data'])

                transformed_row = {}
                with singer.metrics.record_counter(endpoint=stream.tap_stream_id) as counter:
                    for row in batch['data']:
                        if stream.tap_stream_id == 'employees':
                            for key, value in row['attributes'].items():
                                row['attributes'][key] = value['value']
                        singer.write_record(stream.tap_stream_id, row)
                        if bookmark_column:
                            if is_sorted:
                                # update bookmark to latest value
                                singer.write_state({stream.tap_stream_id: row[bookmark_column]})
                            else:
                                # if data unsorted, save max value until end of writes
                                max_bookmark = max(max_bookmark, row[bookmark_column])
                        counter.increment()
                    if bookmark_column and not is_sorted:
                        singer.write_state({stream.tap_stream_id: max_bookmark})
                        
            else:
                LOGGER.error(batch)
                LOGGER.error("Failed to get data")
        LOGGER.info(f"Extracted {Context.new_counts[stream.tap_stream_id]} records from {stream.tap_stream_id}")
    return


@utils.handle_top_exception(LOGGER)
def main():
    # Parse command line arguments
    args = utils.parse_args(REQUIRED_CONFIG_KEYS)
    LOGGER.debug(f"Argumentss: {args}")

    # If discover flag was passed, run discovery mode and dump output to stdout
    if args.discover:
        catalog = discover()
        catalog.dump()
    # Otherwise run in sync mode
    else:
        Context.tap_start = utils.now()
        LOGGER.info("Tap Start: " + str(Context.tap_start))
        if args.catalog:
            Context.catalog = args.catalog#.to_dict()
            #LOGGER.info(f"Catalog: {catalog}")
        else:
            Context.catalog = discover()
            
        Context.config = args.config
        Context.state = args.state
        
        Context.auth_token = auth()
        
        sync(Context.config, Context.state, Context.catalog)


if __name__ == "__main__":
    main()
