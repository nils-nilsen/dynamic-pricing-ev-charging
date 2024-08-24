import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')

PRICE_TABLE = os.environ['PRICE_DB_TABLE_NAME']
price_table = dynamodb.Table(PRICE_TABLE)

CHARGELOG_DB_TABLE_NAME = os.environ['CHARGELOG_DB_TABLE_NAME']
charglog_table = dynamodb.Table(CHARGELOG_DB_TABLE_NAME)

SESSION_DB_TABLE_NAME = os.environ['SESSION_DB_TABLE_NAME']
session_table = dynamodb.Table(SESSION_DB_TABLE_NAME)


def handler(event, context):
    try:
    # session item aus sessionDB holen
        session_id = event['pathParameters']['sessionId']
        print('session_id:', session_id)

        if 'pathParameters' not in event or 'sessionId' not in event['pathParameters']:
            return {
                'statusCode': 400,
                'body': 'Missing sessionId'
            }
        
        try:
            session_response = session_table.get_item(
                Key={
                    'sessionId': session_id
                })
        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Something went wrong at session table', 'error': str(e)})
                }

        # session überprüfen
        if 'Item' not in session_response:
            return {
                'statusCode': 404,
                'body': 'Session not found: ' + str(session_response['Items'][0])
            }
        
        print('session_response:', session_response)

        if 'priceId' not in session_response['Item']:
            return {
                'statusCode': 400,
                'body': 'Missing priceId in session'
            }

        # aus session item price_id 
        price_id = session_response['Item']['priceId']
        print('priceId:', price_id)

        # daten aus event 
        body = json.loads(event['body'])
        print('body:', body)
        chargelog = body['chargelog']
        print('chargelog:', chargelog)

        # chargelog überprüfen
        if 'chargelog' not in body:
            return {
                'statusCode': 400,
                'body': 'Missing chargelog'
            }

        start_meter_value = chargelog['startMeterValue']
        print('start_meter_value:', start_meter_value)
    
        stop_meter_value = chargelog['stopMeterValue']
        print('stop_meter_value:', stop_meter_value)

        # energieverbrauch berechnen
        consumed_energy = stop_meter_value - start_meter_value


        # price auf der priceDb abrufen mit priceId

        try:
            price_response = price_table.get_item( 
                Key={
                    'priceId': price_id
                }
            )
                # Überprüfen Sie, ob Einträge zurückgegeben wurden
        
        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps(f'message: Something went wrong at price table with priceId {price_id}: {e}')
                }

        # preis überprüfen
        if 'Item' not in price_response:
            return {
                'statusCode': 404,
                'body': 'Price not found'
            }

         # gesamtpreis berechnen
        total_price = consumed_energy * price_response['Item']['price']


        # chargelog anreichern
        total_chargelog = chargelog
        total_chargelog['totalPrice'] = total_price
        charglog_table.put_item(
            Item=total_chargelog
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Chargelog saved successfully', 'totalPrice': total_price, 'chargelog': total_chargelog})
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Something went wrong', 'error': str(e)})
        }
