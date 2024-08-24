
import datetime
import json
import boto3
import os
import psycopg2


# Erstelle ein DynamoDB-Client
dynamodb = boto3.resource('dynamodb')

# Setze den Tabellennamen aus der Umgebungsvariable
# TABLE_NAME = os.environ['PRICE_DB_TABLE_NAME']
# table = dynamodb.Table(TABLE_NAME)


def handler(event, context):
    try:
        connector_id = event['pathParameters']['connectorId']
        if not connector_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'connectorId is required'
                })
            }

        print(f'connectorId: {connector_id}')

        # neue query auf postgresql
        # Zugangsdaten aus den Umgebungsvariablen abrufen
        db_host = os.environ['DB_HOST']
        db_port = os.environ['DB_PORT']
        db_name = os.environ['DB_NAME']
        db_user = os.environ['DB_USER']
        db_password = os.environ['DB_PASSWORD']

        conn = psycopg2.connect(dbname=db_name,
                                user=db_user,
                                password=db_password,
                                host=db_host,
                                port=db_port)

        # Cursor-Objekt erstellen
        cursor = conn.cursor()

        # Aktuelles Datum und Zeit abrufen
        time = datetime.datetime.now()

        # 2 Stunden zur aktuellen Zeit hinzufügen wegen zeitzone
        current_time = time + datetime.timedelta(hours=1)

        # SQL-SELECT-Befehl vorbereiten
        sql = """
        SELECT price, price_id, valid_to FROM dynamic_prices
        WHERE connector_id = %s
        AND valid_from <= %s
        AND valid_to >= %s;
        """

        # SQL-Befehl ausführen
        cursor.execute(sql, (connector_id, current_time, current_time))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            price, price_id, valid_to  = result
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'connector_id': connector_id,
                    'current_price': float(result[0]),
                    'price_id': price_id,
                    'valid_to': str(valid_to)
                })
            }
        else:
            return {
                'statusCode': 404,
                'body': f"No valid price found for connector_id {connector_id} at {current_time}."
            }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'Abrufen nicht geklappt, message': str(e)})
        }
