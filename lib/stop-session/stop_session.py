import boto3
import json
import os
import uuid
import psycopg2
from boto3.dynamodb.conditions import Key
from decimal import Decimal



dynamodb = boto3.resource('dynamodb')

# add table name from sessiondb
TABLE_NAME = os.environ['SESSION_DB_TABLE_NAME']
table = dynamodb.Table(TABLE_NAME)

CHARGELOG_DB_TABLE_NAME = os.environ['CHARGELOG_DB_TABLE_NAME']
chargelog_table = dynamodb.Table(CHARGELOG_DB_TABLE_NAME)


# Zugangsdaten aus den Umgebungsvariablen abrufen
db_host = os.environ['DB_HOST']
db_port = os.environ['DB_PORT']
db_name = os.environ['DB_NAME']
db_user = os.environ['DB_USER']
db_password = os.environ['DB_PASSWORD']

def get_price_id(session_id):
    response = table.query(
        KeyConditionExpression=Key('sessionId').eq(session_id)
    )
    items = response['Items']
    if items:
        return items[0].get('priceId')  # return the priceId of the first match
    return None  # return None if no match is found


def get_price_from_postgres(price_id):
    conn = None
    try:
        # Verbindung zur PostgreSQL-Datenbank herstellen
        conn = psycopg2.connect(dbname=db_name, 
                                user=db_user, 
                                password=db_password, 
                                host=db_host, 
                                port=db_port)

        cur = conn.cursor()

        # SQL-Abfrage ausführen um den Preis mithilfe der priceId zu erhalten
        sql = "SELECT price FROM dynamic_prices WHERE price_id = %s;"
        cur.execute(sql, (price_id,))

        # daten abrufen
        result = cur.fetchone()
        if result:
            return result[0]
        return None
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return None
    finally:
        if conn is not None:
            conn.close()


def handler(event, context):
    print(event)
    try:
        body = json.loads(event['body'])
        chargelog = body.get('chargelog', {})
        print(chargelog)
        
        session_id = chargelog.get('sessionId')
        total_meter = chargelog.get('meterTotal')  


        if not session_id:
            return {
                'statusCode': 400,
                'body': 'Session ID missing in the request.'
            }

        # priceId aus SessionDB mit sessionId abrufen
        price_id = get_price_id(session_id)
        if not price_id:
            return {
                'statusCode': 404,
                'body': 'Session not found.'
            }

        # price aus price datenbank (postgres) anhand priceId
        price = get_price_from_postgres(price_id)
        if price is None:
            return {
                'statusCode': 404,
                'body': 'Price not found.'
            }
        
        # Preis berechnen
        total_price = str(round(float(price) * float(total_meter), 2))

        # gesamtpreis zu chargelog hinzufügen
        chargelog['totalPrice'] = total_price

        # add uuid to chargelog
        chargelog['chargelogId'] = str(uuid.uuid4())



        print('Chargelog: ',chargelog)

        # chargelog in chargelog db speichern
        chargelog_table.put_item(Item=chargelog)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'chargelog': chargelog
            }),
        }
    except Exception as e:
        print(str(e))
        return {
            'statusCode': 500,
            'body': json.dumps("An error occurred: " + str(e))
        }