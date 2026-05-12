"""Returns public Pusher config (key + cluster) for the frontend."""
import json
import os


def handler(request):
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'public, max-age=3600',
        },
        'body': json.dumps({
            'pusher_key': os.environ.get('PUSHER_KEY', ''),
            'pusher_cluster': os.environ.get('PUSHER_CLUSTER', 'ap2'),
        }),
    }
