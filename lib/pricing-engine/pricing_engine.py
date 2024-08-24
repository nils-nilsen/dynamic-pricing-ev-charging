import datetime
import json
#import boto3
import uuid
import os
import psycopg2





# dynamodb = boto3.resource('dynamodb')

# TABLE_NAME = os.environ['PRICE_DB_TABLE_NAME']
# table = dynamodb.Table(TABLE_NAME)


def handler(event, context):
    try:



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
        
        # # daten aus event
        # body = json.loads(event['body'])
        # if not body:
        #     return {
        #         'statusCode': 400,
        #         'body': 'Request body is required.'
        #     }

        # Daten aus dem Event-Body als Array extrahieren
        data_array = json.loads(event.get('body', '[]'))
        response_items = []

        if not data_array:
            return {
                'statusCode': 400,
                'body': 'Request body is required.'
            }
        


        
        # connector_id = "test123"
        # price = 0.35
        # valid_from = "2023-10-10 10:00:00" 
        # valid_to = "2023-10-10 11:00:00"
        for data in data_array:
            price_id = str(uuid.uuid4())  
            connector_id  = data['connectorId']
            price = data['price']
            valid_from = data['valid_from']
            valid_to = data['valid_to']
            # plus 1h wegen zeitzone
            #valid_from = str(datetime.datetime.strptime(data['valid_from'],  '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours=1))
            #valid_to = str(datetime.datetime.strptime(data['valid_to'], '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours=1))

            # print data to console and add descrpition before values
            print("Price ID: ", price_id)
            print("Connector ID: ", connector_id)
            print("Price: ", price)
            print("Valid From: ", valid_from)
            print("Valid To: ", valid_to)
    
        

            # sql-abfrage um zu gucken ob eintrag in diesem zeitraum schon vorhanden
            sql_check = """
            SELECT * FROM dynamic_prices
            WHERE connector_id = %s
            AND valid_from <= %s AND valid_to >= %s;
            """

            cursor.execute(sql_check, (connector_id, valid_from, valid_to))
            existing_entry = cursor.fetchone()

            if existing_entry:
                # wenn ein bestehender Eintrag gefunden wird, diesen aktualisieren
                sql_update = """
                UPDATE dynamic_prices
                SET price = %s, valid_from = %s, valid_to = %s 
                WHERE price_id = %s;
                """
                cursor.execute(sql_update, (price, valid_from, valid_to, existing_entry[0]))
            else:
                # sonst einen neuen Eintrag hinzufügen
                sql_insert = """
                INSERT INTO dynamic_prices (price_id, connector_id, price, valid_from, valid_to)
                VALUES (%s, %s, %s, %s, %s);
                """
                cursor.execute(sql_insert, (price_id, connector_id, price, valid_from, valid_to))

            response_items.append({
                'price_id': price_id,
                'connector_id': connector_id,
                'price': price,
                'valid_from': valid_from,
                'valid_to': valid_to
            })
    

        # sql = """
        # INSERT INTO dynamic_prices  (price_id, connector_id, price, valid_from, valid_to)
        # VALUES (%s, %s, %s, %s, %s);
        # """

        #  # SQL-Befehl ausführen
        # cursor.execute(sql, (price_id, connector_id, price, valid_from, valid_to))


        conn.commit()
        cursor.close()
        conn.close()


        
        # # ID für Preiseintrag
        # price_id = str(uuid.uuid4())

        # # daten aus event
        # body = json.loads(event['body'])

        # connector_id  = body['connectorId']
        # price = body['price']
        # startdate = body['startdate']
        # starttime = body['starttime']
        # enddate = body['enddate']
        # endtime = body['endtime']


        # item = {
        #     'priceId': price_id,
        #     'connectorId': connector_id,
        #     'price': price,
        #     'startValidityOfPrice': startdate + ' ' + starttime,
        #     'endValidityOfPrice': enddate + ' ' + endtime,
        #     'createdAt': datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        #     }


        ## Testdaten

        # item = {
        #     # add key id
        #     'priceId': price_id,
        #     'connectorId': '12345',
        #     'price': str(0.35),
        #     # 'time': '2020-06-01'
        #     # 'price': event['price'],
        #     # 'time': event['time']
        #     # current time
        #     'createdAt': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        #     'startValidityOfPrice': datetime.now().strftime("%m/%d/%Y, 13:%M:%S"),
        #     'endValidityOfPrice': datetime.now().strftime("%m/%d/%Y, 14:%M:%S")
        # }

        # table.put_item(Item=item)
        # print(item)

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,UPDATE'
            },
            # 'body': json.dumps(item)
            'body': json.dumps({
                'price_id': price_id,
                'connector_id': connector_id,
                'price': price,
                'valid_from': valid_from,
                'valid_to': valid_to
            })
        }

    except Exception as e:
        print('error:', e)
        return {
            'statusCode': 500,
            # log detailed error message
            # 'body': 'Error: ' + str(e)
            # log simple error message

            'body': 'Error: Preis konnte nicht in der Datenbank gespeichert werden, Error-Log: ' + str(e)}
