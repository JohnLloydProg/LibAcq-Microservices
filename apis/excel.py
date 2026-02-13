from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from fastapi.responses import StreamingResponse
from firebase import veriy_firebase_token
from fastapi import Header, Depends, File, UploadFile,  status, Response
from services import ExcelService
from singleton import get_excel_service
from data.models import Book
import pandas as pd
import io


router = InferringRouter(prefix='/excel')


@cbv(router)
class ExcelView:
    excel_service: ExcelService = Depends(get_excel_service)

    @router.get('/get')
    async def export_excel(self, response:Response, authorization: str = Header(...)):
        id_token = authorization.split('Bearer').pop().strip()
        uid = veriy_firebase_token(id_token)
        if (uid is None):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return {'message': 'Unauthorized'}
        df = self.excel_service.get_acquisition_data(year_purchased=2023, id_token=id_token)

        buffer = io.BytesIO()

        with pd.ExcelWriter(buffer) as writer:
            df.to_excel(writer, index=False)
        return StreamingResponse(
            io.BytesIO(buffer.getvalue()),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={"Content-Disposition": f"attachment; filename=data.csv"}
        )
    
    @router.post('/upload', status_code=status.HTTP_201_CREATED)
    async def import_excel(self, response: Response, file:UploadFile = File(...), authorization: str = Header(...)):
        id_token = authorization.split('Bearer').pop().strip()
        uid = veriy_firebase_token(id_token)
        if (uid is None):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return {'message': 'Unauthorized'}
        df = self.excel_service.read_excel(file)
        self.excel_service.create_acquisitions(df)
        return {'message': f'Created/Updated acquisition records using excel file'}

