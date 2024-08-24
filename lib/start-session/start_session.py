import boto3
import json
import os
import uuid
import datetime
import psycopg2

dynamodb = boto3.resource('dynamodb')

# add table name from sessiondb
TABLE_NAME = os.environ['SESSION_DB_TABLE_NAME']
table = dynamodb.Table(TABLE_NAME)



def is_price_valid(price_id, current_time):
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
        

    cursor = conn.cursor()

    # SQL-SELECT-Befehl vorbereiten
    sql = """
    SELECT valid_from, valid_to FROM dynamic_prices
    WHERE price_id = %s
    """

    # SQL-Befehl ausführen
    cursor.execute(sql, (price_id,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result:
         valid_from, valid_to = result
         print("validfrom, validto, currenttime: ", valid_from, valid_to)
         if valid_from <= current_time <= valid_to:
             return True
    return False



         

def handler(event, context):
    print(event)

    # Aktuelles Datum und Zeit abrufen
    time = datetime.datetime.now()
    # 2 Stunden zur aktuellen Zeit hinzufügen wegen zeitzone
    current_time = time + datetime.timedelta(hours=1)

    #daten aus event
    body = json.loads(event['body'])
    #check if body is present
    if not body:
            return {
                'statusCode': 400,
                'body': 'Request body is required.'
            }

    
    
    try:
        connector_id = body['connectorId']
        price_id = body['priceId']
        session_id = body['sessionId']

        if not all([connector_id, price_id, session_id]):
            return {
                'statusCode': 400,
                'body': 'Request body is missing some required fields.'
            }
        
        # preis überprüfen
        if not is_price_valid(price_id, current_time):
             return {
                'statusCode': 406,
                'body': f'Price for price_id {price_id} is not valid at {current_time}.'
            }


        # session_id zuweisen
        # session_id = str(uuid.uuid4())
        # data['sessionId'] = session_id

        # zeit hinzufügen
        # time = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        # data['time'] = time
        
        # data['connectorId'] = event['pathParameters']['connectorId']

        # table.put_item(Item=data)

        item = {
            'sessionId': session_id,
            'connectorId': connector_id,
            'priceId': price_id,
        }

        table.put_item(Item=item)
        print(item)

        return {
            'statusCode': 200,
            'body': json.dumps(item),
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({"Session konnte nicht gespeichert werden, error ": str(e)})}
    