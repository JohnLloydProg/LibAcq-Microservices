from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from fastapi.responses import StreamingResponse
from firebase import veriy_firebase_token, Firebase
from fastapi import Header, Depends, File, UploadFile,  status, Response, Request
from singleton import get_firebase
from data.models import Book, Acquisition, ProcessingRequest, PurchaseOrder, SalesInvoice, Course, InShelfAcquisition
from datetime import datetime
import pandas as pd
from data import errors
import logging
import io
import re


router = InferringRouter(prefix='/excel')

SEPARATORS = [",", "/", ";", " "]
HEADERS = [
    "PURCHASE", "SUPPLIER", "ACC #",
    "CALL #", "COURSE CODE", "TITLE", "AUTHOR", "PUBLISHER",
    "COPYRIGHT", "ISBN", "NO. OF TITLE", "NO. OF VOLS", "PROGRAM",
    "DR", "PR NO.", "PR DATE", "PO NO.", "SI", "SI PRICE",
    "SI RECEIVED BY", "SI RECEIVE ON", "PO DATE", "REQUESTOR NAME",
    "REQUESTOR DEPARTMENT", "BUNDLE", "NOTES"
]

def default_value_string(value, default):
    return value.strip() if (pd.notna(value)) else default

def default_value_date(date_iso):
    return datetime.fromisoformat(str(date_iso).strip()) if (pd.notna(date_iso)) else datetime.now()

def filter_acquisition(acquisition:Acquisition, **kwargs) -> bool:
    for key, value in kwargs.items():
        if (hasattr(acquisition, key)):
            if (getattr(acquisition, key) != value):
                return False
    return True


@cbv(router)
class ExcelView:
    firebase:Firebase = Depends(get_firebase)
    logger = logging.getLogger('ExcelView')

    @router.get('/get')
    async def export_excel(self, request:Request,  response:Response, authorization: str = Header(...)):
        id_token = authorization.split('Bearer').pop().strip()
        uid = veriy_firebase_token(id_token)
        if (uid is None):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return 'Unauthorized'
        
        df = pd.DataFrame(columns=HEADERS)

        for doc_ref in self.firebase.get_all_data_refs(Acquisition):
            acquisition = self.firebase.get_acquisition(doc_ref)
            if (filter_acquisition(acquisition, **request.query_params)):
                df = pd.concat([df, pd.DataFrame([acquisition.to_table()])], ignore_index=True)

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
            return 'Unauthorized'
        
        df = pd.read_excel(file.file, sheet_name=None)
        df = pd.concat(df.values(), ignore_index=True)
        
        for index, row in df.iterrows():
            cleaning = [
                re.search(r'\d+', str(row['PURCHASE'])), re.search(r'\d+', str(row['PR NO.'])),
                re.search(r'\d{4}-\d{2}-\d{2}', str(row['PR DATE'])), re.search(r'\d{4}-\d{2}-\d{2}', str(row['PO DATE'])),
                re.search(r'\d{4}-\d{2}-\d{2}', str(row['SI RECEIVE ON']))
            ]

            if (not all(cleaning)):
                continue
            
            self.logger.info(f"Reading index of {index}")
            isbn = str(row['ISBN']).strip()
            try:
                self.logger.info(f"Getting book with id {isbn}")
                book = self.firebase.get_book(isbn)
            except errors.BookNotFoundError:
                book = Book(
                    isbn=isbn,
                    title=str(row['TITLE']).strip(),
                    author=default_value_string(row['AUTHOR'], 'No Author'),
                    publisher=default_value_string(row['PUBLISHER'], ''),
                    accession_no=default_value_string(row['ACC #'], 'To be catalogued'),
                    call_number=default_value_string(row['CALL #'], ''),
                )
                self.logger.info(f"Creating book with id {isbn}")
                book = self.firebase.save_book(book)
            
            request_no = str(row['PR NO.']).strip()
            try:
                self.logger.info(f"Getting processing request with id {request_no}...")
                processing_request = self.firebase.get_processing_request(request_no)
            except errors.ProcessingRequestNotFoundError:
                processing_request = ProcessingRequest(
                    request_no=request_no,
                    request_date=default_value_date(row['PR DATE'])
                )
                self.logger.info(f"Creating processing request with id {request_no}...")
                processing_request = self.firebase.save_processing_request(processing_request)
            
            if (pd.notna(row['COURSE CODE'])):
                courses_col = str(row['COURSE CODE']).strip()
                course_codes = re.split(r'[,/;\s]+', courses_col)
                
                courses = []
                for course_code in course_codes:
                    try:
                        self.logger.info(f"Getting courses with id {course_code}...")
                        course = self.firebase.get_course(course_code.strip())
                    except errors.CourseNotFoundError:
                        course = Course(
                            course_code=course_code.strip(),
                            program=str(row['PROGRAM']).strip()
                        )
                        self.logger.info(f'Creating courses with id {course_code}...')
                        course = self.firebase.save_course(course)
                    courses.append(course)
            else:
                courses = []
            
            
            try:
                self.logger.info(f"Getting acquisition with id {book.primary_key} & {processing_request.primary_key}...")
                acquisition = self.firebase.get_acquisition_by_ISBN_PR_NO(book.primary_key, processing_request.primary_key)
                response.status_code = status.HTTP_400_BAD_REQUEST
                return 'Can only create new acqusition records. Updating has to be done through the UI.'
            except errors.AcquisitionNotFoundError:
                acquisition = Acquisition(
                    None, book, processing_request=processing_request, courses=courses, year_purchased=int(row['PURCHASE']),
                    supplier=default_value_string(row['SUPPLIER'], ''), copyright=int(row['COPYRIGHT']), no_title=int(row['NO. OF TITLE']),
                    no_volumes=int(row['NO. OF VOLS']), sales_invoice_price=float(re.search(r'\d+\.?\d+', str(row['SI PRICE'])).group()) if (re.search(r'\d+\.?\d+', str(row['SI PRICE']))) else row['SI PRICE'],
                    requestor_name=default_value_string(row['REQUESTOR NAME'], 'Unknown'), requestor_department=default_value_string(row['REQUESTOR DEPARTMENT'], ''), bundle_name=default_value_string(row['BUNDLE'], ''),
                    program=str(row['PROGRAM']).strip()
                )

                self.logger.info(f"Creating acquisition with id {book.primary_key} & {processing_request.primary_key}...")
                acquisition = self.firebase.save_acquisition(acquisition)
            
            if (pd.notna(row['PO NO.'])):
                order_no = str(row['PO NO.']).strip()
                try:
                    self.logger.info(f"Getting purchase order with id {order_no}...")
                    purchase_order = self.firebase.get_purchase_order(order_no)
                except errors.PurchaseOrderNotFoundError:
                    purchase_order = PurchaseOrder(
                        order_no=order_no,
                        order_date=default_value_date(row['PO DATE'])
                    )
                    self.logger.info(f"Creating purchase order with id {order_no}...")
                    purchase_order = self.firebase.save_purchase_order(purchase_order)
                acquisition.purchase_order = purchase_order
            
            if (pd.notna(row['SI'])):
                invoice_no = str(row['SI']).strip()
                try:
                    self.logger.info(f"Getting sales invoice with id {invoice_no}...")
                    sales_invoice = self.firebase.get_sales_invoice(invoice_no)
                except errors.SalesInvoiceNotFoundError:
                    sales_invoice = SalesInvoice(
                        invoice_no=invoice_no,
                        received_by=default_value_string(row['SI RECEIVED BY'], 'Unknown'),
                        received_on=default_value_date(row['SI RECEIVE ON'])
                    )
                    self.logger.info(f"Creating sales invoice with id {invoice_no}...")
                    sales_invoice = self.firebase.save_sales_invoice(sales_invoice)
                acquisition.sales_invoice = sales_invoice
            
            if (pd.notna(row["DR"])):
                self.logger.info("Assigning delivery receipt...")
                acquisition.delivery_receipt = row['DR']
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
            self.firebase.save_acquisition(acquisition)
        return f'Created/Updated acquisition records using excel file'

