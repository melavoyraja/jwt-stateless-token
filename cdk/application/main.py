from fastapi import FastAPI, HTTPException, status
from mangum import Mangum
from pydantic import BaseModel
import base64
import datetime
import json
import time
import jwt
import boto3

app = FastAPI()
handler = Mangum(app)

KEY_ID = "alias/JWTSigningKey"


class Token(BaseModel):
    auth_token: str


class LoginForm(BaseModel):
    user_name: str
    password: str


def build_data_for_signing_and_verification(header, jwt_payload):
    header = json.dumps(header).encode()
    jwt_payload = json.dumps(jwt_payload).encode()
    token_components = {
        "header": base64.urlsafe_b64encode(header).decode(),
        "payload": base64.urlsafe_b64encode(jwt_payload).decode(),
    }
    return f'{token_components["header"]}.{token_components["payload"]}'


def generate_jwt_token(payload):
    header = {"alg": "RS256", "typ": "JWT"}
    now = datetime.datetime.now()

    # Generate a JWT token
    jwt_payload = {
        "sub": payload.get("user_name"),
        "iat": round(time.time()),
        "exp": (now + datetime.timedelta(days=1)).strftime("%s"),
    }

    message = build_data_for_signing_and_verification(header, jwt_payload)

    client = boto3.client("kms")
    response = client.sign(
        KeyId=KEY_ID,
        Message=message.encode(),
        MessageType="RAW",
        SigningAlgorithm="RSASSA_PKCS1_V1_5_SHA_256",
    )

    signature = base64.urlsafe_b64encode(response["Signature"]).decode()

    return f"{message}.{signature}"


def parse_jwt_token(jwt_token: str):
    # Decode the JWT token
    decoded_token = jwt.decode(jwt_token, options={"verify_signature": False})

    # Extract headers, payload, and signature strings
    headers = jwt.get_unverified_header(jwt_token)
    payload = decoded_token
    signature = jwt_token.split(".")[-1]

    return headers, payload, signature


def verify_with_kms_key(data: str, signature: str):
    # Load the AWS KMS key
    kms_client = boto3.client("kms")
    try:
        response = kms_client.verify(
            KeyId=KEY_ID,
            Message=data.encode(),
            MessageType="RAW",
            Signature=base64.urlsafe_b64decode(signature.encode()),
            SigningAlgorithm="RSASSA_PKCS1_V1_5_SHA_256",
        )
    except kms_client.exceptions.KMSInvalidSignatureException:
        return False

    return response["SignatureValid"]


@app.get("/")
async def hello():
    return {"message": "Hello welcome JWT Stateless Token App!!!"}


@app.post("/test_token")
async def test_token(token: Token):
    tokens = token.auth_token.split(".")
    isSignatureValid = verify_with_kms_key(
        data=f"{tokens[0]}.{tokens[1]}",
        signature=tokens[2],
    )

    if not isSignatureValid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token",
        )

    options = {"verify_signature": False}
    decoded_token = jwt.decode(token.auth_token, options=options)
    return {"my_authorization": decoded_token}


@app.post("/login")
async def login(login_details: LoginForm):
    payload = {"user_name": login_details.user_name}
    jwt_token = generate_jwt_token(payload=payload)

    return {"jwt_token": jwt_token}
