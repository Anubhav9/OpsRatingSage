import boto3
import json
import logging
import os
import requests
from datetime import datetime

print('Loading function')
dynamo = boto3.client('dynamodb')


GOOGLE_PLACES_API_URL="https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={}&inputtype=textquery&key={}"
GOOGLE_PLACES_RATINGS_API_URL="https://maps.googleapis.com/maps/api/place/details/json?place_id={}&key={}"
RATINGS_DYNAMO_DB_TABLE="ratings_info_v1"
CACHE_NO_OF_DAYS=6




def get_place_id(place_name):
    API_KEY=os.environ.get("API_KEY")
    modified_url=GOOGLE_PLACES_API_URL.format(place_name,API_KEY)
    response=requests.get(modified_url)
    if(response.status_code!=200):
        logging.error("Non 200 Response Code is recieved")
        return{"status_code":response.status_code,"message":"Oops, something went wrong"}
    else:
        response_body=response.json()
        print(response_body)
        place_id=response_body['candidates'][0]['place_id']
        logging.info("Place ID returned from the request is ",place_id)
        return place_id
        

def get_google_ratings_from_place_id(place_id):
    modified_url=GOOGLE_PLACES_RATINGS_API_URL.format(place_id,os.environ.get("API_KEY"))
    response=requests.get(modified_url)
    if(response.status_code!=200):
        return {"status_code":response.status_code,"message":"Oops,something went wrong"}
    else:
        response_body=response.json()
        total_user_ratings=response_body['result'].get('user_ratings_total')
        print(response_body['result'])
        return total_user_ratings
        
        

def store_data_dynamo_db(place_id,google_address,no_of_reviews):

    session = boto3.Session(
    aws_access_key_id=os.environ.get('RATINGS_AWS_ACCESS_KEY'),
    aws_secret_access_key=os.environ.get('RATINGS_AWS_SECRET_KEY'),
    region_name='ap-south-1' )

    dynamodb=session.resource('dynamodb')

    table_name=RATINGS_DYNAMO_DB_TABLE
    table = dynamodb.Table(table_name)

    item={
        "placeId":place_id,
        "googleAddress":google_address,
        "timeUpdated":str(datetime.now().date()),
        "noOfReviews":no_of_reviews
    }
    response=table.put_item(Item=item)
    # Check the response
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        logging.info("Item added successfully")
    else:
        logging.error("Error Happened while adding data to dynamo db")
        print("Failed to add item:", response)
    


def cache_in_dynamo_db(placement_id):
    flag=0
    session = boto3.Session(
    aws_access_key_id=os.environ.get('RATINGS_AWS_ACCESS_KEY'),
    aws_secret_access_key=os.environ.get('RATINGS_AWS_SECRET_KEY'),
    region_name='ap-south-1' )
    dynamodb=session.resource('dynamodb')

    table_name=RATINGS_DYNAMO_DB_TABLE
    table = dynamodb.Table(table_name)

    response=table.get_item(Key={'placeId': placement_id})
    if 'Item' in response and 'placeId' in response['Item']:
        flag=1
        logging.info("Key Exists")
        return flag,response
    else:
        flag=0
        logging.info("Key does not exists")
        return flag,""
        
        
def find_diff_in_dates_for_cache(date1_str,date2_str):
    date1 = datetime.strptime(date1_str, "%Y-%m-%d").date()
    date2 = datetime.strptime(date2_str, "%Y-%m-%d").date()

# Calculate the difference between the dates
    date_difference = (date1 - date2).days

    return date_difference
    

def lambda_handler(event, context):
    '''Demonstrates a simple HTTP endpoint using API Gateway. You have full
    access to the request and response payload, including headers and
    status code.

    To scan a DynamoDB table, make a GET request with the TableName as a
    query string parameter. To put, update, or delete an item, make a POST,
    PUT, or DELETE request respectively, passing in the payload to the
    DynamoDB API as a JSON body.
    '''
    #print("Received event: " + json.dumps(event, indent=2))
    
    if "body" in event:
        request_body=json.loads(event['body'])
        
        if "GOOGLE_ADDRESS" in request_body:
            GOOGLE_ADDRESS=request_body["GOOGLE_ADDRESS"]
            print(GOOGLE_ADDRESS)
            place_id=get_place_id(GOOGLE_ADDRESS)
            print("Place ID Received is ",place_id)
            flag,response_dynamo=cache_in_dynamo_db(place_id)
            if(flag==1):
                date_diff=find_diff_in_dates_for_cache(str(datetime.now().date()),response_dynamo['Item'].get('timeUpdated'))
                print("difference in date is ",date_diff)
                if(date_diff>CACHE_NO_OF_DAYS):
                    flag=0
                else:
                    returned_body={"message":"OK","status_code":200,"total_reviews":float(response_dynamo['Item'].get('noOfReviews')),"source":"Dynamo DB","cache_ttl":7-date_diff}
                    return {'statusCode':200,'body':json.dumps(returned_body),'headers':{'Content-Type': 'application/json'}}
            if(flag==0):
                ratings=get_google_ratings_from_place_id(place_id)
                store_data_dynamo_db(place_id,GOOGLE_ADDRESS,ratings)
                return_body={"message":"OK","status_code":200,"total_reviews":ratings,"source":"API Call"}
                return {'statusCode':200,'body':json.dumps(return_body),'headers':{'Content-Type': 'application/json'}}
                
            ratings=get_google_ratings_from_place_id(place_id)
            print("Ratings recieved is ",ratings)
            return json.dumps({"status_code":200,"message":"OK"})
        else:
            return json.dumps({"status_code":400,"message":"Bad Request Received"})
            
