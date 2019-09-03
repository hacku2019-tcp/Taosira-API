from flask import Flask, request, jsonify, make_response
from firebase_admin import messaging
from firebase_admin import credentials
import os
import boto3
import botocore.exceptions
import firebase_admin

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'YOUR_FIREBASE_PROJECT_JSON'
cred = credentials.Certificate("YOUR_FIREBASE_PROJECT_JSON")
firebase_admin.initialize_app()

dynamoDB = boto3.resource('dynamodb',
                        aws_access_key_id = 'YOUR_AWS_ACCESS_KEY_ID',
                        aws_secret_access_key = 'YOUR_AWS_SECRET_ACCESS_KEY',
                        region_name = 'YOUR_REGION')
senderTable = dynamoDB.Table('user')
receiverTable = dynamoDB.Table('receiveruser')

app = Flask(__name__)

@app.route('/api', methods=["POST"])
def processing():
    data = request.json
    print(data)
    res = {}
    if data["apiType"] == 'register': #互換性持たせるために使わないけど残している
        try:
            senderTable.put_item(
                Item = {
                    'ID': data["userId"],
                    'notificationID': data["noticeUserId"]
                },
                ConditionExpression = 'attribute_not_exists(ID)'
            )
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                res = {
                    "statusCode": "failed"
                }
                return make_response(jsonify(res))
        else:
            res = {
                'statusCode': "success",
                'registerUserId': data["userId"],
                'registerNoticeId': data["noticeUserId"],
                'registerPushId': data["pushId"]
            }
            return make_response(jsonify(res))

    elif data["apiType"] == 'notification':
        result = senderTable.get_item(
            Key = {
                'ID': data["userId"]
            }
        )
        if ("Item" in result) == False:
            res = {
                "statusCode": "failed"
            }
            return make_response(jsonify(res))
        else:
            second_result = receiverTable.get_item(
                Key = {
                    'ID': result["Item"]["notificationID"]
                }
            )
            if ("Item" in second_result) == False:
                res = {
                    "statusCode": "failed"
                }
                return make_response(jsonify(res))
            else:
                registration_token = second_result["Item"]["UUID"]
                message = messaging.Message(
                    data = {
                        'userId': data["userId"]
                    },
                    token = registration_token
                )
                result_str = messaging.send(message)
                res.setdefault('send_result', result_str)
                res.setdefault('statusCode', 'success')
                res.setdefault('sendUserId', result["Item"]["notificationID"])
                return make_response(jsonify(res))

    elif data["apiType"] == 'registerToken':
        try:
            receiverTable.put_item(
                Item = {
                    'ID': data["userId"],
                    'UUID': data["pushId"]
                },
                ConditionExpression='attribute_not_exists(ID)'
            )
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                res = {
                    "statusCode": "failed"
                }
                return make_response(jsonify(res))
        else:
            res = {
                'statusCode': "success",
                'registerUserId': data["userId"],
                'registerPushId': data["pushId"]
            }
            return make_response(jsonify(res))

    elif data["apiType"] == "registerNotification":
        try:
            senderTable.put_item(
                Item = {
                    "ID": data["userId"],
                    "notificationID": data["notificationId"]
                },
                ConditionExpression='attribute_not_exists(ID)'
            )
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                res = {
                    "statusCode": "failed"
                }
                return make_response(jsonify(res))
        else:
            res = {
                'statusCode': "success",
                'registerUserId': data["userId"],
                'registerNotificationId': data["notificationId"]
            }
            return make_response(jsonify(res))



if __name__ == '__main__':
    app.run()
