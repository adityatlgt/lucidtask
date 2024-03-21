from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from flask import app


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = {}
    for error in exc.errors():
        error_message = [msg.strip() for msg in error['msg'].split(',')]
        if error_message[0] == 'Value error':
                if len(error['loc']) > 1:
                    error_message.pop(0)
                    errors[error['loc'][1]] = error_message  
                else:
                    error_message.pop(0)
                    errors[error_message[0]] = error_message[1]
        elif error['type'] == 'extra_forbidden':
            errors[error['loc'][1]] = ["Extra fields are not allowed"]
        elif error['type'] == 'missing':
            errors[error['loc'][1]] = [f"{error['loc'][1]} is required"]
        else:
            errors[error['loc'][1]] = error_message
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"message":"validation_errors",'errors':errors, 'status':False , 'statusCode' : 422}),
    )