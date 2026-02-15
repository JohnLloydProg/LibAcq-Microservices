from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from firebase import veriy_firebase_token, Firebase
from fastapi import Header, Depends, Request,  status, Response
from data.models import Book, InShelfAcquisition, Acquisition
from singleton import get_firebase
from datetime import datetime
import logging
import io

router = InferringRouter(prefix='/analysis')


@cbv(router)
class AnalysisView:
    firebase:Firebase= Depends(get_firebase)
    logger = logging.Logger('AnalysisView')
    
    @router.get('/ratio')
    async def get_ratio(self, response:Response, authorization: str = Header(...)):
        id_token = authorization.split('Bearer').pop().strip()
        uid = veriy_firebase_token(id_token)
        if (uid is None):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return 'Unauthorized'
        
        acquisition_refs = self.firebase.get_all_data_refs(InShelfAcquisition)
        total = 0
        up_to_date = 0

        cur_year = datetime.now().date().year
        for ref in acquisition_refs:
            in_shelf = self.firebase.get_in_shelf(ref)
            for record in in_shelf.records.values():
                for item in record:
                    if (cur_year - 5 <= item['copyright'] <= cur_year):
                        up_to_date += 1
                    total += 1
        
        return round((up_to_date/total)*100, 2)

    @router.get('/total')
    async def get_total(self, response:Response, authorization: str = Header(...)):
        id_token = authorization.split('Bearer').pop().strip()
        uid = veriy_firebase_token(id_token)
        if (uid is None):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return 'Unauthorized'
        
        acquisition_refs = self.firebase.get_all_data_refs(InShelfAcquisition)

        result = {}
        cur_date = datetime.now().date()
        for ref in acquisition_refs:
            in_shelf = self.firebase.get_in_shelf(ref)
            result[ref] = 0
            for record in in_shelf.records.values():
                for item in record:
                    if (item['copyright'] < cur_date.year - 5):
                        result[ref] += 1

        return result


    @router.get('/suppliers')
    async def get_suppliers(self, response:Response, authorization: str = Header(...)):
        id_token = authorization.split('Bearer').pop().strip()
        uid = veriy_firebase_token(id_token)
        if (uid is None):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return 'Unauthorized'
        
        suppliers = {}
        
        doc_refs = self.firebase.get_all_data_refs(Acquisition)
        for doc_ref in doc_refs:
            acquisition = self.firebase.get_acquisition(doc_ref)
            suppliers[acquisition.supplier] = suppliers.get(acquisition.supplier, 0) + 1
        
        return sorted(list(suppliers.items()), key=lambda item: item[1], reverse=True)
    
    @router.get('/total-per-course')
    async def get_total_course(self, response:Response, authorization: str = Header(...)):
        id_token = authorization.split('Bearer').pop().strip()
        uid = veriy_firebase_token(id_token)
        if (uid is None):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return 'Unauthorized'

        acquisition_refs = self.firebase.get_all_data_refs(InShelfAcquisition)

        result = {}
        cur_date = datetime.now().date()
        for ref in acquisition_refs:
            in_shelf = self.firebase.get_in_shelf(ref)
            result[ref] = {}
            for key, record in in_shelf.records.items():
                result[ref][key] = 0
                for item in record:
                    if (item['copyright'] < cur_date.year - 5):
                        result[ref][key] += 1

        return result

        