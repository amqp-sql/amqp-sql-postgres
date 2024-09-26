# ################################################################################################################
#  Copyright (c) 2024 amqp-sql-postgres contributors.                                                            #
#  This file is part of amqp-sql-postgres. amqp-sql-postgres is free software:                                   #
#  You can redistribute it and/or modify it under the terms of the GNU General Public License as published by    #
#  the Free Software Foundation, either version 3 of the License, or (at your option) any later version.         #
#  You should have received a copy of the GNU General Public License along with amqp-sql-postgres.               #
#  If not, see: https://www.gnu.org/licenses/.                                                                   #
# ################################################################################################################

import os

import psycopg2
import pika
import json

# PostgreSQL connection settings
PG_HOST = os.environ.get('PG_HOST', 'localhost')
PG_PORT = int(os.environ.get('PG_PORT', 5432))
PG_USER = os.environ.get('PG_USER', os.environ.get('USER', 'postgres'))
PG_PASSWORD = os.environ.get('PG_PASSWORD', '')
PG_DATABASE = os.environ.get('PG_DATABASE', PG_USER)

# AMQP connection settings
AMQP_HOST = os.environ.get('AMQP_HOST', pika.ConnectionParameters.DEFAULT_HOST)
AMQP_PORT = int(os.environ.get('AMQP_PORT', pika.ConnectionParameters.DEFAULT_PORT))
AMQP_EXCHANGE = os.environ.get('AMQP_EXCHANGE', '')
AMQP_QUEUE = os.environ.get('AMQP_QUEUE', 'sql.execute')
AMQP_USERNAME = os.environ.get('AMQP_USERNAME', pika.ConnectionParameters.DEFAULT_USERNAME)
AMQP_PASSWORD = os.environ.get('AMQP_PASSWORD', pika.ConnectionParameters.DEFAULT_PASSWORD)


def connect_to_postgres():
    """Establish a connection to the PostgreSQL database."""
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_USER,
        password=PG_PASSWORD,
        dbname=PG_DATABASE
    )


def connect_to_amqp():
    """Establish a connection to the AMQP server."""
    return pika.BlockingConnection(
        pika.ConnectionParameters(
            host=AMQP_HOST,
            port=AMQP_PORT,
            credentials=pika.credentials.PlainCredentials(
                username=AMQP_USERNAME,
                password=AMQP_PASSWORD
            )
        )
    )


# noinspection PyUnusedLocal
def process_message(ch, method, props, body):
    """Process an incoming AMQP message."""
    try:
        # Parse the message as JSON
        message = json.loads(body)

        # Extract the query and query data
        query = message['query']
        query_data = message.get('data', {})

        # Execute the query
        response = {'results': None}
        with db_conn.cursor() as cursor:
            cursor.execute(query, query_data)

            # If a response is expected, fetch the results
            if props.reply_to:
                results = cursor.fetchall()
                response['results'] = results

        # If a response is expected, send the results to the response queue
        if props.reply_to:
            ch.basic_publish(
                exchange=AMQP_EXCHANGE,
                routing_key=props.reply_to,
                body=json.dumps(response),
                properties=pika.BasicProperties(
                    correlation_id=props.correlation_id
                )
            )

        # Acknowledge the message if processing completed without error
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        # Handle any errors that occur during processing
        print(f"Error processing query: {e}")


# Establish connections to PostgreSQL and AMQP
db_conn = connect_to_postgres()
amqp_conn = connect_to_amqp()
ampq_channel = amqp_conn.channel()

# Declare the queue and bind it to the exchange
ampq_channel.queue_declare(queue=AMQP_QUEUE)

# Start consuming messages from the queue
ampq_channel.basic_consume(
    queue=AMQP_QUEUE,
    on_message_callback=process_message
)

print("Waiting for queries...")
ampq_channel.start_consuming()
