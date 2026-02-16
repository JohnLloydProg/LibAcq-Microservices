from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from firebase import veriy_firebase_token, Firebase
from fastapi import Header, Depends, Request,  status, Response
from data.models import Book, InShelfAcquisition, Acquisition
from singleton import get_firebase
from firebase_admin import auth
from datetime import datetime
import logging
import io

router = InferringRouter(prefix='/account')


@cbv(router)
class AccountView:
    firebase:Firebase = Depends(get_firebase)
    logger = logging.Logger('AccountView')

    @router.post('/signup', status_code=status.HTTP_201_CREATED)
    async def create_librarian(self, request:Request, response:Response, authorization: str = Header(...)):
        id_token = authorization.split('Bearer').pop().strip()
        uid = veriy_firebase_token(id_token)
        if (uid is None):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return "Unauthorized"
        
        librarian_data = self.firebase.firestore.collection('Librarian').document(uid).get()
        if (not librarian_data.exists):
            response.status_code = status.HTTP_400_BAD_REQUEST
            return 'You are not a librarian!'
        
        if (librarian_data.to_dict().get('Role', 'librarian') != 'admin'):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return 'You do not have permission to access this feature.'
        
        try:
            body_data:dict = await request.json()
            body_data["createdAt"] = datetime.now().isoformat()
        except Exception:
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return 'An error occured in the server.'

        try:
            librarian_record = auth.create_user(email=body_data.get('Email'), password=body_data.pop('Password'))
            body_data['LibrarianID'] = librarian_record.uid
        except auth.EmailAlreadyExistsError:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return 'Email already exist!'
        
        librarian_ref = self.firebase.firestore.collection('Librarian').document(librarian_record.uid)
        librarian_ref.set(body_data)

        return 'Successfully created librarian'
    
    @router.delete('/delete/{separate_uid}', status_code=status.HTTP_201_CREATED)
    async def delete(self, separate_uid:str, response:Response, authorization: str = Header(...)):
        id_token = authorization.split('Bearer').pop().strip()
        uid = veriy_firebase_token(id_token)
        if (uid is None):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return "Unauthorized"
        
        librarian_data = self.firebase.firestore.collection('Librarian').document(uid).get()
        if (not librarian_data.exists):
            response.status_code = status.HTTP_400_BAD_REQUEST
            return 'You are not a librarian!'
        
        if (librarian_data.to_dict().get('Role', 'librarian') != 'admin'):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return 'You do not have permission to access this feature.'
        
        auth.delete_user(uid=separate_uid)
        self.firebase.firestore.collection('Librarian').document(separate_uid).delete()
        return 'Deleted the librarian'
        


