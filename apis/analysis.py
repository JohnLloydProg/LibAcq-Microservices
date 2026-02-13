from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from fastapi.responses import StreamingResponse
from firebase import veriy_firebase_token
from fastapi import Header, Depends, Request, File, UploadFile,  status, Response
from data.models import Book
from singleton import get_analysis_service
from services import AnalysisService
import io

router = InferringRouter(prefix='/analysis')


@cbv(router)
class AnalysisView:
    analysis_service:AnalysisService = Depends(get_analysis_service)
    
    @router.get('/ratio')
    async def get_ratio(self, response:Response, authorization: str = Header(...)):
        id_token = authorization.split('Bearer').pop().strip()
        uid = veriy_firebase_token(id_token)
        if (uid is None):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return {'message': 'Unauthorized'}
        return {'up_to_date_ratio':self.analysis_service.get_up_to_date_percentage()}

    @router.get('/total')
    async def get_total(self, response:Response, authorization: str = Header(...)):
        id_token = authorization.split('Bearer').pop().strip()
        uid = veriy_firebase_token(id_token)
        if (uid is None):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return {'message': 'Unauthorized'}

        return self.analysis_service.get_number_of_outdated_per_program()

    @router.get('/')
    async def get_suppliers(self, response:Response, authorization: str = Header(...)):
        id_token = authorization.split('Bearer').pop().strip()
        uid = veriy_firebase_token(id_token)
        if (uid is None):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return {'message': 'Unauthorized'}

        return self.analysis_service.get_number_of_outdated_per_program()
