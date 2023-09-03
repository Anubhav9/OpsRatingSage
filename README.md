# OpsRatingSage
Implementing GitHub Actions and CI/CD Practices with the Google Places API Integration.

# HLD Diagram

![Untitled Diagram drawio](https://github.com/Anubhav9/OpsRatingSage/assets/40270815/8040fc0d-41c8-4c7c-b76c-a33113066fb9)

# Logic in Lambda Function

i) Fetch the Google Place ID from the Google Address recieved in the body of the Post call.

ii) Call the Google Places API to get number of reviews for the particular place.

iii) Capture and store the data in DynamoDB.

iv) The next time, if the POST call happens with the same Google Address , since the data is already stored in Dynamo DB, it wont make a call to Google Places API , instead, it will fetch from Dynamo DB. The TTL cache for Dynamo DB is 7 days.


# Automatic deployment for changes in Lambda Function

A workflow has already been setup in the workflow directory of the repository which contains the YAML File. If we make any changes to Lambda Function Code in Github, the Lambda Function automatically gets updated in the AWS Servers as well.
Pylint workflow has also been set up to capture the linting process.




