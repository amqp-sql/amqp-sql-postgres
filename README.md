# amqp-sql-postgres
A simple and lightweight AMQP-driven SQL executor service for PostgreSQL. The goal of this project is to decouple services from the specific database implementation, and allow for the AMQP service to act as a broker for database queries.

## Project Status
This is currently in early alpha. It is NOT suitable for a production environment, and may contain bugs. Use at your own risk.

## Environment Variables
* PG_HOST - Change the host address for the PostgreSQL server to connect to. Defaults to: localhost
* PG_PORT - Change the port for the PostgreSQL server to connect to. Defaults to: 5432
* PG_USER - Change the username to connect to the PostgreSQL server as. Defaults to the USER environment variable
* PG_PASSWORD - Change the password to use when connecting to the PostgreSQL server. Defaults to an empty string
* PG_DATABASE - Change the database to use when connecting to the PostgreSQL server. Defaults to the PG_USER environment variable
* AMQP_HOST - Change the host address for the AMQP server to connect to. Defaults to: localhost
* AMQP_PORT - Change the port for the AMQP server to connect to. Defaults to 5672
* AMQP_EXCHANGE - Change the Exchange to publish on in the AMQP server. Defaults to an empty string i.e. the default exchange
* AMQP_QUEUE - Change the Queue to subscribe to in the AMQP server. Defaults to: sql.execute
* AMQP_USERNAME - Change the username to connect to the AMQP server as. Defaults to: guest
* AMQP_PASSWORD - Change the password to connect to the AMQP server with. Defaults to: guest

## Message format
The message payload should be a JSON-formatted string in the form:
```JSON
{
  "query": "SQL STATEMENT HERE;",
  "data": {
    "my_placeholder_name": "SOME DATA HERE"
  }
}
```
See the [psycopg docs](https://www.psycopg.org/docs/usage.html#passing-parameters-to-sql-queries) for more details about how placeholder data works. It is strongly recommended to use placeholders for any unsanitised data to prevent SQL injection.

In order to receive a response, the message must contain a `reply_to` header and a `correlation_id` header. 

The response format is as follows:
```JSON
{
  "results": [ROWS_OF_RESULTS_HERE]
}
```

## Further development

### Will be included before release
* Gracefully handle interrupt to shutdown
* Gracefully handle connection to AMQP server dropping, and attempt to reconnect automatically
* Gracefully handle connection to PostgreSQL server dropping, and attempt to reconnect automatically

### Will not be included
* Authentication - Security is beyond the scope of this project. It is assumed that if a user is allowed to post to the AMQP message queue we're subscribed to, they are allowed to execute SQL with the PostgreSQL credentials we connected with. Authentication and permissions should be set up appropriately in the AMQP and PostgreSQL servers for your use case.
