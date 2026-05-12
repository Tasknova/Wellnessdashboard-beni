"""
Vercel Serverless Function — Pusher trigger for WF chatbot questions.
POST /api/ask with {session_id, question, mode}
Triggers 'question' event on 'wf-queries' Pusher channel.
"""
import json
import os
import pusher


def handler(request):
    # CORS preflight
    if request.method == 'OPTIONS':
        return {
            'statusCode': 204,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            },
        }

    if request.method != 'POST':
        return {
            'statusCode': 405,
            'body': json.dumps({'error': 'Method not allowed'}),
        }

    try:
        body = json.loads(request.body)
    except Exception:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Invalid JSON'}),
        }

    session_id = body.get('session_id', '')
    question = body.get('question', '').strip()
    mode = body.get('mode', 'INSIGHTS')

    if not question:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Missing question'}),
        }

    # Trigger Pusher event
    pusher_client = pusher.Pusher(
        app_id=os.environ['PUSHER_APP_ID'],
        key=os.environ['PUSHER_KEY'],
        secret=os.environ['PUSHER_SECRET'],
        cluster=os.environ.get('PUSHER_CLUSTER', 'ap2'),
        ssl=True,
    )

    pusher_client.trigger('wf-queries', 'question', {
        'session_id': session_id,
        'question': question,
        'mode': mode,
    })

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'status': 'sent', 'session_id': session_id}),
    }
