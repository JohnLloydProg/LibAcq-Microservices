from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from firebase import veriy_firebase_token, Firebase
from fastapi import Header, Depends, Request,  status, Response
from data.models import Book, InShelfAcquisition
from data import errors
from singleton import get_firebase
from datetime import datetime
import logging
import io

router = InferringRouter(prefix='/in-shelf')


@cbv(router)
class InShelfView:
    firebase:Firebase= Depends(get_firebase)
    logger = logging.Logger('InShelfView')

    @router.post('/new_acquisition', status_code=status.HTTP_201_CREATED)
    async def new_acquisition(self, request:Request, response:Response, authorization: str = Header(...)):
        id_token = authorization.split('Bearer').pop().strip()
        uid = veriy_firebase_token(id_token)
        if (uid is None):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return "Unauthorized"
        
        try:
            body_data:dict = await request.json()
        except Exception:
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return 'An error occured in the server.'

        try:
            acquisition = self.firebase.get_acquisition(body_data.get('acquisition_id'))
        except errors.AcquisitionNotFoundError:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return 'Given acquisition does not exist!'
        
        try:
            in_shelf = self.firebase.get_in_shelf(acquisition.program)
        except errors.InShelfAcquisitionNotFoundError:
            in_shelf = InShelfAcquisition(acquisition.program)

        if (acquisition.courses):
            for course in acquisition.courses:
                in_shelf.add_acquisition(course.primary_key, acquisition)
        else:
            self.logger.info('Acquisition does not have any courses.')
            in_shelf.add_acquisition('No_Course', acquisition)
        
        self.firebase.save_in_shelf(in_shelf)
    
