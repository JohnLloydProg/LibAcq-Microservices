import pandas as pd
from fastapi import UploadFile
from data.models import Book, Course, Acquisition,  ProcessingRequest, PurchaseOrder, SalesInvoice, InShelfAcquisition
from data import errors
from firebase import Firebase
from datetime import datetime
import logging

SEPARATORS = [",", "/", ";", " "]
HEADERS = [
    "PURCHASE", "SUPPLIER", "ACC #",
    "CALL #", "COURSE CODE", "TITLE", "AUTHOR", "PUBLISHER",
    "COPYRIGHT", "ISBN", "NO. OF TITLE", "NO. OF VOLS", "PROGRAM",
    "DR", "PR NO.", "PR DATE", "PO NO.", "SI", "SI PRICE",
    "SI RECEIVED BY", "SI RECEIVE ON", "PO DATE", "REQUESTOR NAME",
    "REQUESTOR DEPARTMENT", "BUNDLE", "NOTES"
]
firebase_singleton:Firebase = None

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

def get_firebase() -> Firebase:
    global firebase_singleton
    if not firebase_singleton:
        firebase_singleton = Firebase(cred_path='./credentials.json')
    return firebase_singleton

class ExcelService:
    logger = logging.getLogger('ExcelService')
    firebase:Firebase = get_firebase()

    def read_excel(self, file: UploadFile) -> pd.DataFrame:
        df = pd.read_excel(file.file)
        return df

    def get_acquisition_data(self, **kwargs) -> pd.DataFrame:
        df = pd.DataFrame(columns=HEADERS)

        for doc_ref in self.firebase.get_all_data_refs(Acquisition):
            acquisition = self.firebase.get_acquisition(doc_ref)
            if (filter_acquisition(acquisition, **kwargs)):
                df = pd.concat([df, pd.DataFrame([acquisition.to_table()])], ignore_index=True)
        return df

    def create_acquisitions(self, df: pd.DataFrame) -> list[tuple[Book, ProcessingRequest, Course]]:
        for index, row in df.iterrows():
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
            
            request_no = str(int(row['PR NO.'])).strip()
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
                multiple = None
                for sep in SEPARATORS:
                    if (sep in courses_col):
                        multiple = sep
                        break
                
                courses = []
                if (multiple):
                    self.logger.info('Multiple courses detected...')
                    for sep in SEPARATORS:
                        for course_code in courses_col.split(sep):
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
                        break
                else:
                    try:
                        self.logger.info(f"Getting course with id {courses_col}...")
                        course = self.firebase.get_course(courses_col.strip())
                    except errors.CourseNotFoundError:
                        course = Course(
                            course_code=courses_col.strip(),
                            program=str(row['PROGRAM']).strip()
                        )
                        self.logger.info(f'Creating course with id {courses_col}...')
                        course = self.firebase.save_course(course)
                    courses.append(course)
            else:
                courses = []
            
            
            try:
                self.logger.info(f"Getting acquisition with id {book.primary_key} & {processing_request.primary_key}...")
                acquisition = self.firebase.get_acquisition_by_ISBN_PR_NO(book.primary_key, processing_request.primary_key)
            except errors.AcquisitionNotFoundError:

                acquisition = Acquisition(
                    None, book, processing_request=processing_request, courses=courses, year_purchased=int(row['PURCHASE']),
                    supplier=default_value_string(row['SUPPLIER'], ''), copyright=int(row['COPYRIGHT']), no_title=int(row['NO. OF TITLE']),
                    no_volumes=int(row['NO. OF VOLS']), sales_invoice_price=float(row['SI PRICE']),
                    requestor_name=default_value_string(row['REQUESTOR NAME'], 'Unknown'), requestor_department=default_value_string(row['REQUESTOR DEPARTMENT'], ''), bundle_name=default_value_string(row['BUNDLE'], '')
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
                for course in acquisition.courses:
                    try:
                        self.logger.info(f"Getting in shelf with id {course.program}")
                        in_shelf = self.firebase.get_in_shelf(course.program)
                    except errors.InShelfAcquisitionNotFoundError:
                        self.logger.info(f"Can't get acquisition creating it instead...")
                        in_shelf = InShelfAcquisition(course.program)
                    
                    in_shelf.add_acquisition(course.primary_key, acquisition)
                    self.firebase.save_in_shelf(in_shelf)
            
            acquisition = self.firebase.save_acquisition(acquisition)


class AnalysisService:
    firebase:Firebase = get_firebase()

    #percentage of outdated books
    # number of outdated books per program
    # top suppliers
    # number of books per course code

    def get_up_to_date_percentage(self) -> float:
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

    def get_number_of_outdated_per_program(self) -> dict[str, float]:
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


if __name__ == '__main__':
    service = ExcelService()
    with open('./test_data.xlsx', 'rb') as f:
        upload_file = UploadFile(filename='sample.xlsx', file=f)
        df = service.read_excel(upload_file)
        for col in df.columns:
            print(f'{col}: {df[col].unique()}')
        print(df.columns)
        #service.create_acquisitions(df)
