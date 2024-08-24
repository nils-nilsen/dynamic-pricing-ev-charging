import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as python from '@aws-cdk/aws-lambda-python-alpha';
import * as dotenv from 'dotenv';
// import * as sqs from 'aws-cdk-lib/aws-sqs';

dotenv.config();




export class DynCdkStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string, props?: cdk.StackProps) {
    super(scope, id, props);



    // DB fÜr Sessions
    const sessionDb = new dynamodb.Table(this, 'Session DB', {
      partitionKey: {
        name: 'sessionId',
        type: dynamodb.AttributeType.STRING
      },
      billingMode: dynamodb.BillingMode.PROVISIONED,
      readCapacity: 5,
      writeCapacity: 5,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // DB fÜr Chargelog
    const chargelogDb = new dynamodb.Table(this, 'Chargelog DB', {
      partitionKey: {
        name: 'chargelogId',
        type: dynamodb.AttributeType.STRING
      },
      billingMode: dynamodb.BillingMode.PROVISIONED,
      readCapacity: 5,
      writeCapacity: 5,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const layerArn = process.env.LAYER_ARN || '';
    const layer = lambda.LayerVersion.fromLayerVersionArn(this, 'MyLayer', layerArn);
    

    // Lambda-Funktion Price Engine
    const pricingEngine = new lambda.Function(this, 'Pricing Engine', {
      runtime: lambda.Runtime.PYTHON_3_9,
      code: lambda.Code.fromAsset('lib/pricing-engine'),
      layers: [layer],
      handler: 'pricing_engine.handler',
      environment: {
        'DB_HOST': process.env.DB_HOST || '',
        'DB_PORT': process.env.DB_PORT || '',
        'DB_NAME': process.env.DB_NAME || '',
        'DB_USER': process.env.DB_USER || '',
        'DB_PASSWORD': process.env.DB_PASSWORD || '',
      },

    });
  
    // Lambda-Funktion Price Resolver
    const pricingResolver = new lambda.Function(this, 'Pricing Resolver', {
      runtime: lambda.Runtime.PYTHON_3_9,
      code: lambda.Code.fromAsset('lib/pricing-resolver'),
      layers: [layer],
      handler: 'pricing_resolver.handler',
      environment: {
        // 'PRICE_DB_TABLE_NAME': priceDb.tableName,
        'DB_HOST': process.env.DB_HOST || '',
        'DB_PORT': process.env.DB_PORT || '',
        'DB_NAME': process.env.DB_NAME || '',
        'DB_USER': process.env.DB_USER || '',
        'DB_PASSWORD': process.env.DB_PASSWORD || '',
      }
    });

    // Lambda Funktion Start Charging Session
    const startSession = new lambda.Function(this, 'Start Session', {
      runtime: lambda.Runtime.PYTHON_3_9,
      code: lambda.Code.fromAsset('lib/start-session'),
      handler: 'start_session.handler',
      layers: [layer],
      environment: {
        'SESSION_DB_TABLE_NAME': sessionDb.tableName,
        'DB_HOST': process.env.DB_HOST || '',
        'DB_PORT': process.env.DB_PORT || '',
        'DB_NAME': process.env.DB_NAME || '',
        'DB_USER': process.env.DB_USER || '',
        'DB_PASSWORD': process.env.DB_PASSWORD || '',
      }
    });
    startSession.addEnvironment('SESSION_DB_TABLE_NAME', sessionDb.tableName);
    sessionDb.grantWriteData(startSession);

    // Lambda Funktion Stop Charging Session
    const stopSession = new lambda.Function(this, 'Stop Session', {
      runtime: lambda.Runtime.PYTHON_3_9,
      code: lambda.Code.fromAsset('lib/stop-session'),
      handler: 'stop_session.handler',
      layers: [layer],
      environment: {
        'SESSION_DB_TABLE_NAME': sessionDb.tableName,
        'CHARGELOG_DB_TABLE_NAME': chargelogDb.tableName,
        'DB_HOST': process.env.DB_HOST || '',
        'DB_PORT': process.env.DB_PORT || '',
        'DB_NAME': process.env.DB_NAME || '',
        'DB_USER': process.env.DB_USER || '',
        'DB_PASSWORD': process.env.DB_PASSWORD || '',
      }
    });
    stopSession.addEnvironment('SESSION_DB_TABLE_NAME', sessionDb.tableName);
    stopSession.addEnvironment('CHARGELOG_DB_TABLE_NAME', chargelogDb.tableName);
    // sessionDb.grantWriteData(stopSession);
    sessionDb.grantReadWriteData(stopSession);
    chargelogDb.grantReadWriteData(stopSession);


    // API Gateway
    const api = new apigateway.RestApi(this, 'API', {
      restApiName: 'Dynamic Pricing Service',
      description: 'Dynamic Pricing API Gateway',
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS
      },
      deployOptions: {
        stageName: 'dev',
        dataTraceEnabled: true,
        tracingEnabled: true,
      }

    });

    const pricesResource = api.root.addResource('prices').addResource('{connectorId}');
    const chargelogResource = api.root.addResource('chargelog');
    const engineResource = api.root.addResource('engine');

    const startSessionResource = api.root.addResource('startsession');
    const stopSessionResource = api.root.addResource('stopsession');


    pricesResource.addMethod('GET', new apigateway.LambdaIntegration(pricingResolver));
    //chargelogResource.addMethod('POST', new apigateway.LambdaIntegration(chargelogGenerator));

    engineResource.addMethod('POST', new apigateway.LambdaIntegration(pricingEngine));
    // engineResource.addCorsPreflight({
    //   allowOrigins: apigateway.Cors.ALL_ORIGINS,
    //   allowMethods: apigateway.Cors.ALL_METHODS
    // })
    startSessionResource.addMethod('POST', new apigateway.LambdaIntegration(startSession));
    stopSessionResource.addMethod('POST', new apigateway.LambdaIntegration(stopSession));
  }
}