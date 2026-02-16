from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from firebase import veriy_firebase_token, Firebase
from fastapi import Header, Depends, Request,  status, Response
from data.models import Book, InShelfAcquisition, Acquisition
from singleton import get_firebase
from datetime import datetime
import logging
import io

router = InferringRouter(prefix='/account')


@cbv(router)
class AccountView:
    pass

