# Dynamic Pricing Service for EV Charging Stations (with AWS CDK)

This project is a showcase demonstrating how dynamic pricing can be implemented and managed for electric vehicle (EV) charging stations. The service allows for real-time price adjustments based on various factors and integrates with a charging backend for billing purposes.

## Overview

This project showcases a dynamic pricing system designed for EV charging stations. It allows for the management and real-time adjustment of prices at charging stations, which are then processed through a charging backend system for accurate billing.

### Key Features:

- Dynamic Pricing: Prices at charging stations can be adjusted in real-time based on demand, time, or other configurable parameters.
- Session Management: Start and stop charging sessions while tracking the associated pricing.
- Integration with Charging Backend: The service is designed to integrate with a backend system responsible for processing and billing based on the dynamic prices.

### The architecture includes:

- DynamoDB Tables: Used to store session data and charge logs.
- Lambda Functions: Handle the logic for session management and dynamic pricing.
- API Gateway: Exposes RESTful API endpoints for interacting with the system.
- RDS (PostgreSQL): Manages dynamic pricing data and validation.

### Prerequisites

- AWS CLI
- AWS CDK
- Node.js
- An AWS account with necessary permissions to deploy resources
- A PostgreSQL database for dynamic pricing


### Usage

- API Endpoints:
- GET /prices/{connectorId}: Retrieves the price for a specific connector ID.
- POST /startsession: Starts a new charging session.
- POST /stopsession: Stops a charging session.
- POST /engine: Resolves and applies dynamic pricing.

These endpoints are exposed via API Gateway and are backed by the respective Lambda functions defined in the CDK stack.